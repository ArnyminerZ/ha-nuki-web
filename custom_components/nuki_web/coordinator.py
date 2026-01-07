"""Data Coordinator for Nuki Web."""
import logging
import asyncio
from datetime import timedelta
from typing import Dict, Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import NukiWebApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)

class NukiWebCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Nuki Web data."""

    def __init__(self, hass: HomeAssistant, api: NukiWebApi) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self) -> Dict[int, Dict[str, Any]]:
        """Fetch data from API endpoint."""
        try:
            smartlocks = await self.api.get_smartlocks()
            # Convert list to dict keyed by smartlockId
            return {lock["smartlockId"]: lock for lock in smartlocks}
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
