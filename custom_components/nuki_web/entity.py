"""Base entity for Nuki Web."""
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
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
        }.get(device_type, f"Unknown ({device_type})")

        return {
            "identifiers": {(DOMAIN, str(self._smartlock_id))},
            "name": data["name"],
            "manufacturer": "Nuki",
            "model": device_type_name,
            "sw_version": str(data.get("firmwareVersion")),
        }
