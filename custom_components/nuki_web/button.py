"""Button platform for Nuki Web."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import NukiWebCoordinator
from .entity import NukiEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Nuki Web buttons."""
    coordinator: NukiWebCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        NukiSyncButton(coordinator, smartlock_id) for smartlock_id in coordinator.data
    )


class NukiSyncButton(NukiEntity, ButtonEntity):
    """Button that forces Nuki to sync a smartlock."""

    def __init__(self, coordinator: NukiWebCoordinator, smartlock_id: int) -> None:
        """Initialize."""
        super().__init__(coordinator, smartlock_id)
        self._attr_has_entity_name = True
        self._attr_translation_key = "sync"
        self._attr_unique_id = f"{smartlock_id}_sync"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_press(self) -> None:
        """Request a sync, then refresh the data."""
        await self.coordinator.api.post_sync(self._smartlock_id)
        await self.coordinator.async_request_refresh()
