"""Select platform for Nuki Web (configuration values)."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import NukiWebCoordinator
from .entity import NukiConfigDescriptionMixin, NukiConfigEntity, config_value_exists

TYPE_OPENER = 2
LOCK_TYPES = (0, 3, 4, 5)

LNG_TIMEOUTS = (5, 10, 15, 20, 30, 45, 60)
UNLATCH_DURATIONS = (1, 3, 5, 7, 10, 15, 20, 30)
MOTOR_SPEEDS = {0: "standard", 1: "fast", 2: "slow"}
ADVERTISING_MODES = {0: "automatic", 1: "normal", 2: "slow", 3: "slowest"}
BUZZER_VOLUMES = {0: "off", 1: "low", 2: "normal"}
SOUNDS = {0: "no_sound", 1: "sound_1", 2: "sound_2", 3: "sound_3"}
LOCK_BUTTON_ACTIONS = {
    0: "no_action",
    1: "intelligent",
    2: "unlock",
    3: "lock",
    4: "unlatch",
    5: "lock_n_go",
    6: "show_status",
}
OPENER_BUTTON_ACTIONS = {
    0: "no_action",
    1: "toggle_rto",
    2: "activate_rto",
    3: "deactivate_rto",
    4: "toggle_cm",
    5: "activate_cm",
    6: "deactivate_cm",
    7: "open",
}


@dataclass(frozen=True, kw_only=True)
class NukiConfigSelectDescription(NukiConfigDescriptionMixin, SelectEntityDescription):
    """Describes a select backed by an integer config value.

    `option_map` maps the API value to the option shown, as value/option pairs.
    """

    option_map: tuple[tuple[int, str], ...]


def _select(
    key: str,
    section: str,
    config_key: str,
    option_map: dict[int, str],
    types: tuple[int, ...] | None = None,
) -> NukiConfigSelectDescription:
    return NukiConfigSelectDescription(
        key=key,
        translation_key=key,
        entity_category=EntityCategory.CONFIG,
        section=section,
        config_key=config_key,
        types=types,
        option_map=tuple(option_map.items()),
    )


SELECTS: tuple[NukiConfigSelectDescription, ...] = (
    _select("lng_timeout", "advanced", "lngTimeout", {v: str(v) for v in LNG_TIMEOUTS}),
    _select("unlatch_duration", "advanced", "unlatchDuration", {v: str(v) for v in UNLATCH_DURATIONS}),
    _select("motor_speed", "advanced", "motorSpeed", MOTOR_SPEEDS),
    _select("advertising_mode", "config", "advertisingMode", ADVERTISING_MODES),
    _select("buzzer_volume", "advanced", "buzzerVolume", BUZZER_VOLUMES, types=(3,)),
    _select("single_button_press_action", "advanced", "singleButtonPressAction", LOCK_BUTTON_ACTIONS, types=LOCK_TYPES),
    _select("double_button_press_action", "advanced", "doubleButtonPressAction", LOCK_BUTTON_ACTIONS, types=LOCK_TYPES),
    _select("opener_single_button_press_action", "advanced", "singleButtonPressAction", OPENER_BUTTON_ACTIONS, types=(TYPE_OPENER,)),
    _select("opener_double_button_press_action", "advanced", "doubleButtonPressAction", OPENER_BUTTON_ACTIONS, types=(TYPE_OPENER,)),
    _select("sound_ring", "advanced", "soundRing", SOUNDS, types=(TYPE_OPENER,)),
    _select("sound_open", "advanced", "soundOpen", SOUNDS, types=(TYPE_OPENER,)),
    _select("sound_rto", "advanced", "soundRto", SOUNDS, types=(TYPE_OPENER,)),
    _select("sound_cm", "advanced", "soundCm", SOUNDS, types=(TYPE_OPENER,)),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Nuki Web selects."""
    coordinator: NukiWebCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        NukiConfigSelect(coordinator, smartlock_id, description)
        for smartlock_id, smartlock in coordinator.data.items()
        for description in SELECTS
        if config_value_exists(smartlock, description)
    )


class NukiConfigSelect(NukiConfigEntity, SelectEntity):
    """A select for an integer smartlock config value."""

    entity_description: NukiConfigSelectDescription

    def __init__(
        self,
        coordinator: NukiWebCoordinator,
        smartlock_id: int,
        description: NukiConfigSelectDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, smartlock_id, description)
        self._to_option = dict(description.option_map)
        self._to_value = {option: value for value, option in description.option_map}
        self._attr_options = list(self._to_option.values())

    @property
    def current_option(self) -> str | None:
        """Return the selected option."""
        return self._to_option.get(self.config_value)

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        await self.async_set_config_value(self._to_value[option])
