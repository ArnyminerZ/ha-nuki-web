"""Number platform for Nuki Web."""
import logging

from homeassistant.components.number import NumberEntity
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
    """Set up Nuki Web number."""
    coordinator: NukiWebCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    for smartlock_id, smartlock in coordinator.data.items():
        if "config" in smartlock:
            entities.append(
                NukiConfigNumber(coordinator, smartlock_id, "ledBrightness", "config", "led_brightness", 0, 5)
            )
    
    async_add_entities(entities)

class NukiConfigNumber(CoordinatorEntity, NumberEntity):
    """Representation of a Nuki Web configuration number."""

    def __init__(
        self, 
        coordinator: NukiWebCoordinator, 
        smartlock_id: int, 
        key: str, 
        config_type: str, 
        translation_key: str,
        min_value: float,
        max_value: float,
    ) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        self._smartlock_id = smartlock_id
        self._key = key
        self._config_type = config_type
        self._attr_has_entity_name = True
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{smartlock_id}_{key}"
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = 1

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
    def native_value(self) -> float | None:
        """Return the state of the entity."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        return data.get(self._config_type, {}).get(self._key)

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        # Value is float, but API expects int often. Casting to int.
        int_value = int(value)
        if self._config_type == "config":
             await self.coordinator.api.update_smartlock_config(self._smartlock_id, **{self._key: int_value})
        elif self._config_type == "advancedConfig":
             await self.coordinator.api.update_smartlock_advanced_config(self._smartlock_id, **{self._key: int_value})
        
        await self.coordinator.async_request_refresh()
