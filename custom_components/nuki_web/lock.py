"""Lock platform for Nuki Web."""
import logging
from typing import Any

from homeassistant.components.lock import LockEntity, LockEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NukiWebCoordinator

_LOGGER = logging.getLogger(__name__)

# Smartlock states
STATE_LOCKED = 1
STATE_UNLOCKING = 2
STATE_UNLOCKED = 3
STATE_LOCKING = 4
STATE_UNLATCHED = 5
STATE_UNLOCKED_LOCKED_NO_GO = 6
STATE_UNLATCHING = 7
STATE_MOTOR_BLOCKED = 254

# Opener states
OPENER_STATE_ONLINE = 1
OPENER_STATE_RTO_ACTIVE = 3
OPENER_STATE_OPEN = 5
OPENER_STATE_OPENING = 7

# Actions
ACTION_UNLOCK = 1
ACTION_LOCK = 2
ACTION_UNLATCH = 3
ACTION_LOCK_N_GO = 4
ACTION_LOCK_N_GO_UNLATCH = 5

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Nuki Web lock."""
    coordinator: NukiWebCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    for smartlock_id, smartlock in coordinator.data.items():
        entities.append(NukiLockEntity(coordinator, smartlock_id))
    
    async_add_entities(entities)

class NukiLockEntity(CoordinatorEntity, LockEntity):
    """Representation of a Nuki Web lock."""

    def __init__(self, coordinator: NukiWebCoordinator, smartlock_id: int) -> None:
        """Initialize the lock."""
        super().__init__(coordinator)
        self._smartlock_id = smartlock_id
        self._attr_has_entity_name = True
        self._attr_name = None
        self._attr_unique_id = f"{smartlock_id}_lock"
        self._attr_supported_features = LockEntityFeature.OPEN

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
    def is_locked(self) -> bool | None:
        """Return true if lock is locked."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        state = data["state"]["state"]
        type_id = data["type"]

        if type_id == 2: # Opener
            return state == OPENER_STATE_ONLINE

        return state == STATE_LOCKED

    @property
    def is_locking(self) -> bool | None:
        """Return true if lock is locking."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        state = data["state"]["state"]
        type_id = data["type"]
        if type_id == 2: return None # Opener doesn't really "lock" in motion usually
        return state == STATE_LOCKING

    @property
    def is_unlocking(self) -> bool | None:
        """Return true if lock is unlocking."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        state = data["state"]["state"]
        type_id = data["type"]
        if type_id == 2: return state == OPENER_STATE_OPENING
        return state in (STATE_UNLOCKING, STATE_UNLATCHING)

    @property
    def is_jammed(self) -> bool | None:
        """Return true if lock is jammed."""
        if not self.available:
            return None
        data = self.coordinator.data[self._smartlock_id]
        state = data["state"]["state"]
        return state == STATE_MOTOR_BLOCKED

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the lock."""
        await self.coordinator.api.post_action(self._smartlock_id, ACTION_LOCK)
        await self.coordinator.async_request_refresh()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the lock."""
        await self.coordinator.api.post_action(self._smartlock_id, ACTION_UNLOCK)
        await self.coordinator.async_request_refresh()

    async def async_open(self, **kwargs: Any) -> None:
        """Open the door latch."""
        await self.coordinator.api.post_action(self._smartlock_id, ACTION_UNLATCH)
        await self.coordinator.async_request_refresh()
