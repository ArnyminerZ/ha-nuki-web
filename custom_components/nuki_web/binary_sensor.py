"""Binary Sensor platform for Nuki Web."""
import logging

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NukiWebCoordinator
from .entity import NukiEntity

_LOGGER = logging.getLogger(__name__)

DOOR_STATE_CLOSED = 2
DOOR_STATE_OPEN = 3

KEYPAD_MOUNTING_MOVED = 2
KEYPAD_MOUNTING_ERROR = 255
SERVER_STATE_OK = 0


def _has_state(key: str) -> Callable[[dict[str, Any]], bool]:
    return lambda data: key in data["state"]


def _keypad_paired(data: dict[str, Any]) -> bool:
    config = data.get("config") or {}
    return (
        "keypadBatteryCritical" in data["state"]
        or bool(config.get("keypadPaired"))
        or bool(config.get("keypad2Paired"))
    )


@dataclass(frozen=True, kw_only=True)
class NukiBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a Nuki Web binary sensor."""

    value_fn: Callable[[dict[str, Any]], bool | None]
    exists_fn: Callable[[dict[str, Any]], bool] = lambda data: True


BINARY_SENSORS: tuple[NukiBinarySensorDescription, ...] = (
    NukiBinarySensorDescription(
        key="keypad_battery_critical",
        translation_key="keypad_battery_critical",
        device_class=BinarySensorDeviceClass.BATTERY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data["state"].get("keypadBatteryCritical"),
        exists_fn=_keypad_paired,
    ),
    NukiBinarySensorDescription(
        key="doorsensor_battery_critical",
        translation_key="doorsensor_battery_critical",
        device_class=BinarySensorDeviceClass.BATTERY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data["state"].get("doorsensorBatteryCritical"),
        exists_fn=_has_state("doorsensorBatteryCritical"),
    ),
    NukiBinarySensorDescription(
        key="battery_charging",
        translation_key="battery_charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda data: data["state"].get("batteryCharging"),
        exists_fn=_has_state("batteryCharging"),
    ),
    NukiBinarySensorDescription(
        key="keypad_tamper",
        translation_key="keypad_tamper",
        device_class=BinarySensorDeviceClass.TAMPER,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: (
            None
            if data["state"].get("keypadMountingState") is None
            else data["state"]["keypadMountingState"]
            in (KEYPAD_MOUNTING_MOVED, KEYPAD_MOUNTING_ERROR)
        ),
        exists_fn=_has_state("keypadMountingState"),
    ),
    NukiBinarySensorDescription(
        key="night_mode",
        translation_key="night_mode",
        value_fn=lambda data: data["state"].get("nightMode"),
        exists_fn=_has_state("nightMode"),
    ),
    NukiBinarySensorDescription(
        key="server_connectivity",
        translation_key="server_connectivity",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: (
            None
            if data.get("serverState") is None
            else data["serverState"] == SERVER_STATE_OK
        ),
        exists_fn=lambda data: "serverState" in data,
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Nuki Web binary sensor."""
    coordinator: NukiWebCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    for smartlock_id, smartlock in coordinator.data.items():
        entities.append(NukiBatteryCriticalSensor(coordinator, smartlock_id))
        
        # Add door sensor if supported (doorState is present and not unavailable/unknown)
        door_state = smartlock["state"].get("doorState")
        if door_state is not None:
             entities.append(NukiDoorSensor(coordinator, smartlock_id))
             
        # Ring to Open for Opener
        if smartlock.get("type") == 2:
            entities.append(NukiRingToOpenSensor(coordinator, smartlock_id))
    
    async_add_entities(entities)

class NukiBatteryCriticalSensor(NukiEntity, BinarySensorEntity):
    """Representation of a Nuki Web battery critical sensor."""

    def __init__(self, coordinator: NukiWebCoordinator, smartlock_id: int) -> None:
        """Initialize."""
        super().__init__(coordinator, smartlock_id)
        self._attr_has_entity_name = True
        self._attr_translation_key = "battery_critical"
        self._attr_unique_id = f"{smartlock_id}_battery_critical"
        self._attr_device_class = BinarySensorDeviceClass.BATTERY

    @property
    def is_on(self) -> bool | None:
        """Return true if battery is critical."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        return data["state"].get("batteryCritical")

class NukiDoorSensor(NukiEntity, BinarySensorEntity):
    """Representation of a Nuki Web door sensor."""

    def __init__(self, coordinator: NukiWebCoordinator, smartlock_id: int) -> None:
        """Initialize."""
        super().__init__(coordinator, smartlock_id)
        self._attr_has_entity_name = True
        self._attr_translation_key = "door"
        self._attr_unique_id = f"{smartlock_id}_door"
        self._attr_device_class = BinarySensorDeviceClass.DOOR

    @property
    def is_on(self) -> bool | None:
        """Return true if door is open."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        state = data["state"].get("doorState")
        if state == DOOR_STATE_OPEN:
            return True
        if state == DOOR_STATE_CLOSED:
            return False
        return None

class NukiRingToOpenSensor(NukiEntity, BinarySensorEntity):
    """Representation of a Nuki Web Ring to Open sensor."""

    def __init__(self, coordinator: NukiWebCoordinator, smartlock_id: int) -> None:
        """Initialize."""
        super().__init__(coordinator, smartlock_id)
        self._attr_has_entity_name = True
        self._attr_translation_key = "ring_to_open"
        self._attr_unique_id = f"{smartlock_id}_rto"
        # No specific device class, maybe RUNNING?

    @property
    def is_on(self) -> bool | None:
        """Return true if Ring to Open is active."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        state = data["state"].get("state")
        # Opener state 3 is Ring to Open Active
        return state == 3


class NukiDescribedBinarySensor(NukiEntity, BinarySensorEntity):
    """A Nuki Web binary sensor defined by an entity description."""

    entity_description: NukiBinarySensorDescription

    def __init__(
        self,
        coordinator: NukiWebCoordinator,
        smartlock_id: int,
        description: NukiBinarySensorDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, smartlock_id)
        self.entity_description = description
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{smartlock_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return the sensor state."""
        if not self.available:
            return None
        return self.entity_description.value_fn(self.coordinator.data[self._smartlock_id])
