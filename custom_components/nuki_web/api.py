"""API Client for Nuki Web."""
import logging
import aiohttp
from typing import List, Dict, Any, Optional

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)

class NukiWebApi:
    """Nuki Web API Client."""

    def __init__(self, token: str, session: aiohttp.ClientSession) -> None:
        """Initialize the client."""
        self._token = token
        self._session = session
        self._headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def get_smartlocks(self) -> List[Dict[str, Any]]:
        """Get list of smartlocks."""
        url = f"{API_BASE_URL}/smartlock"
        async with self._session.get(url, headers=self._headers) as response:
            if response.status != 200:
                _LOGGER.error("Error fetching smartlocks: %s", response.status)
                response.raise_for_status()
            return await response.json()

    async def post_action(self, smartlock_id: int, action: int, option: int = 0) -> None:
        """Post an action to a smartlock."""
        url = f"{API_BASE_URL}/smartlock/{smartlock_id}/action"
        data = {"action": action, "option": option}
        async with self._session.post(url, headers=self._headers, json=data) as response:
            if response.status != 204:
                _LOGGER.error("Error sending action %s to %s: %s", action, smartlock_id, response.status)
                response.raise_for_status()
            
    async def update_smartlock_config(self, smartlock_id: int, **kwargs) -> None:
        """Update smartlock config."""
        url = f"{API_BASE_URL}/smartlock/{smartlock_id}/config"
        async with self._session.post(url, headers=self._headers, json=kwargs) as response:
            if response.status != 204:
                _LOGGER.error("Error updating config for %s: %s", smartlock_id, response.status)
                response.raise_for_status()

    async def update_smartlock_advanced_config(self, smartlock_id: int, **kwargs) -> None:
        """Update smartlock advanced config."""
        url = f"{API_BASE_URL}/smartlock/{smartlock_id}/advanced/config"
        async with self._session.post(url, headers=self._headers, json=kwargs) as response:
            if response.status != 204:
                _LOGGER.error("Error updating advanced config for %s: %s", smartlock_id, response.status)
                response.raise_for_status()
    async def validate_token(self) -> bool:
        """Validate the API token by fetching accounts or smartlocks."""
        try:
            await self.get_smartlocks()
            return True
        except Exception as e:
            _LOGGER.error("Token validation failed: %s", e)
            return False
