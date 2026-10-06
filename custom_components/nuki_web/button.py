"""Button platform for Nuki Web."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .lock import ACTION_LOCK_N_GO, ACTION_LOCK_N_GO_UNLATCH
from .coordinator import NukiWebCoordinator
from .entity import NukiEntity

# Smart Lock 1/2, Smart Door, Smart Lock 3/4, Smart Lock 5
LOCK_N_GO_TYPES = (0, 3, 4, 5)
LOCK_N_GO_ACTIONS = {
    "lock_n_go": ACTION_LOCK_N_GO,
    "lock_n_go_unlatch": ACTION_LOCK_N_GO_UNLATCH,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Nuki Web buttons."""
    coordinator: NukiWebCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[ButtonEntity] = []
    for smartlock_id, smartlock in coordinator.data.items():
        entities.append(NukiSyncButton(coordinator, smartlock_id))
        # Lock 'n' go is only available on Smart Locks and Smart Doors
        if smartlock.get("type") in LOCK_N_GO_TYPES:
            entities.extend(
                NukiLockActionButton(coordinator, smartlock_id, key, action)
                for key, action in LOCK_N_GO_ACTIONS.items()
            )
    async_add_entities(entities)


class NukiSyncButton(NukiEntity, ButtonEntity):
    """Button that forces Nuki to sync a smartlock."""

    def __init__(self, coordinator: NukiWebCoordinator, smartlock_id: int) -> None:
        """Initialize."""
        super().__init__(coordinator, smartlock_id)
        self._attr_has_entity_name = True
        self._attr_translation_key = "sync"
        self._attr_unique_id = f"{smartlock_id}_sync"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_press(self) -> None:
        """Request a sync, then refresh the data."""
        await self.coordinator.api.post_sync(self._smartlock_id)
        await self.coordinator.async_request_refresh()


class NukiLockActionButton(NukiEntity, ButtonEntity):
    """Button that triggers a lock action such as lock 'n' go."""

    def __init__(
        self,
        coordinator: NukiWebCoordinator,
        smartlock_id: int,
        key: str,
        action: int,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, smartlock_id)
        self._action = action
        self._attr_has_entity_name = True
        self._attr_translation_key = key
        self._attr_unique_id = f"{smartlock_id}_{key}"

    async def async_press(self) -> None:
        """Send the action, then refresh the data."""
        await self.coordinator.api.post_action(self._smartlock_id, self._action)
        await self.coordinator.async_request_refresh()
