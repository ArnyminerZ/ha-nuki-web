"""Event platform for Nuki Web (activity log)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .activity import EVENT_TYPES, SIGNAL_LOG, log_attributes, log_event_type
from .const import DOMAIN
from .coordinator import NukiWebCoordinator
from .entity import NukiEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Nuki Web events."""
    coordinator: NukiWebCoordinator = hass.data[DOMAIN][entry.entry_id]
    if not coordinator.logs_available:
        return
    async_add_entities(
        NukiActivityEvent(coordinator, smartlock_id) for smartlock_id in coordinator.data
    )


class NukiActivityEvent(NukiEntity, EventEntity):
    """Fires an event for every new entry in the smartlock activity log."""

    _attr_event_types = EVENT_TYPES

    def __init__(self, coordinator: NukiWebCoordinator, smartlock_id: int) -> None:
        """Initialize."""
        super().__init__(coordinator, smartlock_id)
        self._attr_has_entity_name = True
        self._attr_translation_key = "activity"
        self._attr_unique_id = f"{smartlock_id}_activity"

    async def async_added_to_hass(self) -> None:
        """Subscribe to new log entries."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_LOG.format(self._smartlock_id), self._handle_log
            )
        )

    @callback
    def _handle_log(self, log: dict[str, Any]) -> None:
        event_type = log_event_type(log)
        if event_type is None:
            return
        self._trigger_event(event_type, log_attributes(log))
        self.async_write_ha_state()
