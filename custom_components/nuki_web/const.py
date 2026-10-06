"""Constants for the Nuki Web integration."""

DOMAIN = "nuki_web"
CONF_API_TOKEN = "api_token"
API_BASE_URL = "https://api.nuki.io"

# Smartlock config sections and the endpoint used to update each of them
CONFIG_ENDPOINTS = {
    "config": "config",
    "advancedConfig": "advanced/config",
    "openerAdvancedConfig": "advanced/openerconfig",
    "smartdoorAdvancedConfig": "advanced/smartdoorconfig",
}
# Advanced config section used by each smartlock type
ADVANCED_SECTIONS = {
    0: "advancedConfig",
    2: "openerAdvancedConfig",
    3: "smartdoorAdvancedConfig",
    4: "advancedConfig",
    5: "advancedConfig",
}

# Attributes
ATTR_BATTERY_CRITICAL = "battery_critical"
ATTR_MODE = "mode"


def decode_firmware_version(value: int | None) -> str | None:
    """Decode the integer firmware version (0x02080F -> "2.8.15")."""
    if value is None:
        return None
    return f"{(value >> 16) & 0xFF}.{(value >> 8) & 0xFF}.{value & 0xFF}"
