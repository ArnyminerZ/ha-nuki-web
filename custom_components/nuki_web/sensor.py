"""Sensor platform for Nuki Web."""
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NukiWebCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Nuki Web sensor."""
    coordinator: NukiWebCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    for smartlock_id, smartlock in coordinator.data.items():
        if "batteryCharge" in smartlock["state"]:
             entities.append(NukiBatterySensor(coordinator, smartlock_id))
    
        if "config" in smartlock:
             entities.append(NukiConfigSensor(coordinator, smartlock_id, "capabilities", "config", "capabilities"))
             entities.append(NukiConfigSensor(coordinator, smartlock_id, "timezoneId", "config", "timezone_id"))
             entities.append(NukiConfigSensor(coordinator, smartlock_id, "timezoneOffset", "config", "timezone_offset"))
    
    async_add_entities(entities)

class NukiConfigSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Nuki Web configuration sensor."""

    def __init__(
        self, 
        coordinator: NukiWebCoordinator, 
        smartlock_id: int, 
        key: str, 
        config_type: str, 
        translation_key: str
    ) -> None:
        """Initialize the sensor."""
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
    def native_value(self) -> str | int | None:
        """Return the state of the sensor."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        return data.get(self._config_type, {}).get(self._key)

class NukiBatterySensor(CoordinatorEntity, SensorEntity):
    """Representation of a Nuki Web battery sensor."""

    def __init__(self, coordinator: NukiWebCoordinator, smartlock_id: int) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._smartlock_id = smartlock_id
        self._attr_has_entity_name = True
        self._attr_translation_key = "battery"
        self._attr_unique_id = f"{smartlock_id}_battery"
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "%"

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
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        return data["state"].get("batteryCharge")
