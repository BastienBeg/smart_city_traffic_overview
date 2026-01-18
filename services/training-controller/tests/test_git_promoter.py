"""Unit tests for Git promoter module."""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import yaml


# Patch settings before importing
with patch.dict('os.environ', {
    'GIT_REPO_URL': 'https://github.com/test/repo.git',
    'GIT_BRANCH': 'main',
    'GIT_USERNAME': 'Test User',
    'GIT_EMAIL': 'test@example.com',
    'GIT_SSH_KEY_PATH': '',
    'GIT_PAT': 'test-pat-token',
    'MODEL_CONFIG_PATH': 'k8s/apps/inference-service/base/deployment.yaml',
    'ENABLE_MODEL_PROMOTION': 'true'
}):
    from src.git_promoter import GitPromoter, promote_model_async


@pytest.fixture
def promoter():
    """Create a GitPromoter instance with test settings."""
    p = GitPromoter()
    # Override settings directly on the instance
    p.repo_url = 'https://github.com/test/repo.git'
    p.branch = 'main'
    p.username = 'Test User'
    p.email = 'test@example.com'
    p.ssh_key_path = ''
    p.pat = 'test-pat-token'
    p.config_path = 'k8s/apps/inference-service/base/deployment.yaml'
    return p


@pytest.fixture
def sample_deployment_yaml():
    """Sample deployment YAML content."""
    return {
        'apiVersion': 'apps/v1',
        'kind': 'Deployment',
        'metadata': {'name': 'inference-service'},
        'spec': {
            'template': {
                'spec': {
                    'containers': [{
                        'name': 'inference-service',
                        'image': 'inference:latest',
                        'env': [
                            {'name': 'MODEL_VERSION', 'value': 'v1'}
                        ]
                    }]
                }
            }
        }
    }


class TestGitPromoterClone:
    """Tests for repository cloning."""

    def test_clone_with_pat_authentication(self, promoter):
        """Test that PAT is correctly inserted into clone URL."""
        mock_repo = MagicMock()

        with patch('src.git_promoter.Repo') as mock_repo_class:
            mock_repo_class.clone_from.return_value = mock_repo

            promoter.clone_repository()

            # Verify PAT was inserted into URL
            call_args = mock_repo_class.clone_from.call_args
            clone_url = call_args[0][0]
            assert 'test-pat-token@' in clone_url
            assert mock_repo_class.clone_from.called

    def test_clone_with_ssh_key(self):
        """Test that SSH key is used when configured."""
        promoter = GitPromoter()
        # Override settings for SSH key scenario
        promoter.repo_url = 'git@github.com:test/repo.git'
        promoter.ssh_key_path = '/path/to/key'
        promoter.pat = ''
        mock_repo = MagicMock()

        with patch('src.git_promoter.Repo') as mock_repo_class, \
             patch('os.path.exists', return_value=True):
            mock_repo_class.clone_from.return_value = mock_repo

            promoter.clone_repository()

            call_args = mock_repo_class.clone_from.call_args
            env = call_args[1].get('env', {})
            assert 'GIT_SSH_COMMAND' in env
            assert '/path/to/key' in env['GIT_SSH_COMMAND']

    def test_clone_creates_temp_directory(self, promoter):
        """Test that clone creates a temporary directory."""
        mock_repo = MagicMock()

        with patch('src.git_promoter.Repo') as mock_repo_class, \
             patch('tempfile.mkdtemp', return_value='/tmp/test-dir') as mock_mkdtemp:
            mock_repo_class.clone_from.return_value = mock_repo

            promoter.clone_repository()

            mock_mkdtemp.assert_called_once()
            assert promoter._temp_dir == '/tmp/test-dir'


class TestGitPromoterConfigureIdentity:
    """Tests for git identity configuration."""

    def test_configure_identity_sets_name_and_email(self, promoter):
        """Test that git user name and email are configured."""
        mock_repo = MagicMock()
        mock_config_writer = MagicMock()
        mock_repo.config_writer.return_value.__enter__ = MagicMock(
            return_value=mock_config_writer
        )
        mock_repo.config_writer.return_value.__exit__ = MagicMock(
            return_value=False
        )

        promoter._repo = mock_repo

        promoter.configure_git_identity()

        mock_config_writer.set_value.assert_any_call(
            "user", "name", "Test User"
        )
        mock_config_writer.set_value.assert_any_call(
            "user", "email", "test@example.com"
        )

    def test_configure_identity_raises_without_clone(self, promoter):
        """Test that RuntimeError is raised if repo not cloned."""
        with pytest.raises(RuntimeError):
            promoter.configure_git_identity()


class TestGitPromoterUpdateVersion:
    """Tests for model version updates."""

    def test_update_model_version_existing_env(
        self, promoter, sample_deployment_yaml
    ):
        """Test updating an existing MODEL_VERSION env var."""
        promoter._repo = MagicMock()
        promoter._temp_dir = '/tmp/test'

        yaml_content = yaml.dump(sample_deployment_yaml)

        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('yaml.safe_load', return_value=sample_deployment_yaml), \
             patch('yaml.dump') as mock_dump:

            result = promoter.update_model_version('v2')

            assert result is True
            # Verify the YAML was updated
            written_config = mock_dump.call_args[0][0]
            env_vars = (
                written_config['spec']['template']['spec']
                ['containers'][0]['env']
            )
            version_env = next(
                e for e in env_vars if e['name'] == 'MODEL_VERSION'
            )
            assert version_env['value'] == 'v2'

    def test_update_model_version_adds_env_if_missing(self, promoter):
        """Test adding MODEL_VERSION when it doesn't exist."""
        config_without_env = {
            'spec': {
                'template': {
                    'spec': {
                        'containers': [{
                            'name': 'inference-service',
                            'image': 'inference:latest'
                        }]
                    }
                }
            }
        }

        promoter._repo = MagicMock()
        promoter._temp_dir = '/tmp/test'

        with patch('builtins.open', mock_open()), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('yaml.safe_load', return_value=config_without_env), \
             patch('yaml.dump') as mock_dump:

            result = promoter.update_model_version('v1')

            assert result is True
            written_config = mock_dump.call_args[0][0]
            container = written_config['spec']['template']['spec']['containers'][0]
            assert 'env' in container
            assert any(
                e['name'] == 'MODEL_VERSION' and e['value'] == 'v1'
                for e in container['env']
            )

    def test_update_model_version_file_not_found(self, promoter):
        """Test handling of missing config file."""
        promoter._repo = MagicMock()
        promoter._temp_dir = '/tmp/test'

        with patch('pathlib.Path.exists', return_value=False):
            result = promoter.update_model_version('v2')

            assert result is False


