"""Binary Sensor platform for Nuki Web."""
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
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
