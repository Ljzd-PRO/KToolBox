import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from ktoolbox.utils import check_for_updates


class TestUpdateCheck:
    """Test update checking functionality"""

    @pytest.mark.asyncio
    async def test_update_check_no_update_available(self):
        """Test when no update is available"""
        # Mock httpx.AsyncClient
        mock_response = MagicMock()  # Use MagicMock instead of AsyncMock for response
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tag_name": "v0.20.0",  # Same as current version
            "html_url": "https://github.com/Ljzd-PRO/KToolBox/releases/tag/v0.20.0"
        }
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            # This should not raise an exception
            await check_for_updates()

    @pytest.mark.asyncio
    async def test_update_check_with_new_version_github(self):
        """Test when a newer version is available on GitHub"""
        # Mock HTTP client to return a newer version
        mock_response = MagicMock()  # Use MagicMock instead of AsyncMock for response
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tag_name": "v0.21.0",
            "html_url": "https://github.com/Ljzd-PRO/KToolBox/releases/tag/v0.21.0"
        }
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            # This should not raise an exception
            await check_for_updates()

    @pytest.mark.asyncio
    async def test_update_check_github_fails_pypi_succeeds(self):
        """Test fallback to PyPI when GitHub fails"""
        call_count = 0
        
        def mock_client_factory():
            nonlocal call_count
            call_count += 1
            
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            if call_count == 1:
                # First call (GitHub) fails
                mock_client.get.side_effect = Exception("GitHub API failed")
            else:
                # Second call (PyPI) succeeds
                mock_pypi_response = MagicMock()  # Use MagicMock instead of AsyncMock for response
                mock_pypi_response.status_code = 200
                mock_pypi_response.json.return_value = {
                    "info": {"version": "0.21.0"}
                }
                mock_client.get.return_value = mock_pypi_response
            
            return mock_client
        
        with patch('httpx.AsyncClient', side_effect=mock_client_factory):
            # This should not raise an exception
            await check_for_updates()

    @pytest.mark.asyncio 
    async def test_update_check_handles_network_failure(self):
        """Test that network failures are handled gracefully"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception("Network error")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            # This should not raise an exception even with network failures
            await check_for_updates()