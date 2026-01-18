"""Unit tests for ArgoCD client module."""

import pytest
from unittest.mock import MagicMock, patch


# Patch settings before importing
with patch.dict('os.environ', {
    'ARGOCD_SERVER_URL': 'https://argocd.example.com',
    'ARGOCD_AUTH_TOKEN': 'test-auth-token',
    'ARGOCD_APP_NAME': 'inference-service'
}):
    from src.argocd_client import ArgocdClient, trigger_argocd_sync_async


@pytest.fixture
def client():
    """Create an ArgocdClient instance with test settings."""
    return ArgocdClient(
        server_url='https://argocd.example.com',
        auth_token='test-auth-token',
        app_name='inference-service'
    )


@pytest.fixture
def unconfigured_client():
    """Create an ArgocdClient instance without configuration."""
    return ArgocdClient(server_url='', auth_token='', app_name='test-app')


class TestArgocdClientConfiguration:
    """Tests for client configuration."""

    def test_is_configured_true(self, client):
        """Test that client reports configured when URL and token set."""
        assert client.is_configured is True

    def test_is_configured_false_no_url(self, unconfigured_client):
        """Test that client reports not configured without URL."""
        assert unconfigured_client.is_configured is False

    def test_is_configured_false_no_token(self):
        """Test that client reports not configured without token."""
        client = ArgocdClient(
            server_url='https://argocd.example.com',
            auth_token='',
            app_name='test-app'
        )
        assert client.is_configured is False


class TestArgocdClientTriggerSync:
    """Tests for sync trigger functionality."""

    def test_trigger_sync_success(self, client):
        """Test successful sync trigger."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch('httpx.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = client.trigger_sync()

            assert result is True
            mock_client.post.assert_called_once()

            # Verify correct URL
            call_args = mock_client.post.call_args
            url = call_args[0][0]
            assert 'inference-service/sync' in url

    def test_trigger_sync_with_prune_and_dry_run(self, client):
        """Test sync trigger with optional parameters."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch('httpx.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = client.trigger_sync(prune=True, dry_run=True)

            assert result is True
            call_args = mock_client.post.call_args
            payload = call_args[1]['json']
            assert payload['prune'] is True
            assert payload['dryRun'] is True

    def test_trigger_sync_failure_status_code(self, client):
        """Test sync trigger handles error status codes."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'

        with patch('httpx.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = client.trigger_sync()

            assert result is False

    def test_trigger_sync_connection_error(self, client):
        """Test sync trigger handles connection errors."""
        import httpx

        with patch('httpx.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.side_effect = httpx.ConnectError('Connection refused')
            mock_client_class.return_value = mock_client

            result = client.trigger_sync()

            assert result is False

    def test_trigger_sync_timeout(self, client):
        """Test sync trigger handles timeout."""
        import httpx

        with patch('httpx.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.side_effect = httpx.TimeoutException('Timeout')
            mock_client_class.return_value = mock_client

            result = client.trigger_sync()

            assert result is False

    def test_trigger_sync_not_configured(self, unconfigured_client):
        """Test that unconfigured client returns True (skip is not error)."""
        result = unconfigured_client.trigger_sync()

        assert result is True  # Skipping is not an error


class TestArgocdClientGetStatus:
    """Tests for application status retrieval."""

    def test_get_status_success(self, client):
        """Test successful status retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': {
                'sync': {'status': 'Synced'},
                'health': {'status': 'Healthy'}
            }
        }

        with patch('httpx.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = client.get_application_status()

            assert 'Synced' in result
            assert 'Healthy' in result

    def test_get_status_not_configured(self, unconfigured_client):
        """Test that unconfigured client returns None."""
        result = unconfigured_client.get_application_status()

        assert result is None

    def test_get_status_error(self, client):
        """Test that errors return None."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch('httpx.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = client.get_application_status()

            assert result is None


@pytest.mark.asyncio
async def test_trigger_argocd_sync_async():
    """Test async wrapper for sync trigger."""
    with patch('src.argocd_client.ArgocdClient') as mock_client_class:
        mock_instance = MagicMock()
        mock_instance.trigger_sync.return_value = True
        mock_client_class.return_value = mock_instance

        result = await trigger_argocd_sync_async()

        assert result is True
        mock_instance.trigger_sync.assert_called_once()
