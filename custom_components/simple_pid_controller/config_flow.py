"""Config flow for the PID Controller integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import selector

from .const import DOMAIN, CONF_NAME, CONF_SENSOR_ENTITY_ID

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): str,
        vol.Required(CONF_SENSOR_ENTITY_ID): selector({"entity": {"domain": "sensor"}}),
    }
)


class AdvancedPIDControllerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Advanced PID Controller."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return None
