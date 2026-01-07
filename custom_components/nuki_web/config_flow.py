"""Config flow for Nuki Web integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_TOKEN
from homeassistant.helpers import aiohttp_client

from .const import DOMAIN
from .api import NukiWebApi

_LOGGER = logging.getLogger(__name__)

class NukiWebConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nuki Web."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            token = user_input[CONF_API_TOKEN]
            session = aiohttp_client.async_get_clientsession(self.hass)
            api = NukiWebApi(token, session)

            if await api.validate_token():
                return self.async_create_entry(title="Nuki Web", data=user_input)
            else:
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_API_TOKEN): str}),
            errors=errors,
        )
