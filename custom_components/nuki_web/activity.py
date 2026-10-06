"""Helpers to interpret Nuki activity log entries."""
from __future__ import annotations

from typing import Any

SIGNAL_LOG = "nuki_web_log_{}"

LOCK_ACTIONS = {1, 2, 3, 4, 5}

# Log action -> event type
EVENT_TYPES_BY_ACTION = {
    1: "unlock",
    2: "lock",
    3: "unlatch",
    4: "lock_n_go",
    5: "lock_n_go_unlatch",
    208: "door_ajar",
    224: "doorbell",
    240: "door_opened",
    241: "door_closed",
    242: "door_sensor_jammed",
    243: "firmware_update",
    253: "calibration",
}
# Reported when a lock action did not complete successfully
EVENT_TYPE_ACTION_FAILED = "action_failed"
EVENT_TYPES = [*EVENT_TYPES_BY_ACTION.values(), EVENT_TYPE_ACTION_FAILED]

RESULTS = {
    0: "success",
    1: "motor_blocked",
    2: "canceled",
    3: "too_recent",
    4: "busy",
    5: "low_motor_voltage",
    6: "clutch_failure",
    7: "motor_power_failure",
    8: "incomplete",
    9: "rejected",
    10: "rejected_night_mode",
    224: "invalid_code",
    225: "invalid_fingerprint",
    226: "invalid_nfc_tag",
    254: "other_error",
    255: "unknown_error",
}
TRIGGERS = {
    0: "system",
    1: "manual",
    2: "button",
    3: "automatic",
    4: "web",
    5: "app",
    6: "auto_lock",
    7: "accessory",
    253: "keypad_error",
    254: "nuki_mode",
    255: "keypad",
}
SOURCES = {0: "default", 1: "keypad_code", 2: "fingerprint", 3: "tap_to_unlock"}


def log_event_type(log: dict[str, Any]) -> str | None:
    """Return the event type of a log entry, or None if it is not an event."""
    action = log.get("action")
    event_type = EVENT_TYPES_BY_ACTION.get(action)
    if event_type is None:
        return None
    if action in LOCK_ACTIONS and log.get("state", 0) != 0:
        return EVENT_TYPE_ACTION_FAILED
    return event_type


def log_attributes(log: dict[str, Any]) -> dict[str, Any]:
    """Return the attributes describing a log entry."""
    attributes: dict[str, Any] = {
        "action": EVENT_TYPES_BY_ACTION.get(log.get("action")),
        "name": log.get("name"),
        "trigger": TRIGGERS.get(log.get("trigger")),
        "source": SOURCES.get(log.get("source")),
        "result": RESULTS.get(log.get("state"), "unknown_error"),
        "auto_unlock": log.get("autoUnlock"),
        "date": log.get("date"),
    }
    return {key: value for key, value in attributes.items() if value is not None}
