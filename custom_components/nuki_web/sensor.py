"""Sensor platform for Nuki Web."""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN, decode_firmware_version
from .coordinator import NukiWebCoordinator
from .entity import NukiEntity

_LOGGER = logging.getLogger(__name__)

TYPE_OPENER = 2

DOOR_STATES = {
    0: "unavailable",
    1: "deactivated",
    2: "closed",
    3: "opened",
    4: "unknown",
    5: "calibrating",
    16: "uncalibrated",
    240: "removed",
}
MODES = {
    0: "uninitialized",
    1: "pairing",
    2: "door",
    3: "continuous",
    4: "maintenance",
    5: "off_door_charging",
}
SERVER_STATES = {
    0: "ok",
    1: "unregistered",
    2: "auth_uuid_invalid",
    3: "auth_invalid",
    4: "offline",
}
ADMIN_PIN_STATES = {0: "ok", 1: "missing", 2: "invalid"}
TRIGGERS = {
    0: "system",
    1: "manual",
    2: "button",
    3: "automatic",
    4: "web",
    5: "app",
    6: "continuous_mode",
    7: "accessory",
}
LOCK_ACTIONS = {
    1: "unlock",
    2: "lock",
    3: "unlatch",
    4: "lock_n_go",
    5: "lock_n_go_unlatch",
}
OPENER_ACTIONS = {
    1: "activate_rto",
    2: "deactivate_rto",
    3: "open",
    6: "activate_continuous_mode",
    7: "deactivate_continuous_mode",
}
LAST_ACTION_OPTIONS = sorted({*LOCK_ACTIONS.values(), *OPENER_ACTIONS.values(), "unknown"})


def _last_action(data: dict[str, Any]) -> str | None:
    action = data["state"].get("lastAction")
    if action is None:
        return None
    actions = OPENER_ACTIONS if data.get("type") == TYPE_OPENER else LOCK_ACTIONS
    return actions.get(action, "unknown")


def _mapped(key: str, mapping: dict[int, str]) -> Callable[[dict[str, Any]], str | None]:
    def value_fn(data: dict[str, Any]) -> str | None:
        value = data["state"].get(key) if key in data["state"] else data.get(key)
        if value is None:
            return None
        return mapping.get(value, "unknown")

    return value_fn


def _ring_to_open_end(data: dict[str, Any]) -> datetime | None:
    end = data["state"].get("ringToOpenEnd")
    return dt_util.parse_datetime(end) if end else None


@dataclass(frozen=True, kw_only=True)
class NukiSensorDescription(SensorEntityDescription):
    """Describes a Nuki Web sensor."""

    value_fn: Callable[[dict[str, Any]], Any]
    exists_fn: Callable[[dict[str, Any]], bool] = lambda data: True


SENSORS: tuple[NukiSensorDescription, ...] = (
    NukiSensorDescription(
        key="door_state",
        translation_key="door_state",
        device_class=SensorDeviceClass.ENUM,
        options=sorted({*DOOR_STATES.values(), "unknown"}),
        value_fn=_mapped("doorState", DOOR_STATES),
        exists_fn=lambda data: "doorState" in data["state"],
    ),
    NukiSensorDescription(
        key="mode",
        translation_key="mode",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        options=sorted({*MODES.values(), "unknown"}),
        value_fn=_mapped("mode", MODES),
        exists_fn=lambda data: "mode" in data["state"],
    ),
    NukiSensorDescription(
        key="last_action",
        translation_key="last_action",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        options=LAST_ACTION_OPTIONS,
        value_fn=_last_action,
        exists_fn=lambda data: "lastAction" in data["state"],
    ),
    NukiSensorDescription(
        key="trigger",
        translation_key="trigger",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        options=sorted({*TRIGGERS.values(), "unknown"}),
        value_fn=_mapped("trigger", TRIGGERS),
        exists_fn=lambda data: "trigger" in data["state"],
    ),
    NukiSensorDescription(
        key="admin_pin_state",
        translation_key="admin_pin_state",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        options=sorted({*ADMIN_PIN_STATES.values(), "unknown"}),
        value_fn=_mapped("adminPinState", ADMIN_PIN_STATES),
        exists_fn=lambda data: "adminPinState" in data,
    ),
    NukiSensorDescription(
        key="firmware_version",
        translation_key="firmware_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: decode_firmware_version(data.get("firmwareVersion")),
        exists_fn=lambda data: data.get("firmwareVersion") is not None,
    ),
    NukiSensorDescription(
        key="hardware_version",
        translation_key="hardware_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("hardwareVersion"),
        exists_fn=lambda data: data.get("hardwareVersion") is not None,
    ),
    NukiSensorDescription(
        key="ring_to_open_end",
        translation_key="ring_to_open_end",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_ring_to_open_end,
        exists_fn=lambda data: data.get("type") == TYPE_OPENER,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Nuki Web sensor."""
    coordinator: NukiWebCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []
    for smartlock_id, smartlock in coordinator.data.items():
        if "batteryCharge" in smartlock["state"]:
            entities.append(NukiBatterySensor(coordinator, smartlock_id))
        entities.extend(
            NukiDescribedSensor(coordinator, smartlock_id, description)
            for description in SENSORS
            if description.exists_fn(smartlock)
        )

    async_add_entities(entities)


class NukiBatterySensor(NukiEntity, SensorEntity):
    """Representation of a Nuki Web battery sensor."""

    def __init__(self, coordinator: NukiWebCoordinator, smartlock_id: int) -> None:
        """Initialize."""
        super().__init__(coordinator, smartlock_id)
        self._attr_has_entity_name = True
        self._attr_translation_key = "battery"
        self._attr_unique_id = f"{smartlock_id}_battery"
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "%"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        return data["state"].get("batteryCharge")


class NukiDescribedSensor(NukiEntity, SensorEntity):
    """A Nuki Web sensor defined by an entity description."""

    entity_description: NukiSensorDescription

    def __init__(
        self,
        coordinator: NukiWebCoordinator,
        smartlock_id: int,
        description: NukiSensorDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, smartlock_id)
        self.entity_description = description
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{smartlock_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.available:
            return None
        return self.entity_description.value_fn(self.coordinator.data[self._smartlock_id])
