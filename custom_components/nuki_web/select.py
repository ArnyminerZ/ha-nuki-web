"""Select platform for Nuki Web."""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NukiWebCoordinator

_LOGGER = logging.getLogger(__name__)

# Option Mappings
BATTERY_TYPE_MAP = {
    0: "alkali",
    1: "accumulator",
    2: "lithium"
}

BUTTON_ACTION_MAP = {
    0: "no_action",
    1: "intelligent",
    2: "unlock",
    3: "lock",
    4: "unlatch",
    5: "lock_n_go",
    6: "show_status"
}

MOTOR_SPEED_MAP = {
    0: "standard",
    1: "fast",
    2: "slow"
}

# Timeout options are just the numbers as strings
LNG_TIMEOUT_OPTIONS = ["5", "10", "15", "20", "30", "45", "60"]
UNLATCH_DURATION_OPTIONS = ["1", "3", "5", "7", "10", "15", "20", "30"]

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Nuki Web select."""
    coordinator: NukiWebCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    for smartlock_id, smartlock in coordinator.data.items():
        if "advancedConfig" in smartlock:
             # LNG Timeout
             entities.append(
                 NukiConfigSelect(coordinator, smartlock_id, "lngTimeout", "advancedConfig", "lng_timeout", LNG_TIMEOUT_OPTIONS)
             )
             # Unlatch Duration
             entities.append(
                 NukiConfigSelect(coordinator, smartlock_id, "unlatchDuration", "advancedConfig", "unlatch_duration", UNLATCH_DURATION_OPTIONS)
             )
             # Battery Type
             entities.append(
                 NukiConfigMappedSelect(coordinator, smartlock_id, "batteryType", "advancedConfig", "battery_type", BATTERY_TYPE_MAP)
             )
             # Single Button Press
             entities.append(
                 NukiConfigMappedSelect(coordinator, smartlock_id, "singleButtonPressAction", "advancedConfig", "single_button_action", BUTTON_ACTION_MAP)
             )
             # Double Button Press
             entities.append(
                 NukiConfigMappedSelect(coordinator, smartlock_id, "doubleButtonPressAction", "advancedConfig", "double_button_action", BUTTON_ACTION_MAP)
             )
             # Motor Speed
             entities.append(
                 NukiConfigMappedSelect(coordinator, smartlock_id, "motorSpeed", "advancedConfig", "motor_speed", MOTOR_SPEED_MAP)
             )

    async_add_entities(entities)

class NukiConfigSelect(CoordinatorEntity, SelectEntity):
    """Representation of a Nuki Web configuration select (string options)."""

    def __init__(
        self, 
        coordinator: NukiWebCoordinator, 
        smartlock_id: int, 
        key: str, 
        config_type: str, 
        translation_key: str,
        options: list[str]
    ) -> None:
        """Initialize the select."""
        super().__init__(coordinator)
        self._smartlock_id = smartlock_id
        self._key = key
        self._config_type = config_type
        self._attr_has_entity_name = True
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{smartlock_id}_{key}"
        self._attr_options = options

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
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        val = data.get(self._config_type, {}).get(self._key)
        if val is None:
            return None
        return str(val)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        # Convert back to int for API
        int_value = int(option)
        if self._config_type == "config":
             await self.coordinator.api.update_smartlock_config(self._smartlock_id, **{self._key: int_value})
        elif self._config_type == "advancedConfig":
             await self.coordinator.api.update_smartlock_advanced_config(self._smartlock_id, **{self._key: int_value})
        
        await self.coordinator.async_request_refresh()

class NukiConfigMappedSelect(NukiConfigSelect):
    """Representation of a Nuki Web configuration select with mapped values."""

    def __init__(
        self, 
        coordinator: NukiWebCoordinator, 
        smartlock_id: int, 
        key: str, 
        config_type: str, 
        translation_key: str,
        mapping: dict[int, str]
    ) -> None:
        """Initialize the mapped select."""
        self._mapping = mapping
        self._reverse_mapping = {v: k for k, v in mapping.items()}
        options = list(mapping.values())
        super().__init__(coordinator, smartlock_id, key, config_type, translation_key, options)

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        val = data.get(self._config_type, {}).get(self._key)
        if val is None:
            return None
        return self._mapping.get(val, "unknown")

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        api_value = self._reverse_mapping.get(option)
        if api_value is None:
            _LOGGER.error("Invalid option selected: %s", option)
            return

        if self._config_type == "config":
             await self.coordinator.api.update_smartlock_config(self._smartlock_id, **{self._key: api_value})
        elif self._config_type == "advancedConfig":
             await self.coordinator.api.update_smartlock_advanced_config(self._smartlock_id, **{self._key: api_value})
        
        await self.coordinator.async_request_refresh()
