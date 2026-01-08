# Nuki Web Home Assistant Integration

This is a custom integration for Home Assistant that interacts with the Nuki Web API. It allows you to view and control your Nuki Smart Locks and Openers directly from Home Assistant.

> [!IMPORTANT]
> This integration is not affiliated with or endorsed by Nuki.
> It is a completely independent project, backed up by the community, and based on official documentation and APIs.

> [!NOTE]
> **Disclaimer:** this project has been generated mainly by AI. Even though it has been reviewed and tested by a professional programmer, I feel like it's important to disclose this fact.

## Features

*   **Platform Support**:
    *   **Lock**: Lock, Unlock, and Open (Unlatch) your specific Nuki devices.
    *   **Sensor**: Battery level monitoring.
    *   **Binary Sensor**: Critical battery warnings, Door state (Open/Closed), and Ring to Open status (for Openers).
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
    *   You can generate a token at [Nuki Web API](https://developer.nuki.io/). Make sure to enable the necessary permissions (Smartlock view/action, etc.).

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
