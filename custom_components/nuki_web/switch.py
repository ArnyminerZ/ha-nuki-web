"""Switch platform for Nuki Web (Opener ring to open and continuous mode)."""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import NukiWebCoordinator
from .entity import NukiEntity

_LOGGER = logging.getLogger(__name__)

TYPE_OPENER = 2

# Opener actions
ACTION_ACTIVATE_RTO = 1
ACTION_DEACTIVATE_RTO = 2
ACTION_ACTIVATE_CM = 6
ACTION_DEACTIVATE_CM = 7

# Opener state / mode values
OPENER_STATE_RTO_ACTIVE = 3
MODE_CONTINUOUS = 3


@dataclass(frozen=True, kw_only=True)
class NukiSwitchDescription(SwitchEntityDescription):
    """Describes a Nuki Web switch."""

    is_on_fn: Callable[[dict[str, Any]], bool | None]
    on_action: int
    off_action: int


SWITCHES: tuple[NukiSwitchDescription, ...] = (
    NukiSwitchDescription(
        key="ring_to_open_switch",
        translation_key="ring_to_open_switch",
        is_on_fn=lambda data: data["state"].get("state") == OPENER_STATE_RTO_ACTIVE,
        on_action=ACTION_ACTIVATE_RTO,
        off_action=ACTION_DEACTIVATE_RTO,
    ),
    NukiSwitchDescription(
        key="continuous_mode",
        translation_key="continuous_mode",
        is_on_fn=lambda data: data["state"].get("mode") == MODE_CONTINUOUS,
        on_action=ACTION_ACTIVATE_CM,
        off_action=ACTION_DEACTIVATE_CM,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Nuki Web switches."""
    coordinator: NukiWebCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        NukiSwitch(coordinator, smartlock_id, description)
        for smartlock_id, smartlock in coordinator.data.items()
        if smartlock.get("type") == TYPE_OPENER
        for description in SWITCHES
    )


class NukiSwitch(NukiEntity, SwitchEntity):
    """An Opener switch that triggers a lock action."""

    entity_description: NukiSwitchDescription

    def __init__(
        self,
        coordinator: NukiWebCoordinator,
        smartlock_id: int,
        description: NukiSwitchDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, smartlock_id)
        self.entity_description = description
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{smartlock_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return true if the feature is active."""
        if not self.available:
            return None
        return self.entity_description.is_on_fn(self.coordinator.data[self._smartlock_id])

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Activate the feature."""
        await self.coordinator.api.post_action(
            self._smartlock_id, self.entity_description.on_action
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Deactivate the feature."""
        await self.coordinator.api.post_action(
            self._smartlock_id, self.entity_description.off_action
        )
        await self.coordinator.async_request_refresh()
