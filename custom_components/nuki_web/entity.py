"""Base entity for Nuki Web."""
from dataclasses import dataclass
from typing import Any

from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import Entity

from .const import ADVANCED_SECTIONS, DOMAIN, decode_firmware_version
from .coordinator import NukiWebCoordinator

class NukiEntity(CoordinatorEntity, Entity):
    """Base class for Nuki Web entities."""

    def __init__(self, coordinator: NukiWebCoordinator, smartlock_id: int) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._smartlock_id = smartlock_id

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
        
        device_type = data.get("type")
        device_type_name = {
            0: "Smart Lock", # Keyturner
            1: "Bridge", # Box
            2: "Opener",
            3: "Smart Door",
            4: "Smart Lock 3.0/4. Gen",
            5: "Smart Lock Ultra"
        }.get(device_type, f"Unknown ({device_type})")

        # Smartlock 5 variants
        if device_type == 5:
            variant = {1: "Go", 2: "Pro", 3: "Ultra"}.get(
                (data.get("config") or {}).get("productVariant")
            )
            if variant:
                device_type_name = f"Smart Lock {variant}"

        return {
            "identifiers": {(DOMAIN, str(self._smartlock_id))},
            "name": data["name"],
            "manufacturer": "Nuki",
            "model": device_type_name,
            "sw_version": decode_firmware_version(data.get("firmwareVersion")),
        }


@dataclass(frozen=True, kw_only=True)
class NukiConfigDescriptionMixin:
    """Where a configurable value lives in the smartlock data.

    `section` is a smartlock key (e.g. "config") or "advanced", which resolves to
    the advanced config section matching the device type. `types` optionally
    restricts the entity to some device types.
    """

    section: str
    config_key: str
    types: tuple[int, ...] | None = None


def config_section(data: dict[str, Any], section: str) -> str | None:
    """Resolve the smartlock key holding a config section."""
    if section == "advanced":
        return ADVANCED_SECTIONS.get(data.get("type"))
    return section


def config_value_exists(data: dict[str, Any], description: NukiConfigDescriptionMixin) -> bool:
    """Return true if the device reports the value described."""
    if description.types is not None and data.get("type") not in description.types:
        return False
    section = config_section(data, description.section)
    if section is None:
        return False
    return (data.get(section) or {}).get(description.config_key) is not None


class NukiConfigEntity(NukiEntity):
    """Base class for entities that read and write a smartlock config value."""

    entity_description: NukiConfigDescriptionMixin

    def __init__(
        self,
        coordinator: NukiWebCoordinator,
        smartlock_id: int,
        description: NukiConfigDescriptionMixin,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, smartlock_id)
        self.entity_description = description
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{smartlock_id}_{description.key}"

    @property
    def config_value(self) -> Any:
        """Return the current raw config value."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        section = config_section(data, self.entity_description.section)
        return (data.get(section) or {}).get(self.entity_description.config_key)

    async def async_set_config_value(self, value: Any) -> None:
        """Write a new raw config value."""
        data = self.coordinator.data[self._smartlock_id]
        section = config_section(data, self.entity_description.section)
        await self.coordinator.async_update_config(
            self._smartlock_id, section, self.entity_description.config_key, value
        )
