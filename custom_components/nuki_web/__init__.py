"""The Nuki Web integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client, device_registry as dr

from .const import DOMAIN
from .coordinator import NukiWebCoordinator
from .api import NukiWebApi

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.LOCK, Platform.SENSOR, Platform.BINARY_SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Nuki Web from a config entry."""
    token = entry.data[CONF_API_TOKEN]
    session = aiohttp_client.async_get_clientsession(hass)
    api = NukiWebApi(token, session)
    coordinator = NukiWebCoordinator(hass, api)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register update listener to reconcile devices on every update
    coordinator.async_add_listener(lambda: _async_reconcile_devices(hass, coordinator, entry))

    return True

def _async_reconcile_devices(hass: HomeAssistant, coordinator: NukiWebCoordinator, entry: ConfigEntry) -> None:
    """Reconcile devices with the coordinator data."""
    device_registry = dr.async_get(hass)
    devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    
    # Coordinator data is a dict of smartlock_id -> data
    current_smartlock_ids = set(coordinator.data.keys())
    
    for device in devices:
        # Check if the device matches our domain and has identifiers
        for identifier in device.identifiers:
            if identifier[0] == DOMAIN:
                smartlock_id = int(identifier[1])
                if smartlock_id not in current_smartlock_ids:
                    _LOGGER.info("Removing Nuki device %s as it is no longer in the API", smartlock_id)
                    device_registry.async_remove_device(device.id)
                break

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
