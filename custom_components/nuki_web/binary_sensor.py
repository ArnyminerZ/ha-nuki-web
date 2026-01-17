"""Binary Sensor platform for Nuki Web."""
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.const import EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NukiWebCoordinator

_LOGGER = logging.getLogger(__name__)

DOOR_STATE_CLOSED = 2
DOOR_STATE_OPEN = 3

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
    
        if "config" in smartlock:
             entities.append(NukiConfigBinarySensor(coordinator, smartlock_id, "fobPaired", "config", "fob_paired"))

    async_add_entities(entities)

class NukiConfigBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Nuki Web configuration binary sensor."""

    def __init__(
        self, 
        coordinator: NukiWebCoordinator, 
        smartlock_id: int, 
        key: str, 
        config_type: str, 
        translation_key: str
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._smartlock_id = smartlock_id
        self._key = key
        self._config_type = config_type
        self._attr_has_entity_name = True
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{smartlock_id}_{key}"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self._smartlock_id in self.coordinator.data

    @property
    def device_info(self):
        """Return device info."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        return {
            "identifiers": {(DOMAIN, str(self._smartlock_id))},
            "name": data["name"],
            "manufacturer": "Nuki",
            "model": f"Smart Lock Type {data.get('type')}",
            "sw_version": str(data.get("firmwareVersion")),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if sensor is on."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        return data.get(self._config_type, {}).get(self._key)

class NukiBatteryCriticalSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Nuki Web battery critical sensor."""

    def __init__(self, coordinator: NukiWebCoordinator, smartlock_id: int) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._smartlock_id = smartlock_id
        self._attr_has_entity_name = True
        self._attr_translation_key = "battery_critical"
        self._attr_unique_id = f"{smartlock_id}_battery_critical"
        self._attr_device_class = BinarySensorDeviceClass.BATTERY

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self._smartlock_id in self.coordinator.data

    @property
    def device_info(self):
        """Return device info."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        return {
            "identifiers": {(DOMAIN, str(self._smartlock_id))},
            "name": data["name"],
            "manufacturer": "Nuki",
            "model": f"Smart Lock Type {data.get('type')}",
            "sw_version": str(data.get("firmwareVersion")),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if battery is critical."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        return data["state"].get("batteryCritical")

class NukiDoorSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Nuki Web door sensor."""

    def __init__(self, coordinator: NukiWebCoordinator, smartlock_id: int) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._smartlock_id = smartlock_id
        self._attr_has_entity_name = True
        self._attr_translation_key = "door"
        self._attr_unique_id = f"{smartlock_id}_door"
        self._attr_device_class = BinarySensorDeviceClass.DOOR

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self._smartlock_id in self.coordinator.data

    @property
    def device_info(self):
        """Return device info."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        return {
            "identifiers": {(DOMAIN, str(self._smartlock_id))},
            "name": data["name"],
            "manufacturer": "Nuki",
            "model": f"Smart Lock Type {data.get('type')}",
            "sw_version": str(data.get("firmwareVersion")),
        }

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

class NukiRingToOpenSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Nuki Web Ring to Open sensor."""

    def __init__(self, coordinator: NukiWebCoordinator, smartlock_id: int) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._smartlock_id = smartlock_id
        self._attr_has_entity_name = True
        self._attr_translation_key = "ring_to_open"
        self._attr_unique_id = f"{smartlock_id}_rto"
        # No specific device class, maybe RUNNING?
        
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self._smartlock_id in self.coordinator.data

    @property
    def device_info(self):
        """Return device info."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        return {
            "identifiers": {(DOMAIN, str(self._smartlock_id))},
            "name": data["name"],
            "manufacturer": "Nuki",
            "model": f"Smart Lock Type {data.get('type')}",
            "sw_version": str(data.get("firmwareVersion")),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if Ring to Open is active."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        state = data["state"].get("state")
        # Opener state 3 is Ring to Open Active
        return state == 3
