"""Git operations module for model promotion via GitOps.

Handles cloning the repository, updating model version configuration,
and pushing changes for ArgoCD to detect.
"""

import logging
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional

import yaml
from git import Repo, GitCommandError
from git.exc import InvalidGitRepositoryError

from src.config import settings

logger = logging.getLogger(__name__)


class GitPromoter:
    """Handles GitOps-based model promotion.

    Clones the repository, updates the model version in deployment config,
    commits and pushes the change for ArgoCD to detect.
    """

    def __init__(self):
        """Initialize GitPromoter with configuration from settings."""
        self.repo_url = settings.git_repo_url
        self.branch = settings.git_branch
        self.username = settings.git_username
        self.email = settings.git_email
        self.ssh_key_path = settings.git_ssh_key_path
        self.pat = settings.git_pat
        self.config_path = settings.model_config_path
        self._temp_dir: Optional[str] = None
        self._repo: Optional[Repo] = None

    def clone_repository(self) -> Repo:
        """Clone the repository to a temporary directory.

        Returns:
            Repo: GitPython Repo object for the cloned repository.

        Raises:
            GitCommandError: If clone operation fails.
        """
        self._temp_dir = tempfile.mkdtemp(prefix="model-promotion-")
        logger.info(f"Cloning repository to {self._temp_dir}")

        env = {}
        if self.ssh_key_path and os.path.exists(self.ssh_key_path):
            # Use SSH key for authentication
            ssh_cmd = f'ssh -i {self.ssh_key_path} -o StrictHostKeyChecking=no'
            env['GIT_SSH_COMMAND'] = ssh_cmd
            logger.info("Using SSH key authentication")

        repo_url = self.repo_url
        if self.pat and not self.ssh_key_path:
            # Use PAT for HTTPS authentication
            if 'github.com' in repo_url:
                repo_url = repo_url.replace(
                    'https://',
                    f'https://{self.pat}@'
                )
            logger.info("Using PAT authentication")

        try:
            self._repo = Repo.clone_from(
                repo_url,
                self._temp_dir,
                branch=self.branch,
                env=env if env else None,
                depth=1  # Shallow clone for speed
            )
            logger.info(f"Successfully cloned {self.branch} branch")
            return self._repo
        except GitCommandError as e:
            logger.error(f"Failed to clone repository: {e}")
            self.cleanup()
            raise

    def configure_git_identity(self) -> None:
        """Configure git user identity for commits."""
        if not self._repo:
            raise RuntimeError("Repository not cloned. Call clone_repository first.")

        with self._repo.config_writer() as config:
            config.set_value("user", "name", self.username)
            config.set_value("user", "email", self.email)

        logger.info(f"Configured git identity: {self.username} <{self.email}>")

    def update_model_version(self, new_version: str) -> bool:
        """Update the model version in the deployment configuration.

        Args:
            new_version: The new model version string (e.g., 'v2').

        Returns:
            bool: True if update was successful, False otherwise.
        """
        if not self._repo or not self._temp_dir:
            raise RuntimeError("Repository not cloned. Call clone_repository first.")

        config_file = Path(self._temp_dir) / self.config_path

        if not config_file.exists():
            logger.error(f"Configuration file not found: {config_file}")
            return False

        try:
            # Read the YAML file
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)

            if config is None:
                logger.error("Failed to parse YAML configuration")
                return False

            # Navigate to container env and update MODEL_VERSION
            updated = False
            containers = (
                config.get('spec', {})
                .get('template', {})
                .get('spec', {})
                .get('containers', [])
            )

            for container in containers:
                env_vars = container.get('env', [])
                for env_var in env_vars:
                    if env_var.get('name') == 'MODEL_VERSION':
                        old_version = env_var.get('value', 'unknown')
                        env_var['value'] = new_version
                        updated = True
                        logger.info(
                            f"Updated MODEL_VERSION: {old_version} -> {new_version}"
                        )
                        break

                # If MODEL_VERSION not found, add it
                if not updated:
                    if 'env' not in container:
                        container['env'] = []
                    container['env'].append({
                        'name': 'MODEL_VERSION',
                        'value': new_version
                    })
                    updated = True
                    logger.info(f"Added MODEL_VERSION: {new_version}")

            if updated:
                # Write the updated YAML back
                with open(config_file, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
                logger.info(f"Wrote updated configuration to {config_file}")
                return True

            logger.warning("No containers found to update")
            return False

        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to update model version: {e}")
            return False

    def commit_and_push(
        self,
        version: str,
        max_retries: int = 3,
        base_delay: float = 1.0
    ) -> bool:
        """Commit the changes and push to remote.

        Args:
            version: Model version for commit message.
            max_retries: Maximum number of push attempts.
            base_delay: Base delay in seconds for exponential backoff.

        Returns:
            bool: True if push was successful, False otherwise.
        """
        if not self._repo:
            raise RuntimeError("Repository not cloned. Call clone_repository first.")

        try:
            # Stage the config file
            self._repo.index.add([self.config_path])

            # Check if there are changes to commit
            if not self._repo.index.diff("HEAD"):
                logger.info("No changes to commit")
                return True

            # Commit with conventional commit message
            commit_message = f"chore: promote model to {version}"
            self._repo.index.commit(commit_message)
            logger.info(f"Committed changes: {commit_message}")

            # Push with retry logic
            origin = self._repo.remote('origin')

            for attempt in range(1, max_retries + 1):
                try:
                    origin.push(self.branch)
                    logger.info(f"Successfully pushed to {self.branch}")
                    return True
                except GitCommandError as e:
                    if attempt == max_retries:
                        logger.error(
                            f"Failed to push after {max_retries} attempts: {e}"
                        )
                        return False

                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"Push attempt {attempt} failed, retrying in {delay}s: {e}"
                    )
                    time.sleep(delay)

        except GitCommandError as e:
            logger.error(f"Git operation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during commit/push: {e}")
            return False

        return False

    def cleanup(self) -> None:
        """Clean up temporary directory."""
        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir)
                logger.info(f"Cleaned up temporary directory: {self._temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory: {e}")
            finally:
                self._temp_dir = None
                self._repo = None

    def promote_model(self, new_version: str) -> bool:
        """Execute the full model promotion workflow.

        Args:
            new_version: The new model version to promote (e.g., 'v2').

        Returns:
            bool: True if promotion was successful, False otherwise.
        """
        logger.info(f"Starting model promotion to {new_version}")

        try:
            # Step 1: Clone repository
            self.clone_repository()

            # Step 2: Configure git identity
            self.configure_git_identity()

            # Step 3: Update model version
            if not self.update_model_version(new_version):
                logger.error("Failed to update model version")
                return False

            # Step 4: Commit and push
            if not self.commit_and_push(new_version):
                logger.error("Failed to commit and push changes")
                return False

            logger.info(f"Successfully promoted model to {new_version}")
            return True

        except Exception as e:
            logger.exception(f"Model promotion failed: {e}")
            return False

        finally:
            # Always clean up
            self.cleanup()


async def promote_model_async(new_version: str) -> bool:
    """Async wrapper for model promotion.

    Args:
        new_version: The new model version to promote.

    Returns:
        bool: True if promotion was successful, False otherwise.
    """
    if not settings.enable_model_promotion:
        logger.info("Model promotion is disabled")
        return True

    promoter = GitPromoter()
    return promoter.promote_model(new_version)