class TestGitPromoterCommitPush:
    """Tests for commit and push operations."""

    def test_commit_and_push_success(self, promoter):
        """Test successful commit and push."""
        mock_repo = MagicMock()
        mock_repo.index.diff.return_value = [MagicMock()]  # Has changes
        mock_remote = MagicMock()
        mock_repo.remote.return_value = mock_remote

        promoter._repo = mock_repo

        result = promoter.commit_and_push('v2')

        assert result is True
        mock_repo.index.add.assert_called_once()
        mock_repo.index.commit.assert_called_once_with(
            "chore: promote model to v2"
        )
        mock_remote.push.assert_called_once()

    def test_commit_and_push_no_changes(self, promoter):
        """Test that no commit happens when no changes exist."""
        mock_repo = MagicMock()
        mock_repo.index.diff.return_value = []  # No changes

        promoter._repo = mock_repo

        result = promoter.commit_and_push('v2')

        assert result is True
        mock_repo.index.commit.assert_not_called()

    def test_commit_and_push_retry_on_failure(self, promoter):
        """Test retry logic on push failure."""
        from git import GitCommandError

        mock_repo = MagicMock()
        mock_repo.index.diff.return_value = [MagicMock()]
        mock_remote = MagicMock()
        mock_remote.push.side_effect = [
            GitCommandError('push', 'error'),  # First attempt fails
            None  # Second attempt succeeds
        ]
        mock_repo.remote.return_value = mock_remote

        promoter._repo = mock_repo

        with patch('time.sleep'):  # Skip actual sleep
            result = promoter.commit_and_push('v2', max_retries=3)

        assert result is True
        assert mock_remote.push.call_count == 2

    def test_commit_and_push_all_retries_fail(self, promoter):
        """Test that failure is returned after all retries exhausted."""
        from git import GitCommandError

        mock_repo = MagicMock()
        mock_repo.index.diff.return_value = [MagicMock()]
        mock_remote = MagicMock()
        mock_remote.push.side_effect = GitCommandError('push', 'error')
        mock_repo.remote.return_value = mock_remote

        promoter._repo = mock_repo

        with patch('time.sleep'):
            result = promoter.commit_and_push('v2', max_retries=3)

        assert result is False
        assert mock_remote.push.call_count == 3


class TestGitPromoterCleanup:
    """Tests for cleanup operations."""

    def test_cleanup_removes_temp_directory(self, promoter):
        """Test that cleanup removes the temporary directory."""
        promoter._temp_dir = '/tmp/test-cleanup'
        promoter._repo = MagicMock()

        with patch('os.path.exists', return_value=True), \
             patch('shutil.rmtree') as mock_rmtree:

            promoter.cleanup()

            mock_rmtree.assert_called_once_with('/tmp/test-cleanup')
            assert promoter._temp_dir is None
            assert promoter._repo is None


class TestGitPromoterPromoteModel:
    """Tests for the full promote_model workflow."""

    def test_promote_model_success(self, promoter):
        """Test successful end-to-end model promotion."""
        with patch.object(promoter, 'clone_repository'), \
             patch.object(promoter, 'configure_git_identity'), \
             patch.object(promoter, 'update_model_version', return_value=True), \
             patch.object(promoter, 'commit_and_push', return_value=True), \
             patch.object(promoter, 'cleanup'):

            result = promoter.promote_model('v2')

            assert result is True

    def test_promote_model_fails_on_update(self, promoter):
        """Test that promotion fails if update fails."""
        with patch.object(promoter, 'clone_repository'), \
             patch.object(promoter, 'configure_git_identity'), \
             patch.object(promoter, 'update_model_version', return_value=False), \
             patch.object(promoter, 'cleanup') as mock_cleanup:

            result = promoter.promote_model('v2')

            assert result is False
            mock_cleanup.assert_called_once()

    def test_promote_model_fails_on_push(self, promoter):
        """Test that promotion fails if push fails."""
        with patch.object(promoter, 'clone_repository'), \
             patch.object(promoter, 'configure_git_identity'), \
             patch.object(promoter, 'update_model_version', return_value=True), \
             patch.object(promoter, 'commit_and_push', return_value=False), \
             patch.object(promoter, 'cleanup') as mock_cleanup:

            result = promoter.promote_model('v2')

            assert result is False
            mock_cleanup.assert_called_once()


@pytest.mark.asyncio
async def test_promote_model_async_disabled():
    """Test that promotion is skipped when disabled."""
    with patch.dict('os.environ', {'ENABLE_MODEL_PROMOTION': 'false'}):
        with patch('src.git_promoter.settings') as mock_settings:
            mock_settings.enable_model_promotion = False

            result = await promote_model_async('v2')

            assert result is True  # Returns True (success) when disabled
