# Nuki Web Home Assistant Integration

This is a custom integration for Home Assistant that interacts with the Nuki Web API. It allows you to view and control your Nuki Smart Locks and Openers directly from Home Assistant.

> [!IMPORTANT]
> This integration is not affiliated with or endorsed by Nuki.
> It is a completely independent project, backed up by the community, and based on official documentation and APIs.

> [!NOTE]
> **Disclaimer:** this project has been generated mainly by AI. Even though it has been reviewed and tested by a professional programmer, I feel like it's important to disclose this fact.

## Features

*   **Platform Support**:
    *   **Lock**: Lock, Unlock, and Open (Unlatch) your Nuki devices, plus a `nuki_web.perform_action` service with *force* and *full lock* options.
    *   **Sensor**: Battery level, door state, mode, last action and trigger, firmware/hardware version, admin PIN state, Ring to Open end time (Openers) and last activity.
    *   **Binary Sensor**: Battery critical (lock, keypad, door sensor), battery charging, door open/closed, keypad tamper, night mode, Nuki server connection and Ring to Open status (Openers).
    *   **Switch**: Ring to Open and Continuous mode (Openers), plus settings such as auto lock, auto firmware update, button, LED and pairing.
    *   **Number / Select**: Auto lock timeout, LED brightness, lock 'n' go timeout, unlatch duration, motor speed, advertising mode, button actions, buzzer volume and Opener sounds and Ring to Open timeout.
    *   **Button**: Sync, Lock 'n' go and Lock 'n' go with unlatch.
    *   **Event**: Activity log events (lock, unlock, door opened/closed, door ajar, doorbell, failed actions, ...).
*   **Config Flow**: Easy setup via the Home Assistant UI using your Nuki Web API Token.
*   **Polling**: Automatically updates device status every 30 seconds.

## Installation

### Via HACS (Recommended)

1.  Ensure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance.
2.  Add this repository as a custom repository in HACS.
    *   Go to **HACS > Integrations**.
    *   Click the **3 dots** in the top right corner and select **Custom repositories**.
    *   Enter the URL of this repository.
    *   Select **Integration** as the Category.
    *   Click **Add**.
3.  Search for "Nuki Web" in HACS and install it.
4.  Restart Home Assistant.

### Manual Installation

1.  Download the `custom_components/nuki_web` folder from this repository.
2.  Copy the `nuki_web` folder into your Home Assistant's `custom_components` directory.
3.  Restart Home Assistant.

## Configuration

1.  Go to **Settings > Devices & Services**.
2.  Click **+ ADD INTEGRATION**.
3.  Search for "Nuki Web".
4.  Enter your **Nuki Web API Token**.
    *   You can generate a token at [Nuki Web API](https://developer.nuki.io/). Make sure to enable the permissions listed in [Required API token scopes](#required-api-token-scopes).

### Required API token scopes

The token only needs the scopes for the features you want to use. Without a scope, the matching feature will not work. The integration does not use OAuth or the Advanced API.

| Scope | Needed for | Required |
|---|---|---|
| `smartlock.readonly` (or `smartlock`) | Listing your devices and reading their state, battery and settings | **Yes** |
| `smartlock.action` | Lock, unlock, open, lock 'n' go, Ring to Open, Continuous mode, the `perform_action` service and the Sync button | For control |
| `smartlock.config` | Changing settings (switches, numbers and selects in the *Configuration* category) | For settings |
| `smartlock.log` | Activity events and the *Last activity* sensor | For activity |

If the token cannot read the activity log, a warning is logged and the activity entities are not created. Everything else keeps working.

## attributes

The integration exposes several attributes on the entities, such as:
-   **Battery Level**: Percentage of battery remaining.
-   **Firmware Version**: The current firmware version of the lock.

## Troubleshooting

Enable debug logging for more information:

```yaml
logger:
  default: warning
  logs:
    custom_components.nuki_web: debug
```
