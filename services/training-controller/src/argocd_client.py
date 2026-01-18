"""ArgoCD client for triggering application sync.

Optional module for explicitly syncing ArgoCD applications
after GitOps configuration changes.
"""

import logging
from typing import Optional

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class ArgocdClient:
    """Client for ArgoCD API interactions.

    Used to optionally trigger application sync after
    pushing GitOps configuration changes.
    """

    def __init__(
        self,
        server_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        app_name: str = "inference-service"
    ):
        """Initialize ArgoCD client.

        Args:
            server_url: ArgoCD server URL (defaults from settings).
            auth_token: ArgoCD authentication token (defaults from settings).
            app_name: Name of the ArgoCD application to sync.
        """
        self.server_url = server_url if server_url is not None else settings.argocd_server_url
        self.auth_token = auth_token if auth_token is not None else settings.argocd_auth_token
        self.app_name = app_name
        self._timeout = 30.0

    @property
    def is_configured(self) -> bool:
        """Check if ArgoCD integration is properly configured."""
        return bool(self.server_url and self.auth_token)

    def trigger_sync(self, prune: bool = False, dry_run: bool = False) -> bool:
        """Trigger an ArgoCD application sync.

        Args:
            prune: If True, prune resources that are no longer defined.
            dry_run: If True, perform a dry run without applying changes.

        Returns:
            bool: True if sync was triggered successfully, False otherwise.
        """
        if not self.is_configured:
            logger.info("ArgoCD not configured, skipping sync trigger")
            return True  # Not an error, just not configured

        sync_url = f"{self.server_url}/api/v1/applications/{self.app_name}/sync"

        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "revision": "HEAD",
            "prune": prune,
            "dryRun": dry_run
        }

        try:
            with httpx.Client(timeout=self._timeout, verify=True) as client:
                response = client.post(sync_url, headers=headers, json=payload)

                if response.status_code in (200, 201):
                    logger.info(
                        f"Successfully triggered sync for {self.app_name}"
                    )
                    return True
                else:
                    logger.error(
                        f"ArgoCD sync failed with status {response.status_code}: "
                        f"{response.text}"
                    )
                    return False

        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to ArgoCD server: {e}")
            return False
        except httpx.TimeoutException as e:
            logger.error(f"ArgoCD request timed out: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error triggering ArgoCD sync: {e}")
            return False

    def get_application_status(self) -> Optional[str]:
        """Get the current sync status of the ArgoCD application.

        Returns:
            Optional[str]: The sync status or None if unavailable.
        """
        if not self.is_configured:
            return None

        status_url = f"{self.server_url}/api/v1/applications/{self.app_name}"

        headers = {
            "Authorization": f"Bearer {self.auth_token}"
        }

        try:
            with httpx.Client(timeout=self._timeout, verify=True) as client:
                response = client.get(status_url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    sync_status = (
                        data.get("status", {})
                        .get("sync", {})
                        .get("status", "Unknown")
                    )
                    health_status = (
                        data.get("status", {})
                        .get("health", {})
                        .get("status", "Unknown")
                    )
                    return f"Sync: {sync_status}, Health: {health_status}"
                else:
                    logger.warning(
                        f"Failed to get app status: {response.status_code}"
                    )
                    return None

        except Exception as e:
            logger.warning(f"Failed to get ArgoCD application status: {e}")
            return None


async def trigger_argocd_sync_async() -> bool:
    """Async wrapper for triggering ArgoCD sync.

    Returns:
        bool: True if sync was triggered or not configured, False on error.
    """
    client = ArgocdClient()
    return client.trigger_sync()
