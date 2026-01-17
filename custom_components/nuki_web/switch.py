"""Switch platform for Nuki Web."""
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up Nuki Web switch."""
    coordinator: NukiWebCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    for smartlock_id, smartlock in coordinator.data.items():
        if "config" in smartlock:
            entities.extend([
                NukiConfigSwitch(coordinator, smartlock_id, "autoUnlatch", "config", "auto_unlatch"),
                NukiConfigSwitch(coordinator, smartlock_id, "liftUpHandle", "config", "lift_up_handle"),
                NukiConfigSwitch(coordinator, smartlock_id, "pairingEnabled", "config", "pairing_enabled"),
                NukiConfigSwitch(coordinator, smartlock_id, "buttonEnabled", "config", "button_enabled"),
                NukiConfigSwitch(coordinator, smartlock_id, "ledEnabled", "config", "led_enabled"),
            ])
            
        if "advancedConfig" in smartlock:
             entities.extend([
                 NukiConfigSwitch(coordinator, smartlock_id, "automaticBatteryTypeDetection", "advancedConfig", "auto_battery_detection"),
                 NukiConfigSwitch(coordinator, smartlock_id, "detachedCylinder", "advancedConfig", "detached_cylinder"),
                 NukiConfigSwitch(coordinator, smartlock_id, "autoUpdateEnabled", "advancedConfig", "auto_update_enabled"),
                 NukiConfigSwitch(coordinator, smartlock_id, "autoLock", "advancedConfig", "auto_lock"),
             ])
    
    async_add_entities(entities)

class NukiConfigSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Nuki Web configuration switch."""

    def __init__(
        self, 
        coordinator: NukiWebCoordinator, 
        smartlock_id: int, 
        key: str, 
        config_type: str, 
        translation_key: str
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._smartlock_id = smartlock_id
        self._key = key
        self._config_type = config_type
        self._attr_has_entity_name = True
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{smartlock_id}_{key}"

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
        """Return true if switch is on."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        return data.get(self._config_type, {}).get(self._key)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._async_set_state(False)

    async def _async_set_state(self, state: bool) -> None:
        """Set the state."""
        if self._config_type == "config":
             await self.coordinator.api.update_smartlock_config(self._smartlock_id, **{self._key: state})
        elif self._config_type == "advancedConfig":
             await self.coordinator.api.update_smartlock_advanced_config(self._smartlock_id, **{self._key: state})
        
        # Optimistic update
        # self.coordinator.data[self._smartlock_id][self._config_type][self._key] = state
        # self.async_write_ha_state()
        
        await self.coordinator.async_request_refresh()
