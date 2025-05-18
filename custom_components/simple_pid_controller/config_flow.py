"""Config flow for the PID Controller integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import selector

from .const import DOMAIN, CONF_NAME, DEFAULT_NAME, CONF_SENSOR_ENTITY_ID

_LOGGER = logging.getLogger(__name__)


class PIDControllerFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PID Controller."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> PIDControllerOptionsFlowHandler:
        """Get the options flow for this handler."""
        return PIDControllerOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_SENSOR_ENTITY_ID: user_input[CONF_SENSOR_ENTITY_ID],
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME, default=DEFAULT_NAME
                    ): str,
                    vol.Required(CONF_SENSOR_ENTITY_ID): selector(
                        {"entity": {"domain": "sensor"}}
                    ),
                }
            ),
        )


class PIDControllerOptionsFlowHandler(OptionsFlow):
    """Handle options for PID Controller."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_sensor = self.config_entry.options.get(
            CONF_SENSOR_ENTITY_ID,
            self.config_entry.data.get(CONF_SENSOR_ENTITY_ID, ""),
        )

        options_schema = vol.Schema(
            {
                vol.Required(CONF_SENSOR_ENTITY_ID, default=current_sensor): selector(
                    {"entity": {"domain": "sensor"}}
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)
