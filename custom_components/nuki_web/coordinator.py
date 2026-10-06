"""Data Coordinator for Nuki Web."""
import logging
import asyncio
from datetime import timedelta
from typing import Dict, Any

from aiohttp import ClientResponseError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import NukiWebApi
from .activity import SIGNAL_LOG
from .const import CONFIG_ENDPOINTS, DOMAIN

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
        # Activity log state. Logs need the smartlock.log scope, so they are
        # optional: `logs_available` is only true once a fetch has succeeded.
        self.logs_available = False
        self.last_logs: Dict[int, Dict[str, Any]] = {}
        self._logs_forbidden = False
        self._seen_log_ids: set[str] | None = None

    async def _async_update_data(self) -> Dict[int, Dict[str, Any]]:
        """Fetch data from API endpoint."""
        try:
            smartlocks = await self.api.get_smartlocks()
            # Convert list to dict keyed by smartlockId
            data = {lock["smartlockId"]: lock for lock in smartlocks}
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

        await self._async_update_logs(data)
        return data

    async def _async_update_logs(self, data: Dict[int, Dict[str, Any]]) -> None:
        """Fetch the activity log and dispatch entries not seen before.

        Failures here never fail the main update.
        """
        if self._logs_forbidden:
            return
        try:
            logs = await self.api.get_logs()
        except ClientResponseError as err:
            if err.status in (401, 403):
                _LOGGER.warning(
                    "The API token cannot read the activity log (needs the "
                    "smartlock.log scope); activity entities are disabled"
                )
                self._logs_forbidden = True
            else:
                _LOGGER.debug("Error fetching activity log: %s", err)
            return
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Error fetching activity log: %s", err)
            return

        self.logs_available = True
        logs = [log for log in logs if log.get("smartlockId") in data]
        # Logs are newest first, so the first one seen per lock is the latest
        newest: Dict[int, Dict[str, Any]] = {}
        for log in logs:
            newest.setdefault(log["smartlockId"], log)
        self.last_logs.update(newest)

        seen, self._seen_log_ids = self._seen_log_ids, {log["id"] for log in logs}
        if seen is None:
            return  # first fetch: do not replay history as events
        for log in reversed(logs):
            if log["id"] not in seen:
                async_dispatcher_send(
                    self.hass, SIGNAL_LOG.format(log["smartlockId"]), log
                )

    async def async_update_config(
        self, smartlock_id: int, section: str, key: str, value: Any
    ) -> None:
        """Change one config value.

        The API validates the whole config object (several fields are marked as
        required), so the current section is sent back with the single change.
        """
        current = self.data[smartlock_id][section]
        body = {
            k: v for k, v in current.items() if k != "operationId" and v is not None
        }
        body[key] = value
        await self.api.update_config(smartlock_id, CONFIG_ENDPOINTS[section], body)
        # The device applies the change asynchronously, reflect it right away
        current[key] = value
        self.async_set_updated_data(self.data)
