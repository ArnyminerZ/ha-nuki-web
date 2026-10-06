"""Number platform for Nuki Web (configuration values)."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import NukiWebCoordinator
from .entity import NukiConfigDescriptionMixin, NukiConfigEntity, config_value_exists

TYPE_OPENER = 2
TYPE_BOX = 1
TYPE_SMART_DOOR = 3


@dataclass(frozen=True, kw_only=True)
class NukiConfigNumberDescription(NukiConfigDescriptionMixin, NumberEntityDescription):
    """Describes a number backed by an integer config value."""


NUMBERS: tuple[NukiConfigNumberDescription, ...] = (
    NukiConfigNumberDescription(
        key="auto_lock_timeout",
        translation_key="auto_lock_timeout",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        native_min_value=2,
        native_max_value=1800,
        native_step=1,
        section="advanced",
        config_key="autoLockTimeout",
    ),
    NukiConfigNumberDescription(
        key="led_brightness",
        translation_key="led_brightness",
        entity_category=EntityCategory.CONFIG,
        native_min_value=0,
        native_max_value=5,
        native_step=1,
        section="config",
        config_key="ledBrightness",
        types=(TYPE_BOX, TYPE_SMART_DOOR),
    ),
    NukiConfigNumberDescription(
        key="rto_timeout",
        translation_key="rto_timeout",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        native_min_value=1,
        native_max_value=120,
        native_step=1,
        section="advanced",
        config_key="rtoTimeout",
        types=(TYPE_OPENER,),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Nuki Web numbers."""
    coordinator: NukiWebCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        NukiConfigNumber(coordinator, smartlock_id, description)
        for smartlock_id, smartlock in coordinator.data.items()
        for description in NUMBERS
        if config_value_exists(smartlock, description)
    )


class NukiConfigNumber(NukiConfigEntity, NumberEntity):
    """A number for an integer smartlock config value."""

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        return self.config_value

    async def async_set_native_value(self, value: float) -> None:
        """Set a new value."""
        await self.async_set_config_value(int(value))
