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

from .const import (
    DOMAIN,
    CONF_NAME,
    DEFAULT_NAME,
    CONF_SENSOR_ENTITY_ID,
    CONF_RANGE_MIN,
    CONF_RANGE_MAX,
    DEFAULT_RANGE_MIN,
    DEFAULT_RANGE_MAX,
)

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
        return PIDControllerOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_SENSOR_ENTITY_ID): selector(
                    {"entity": {"domain": "sensor"}}
                ),
                vol.Optional(CONF_RANGE_MIN, default=DEFAULT_RANGE_MIN): vol.Coerce(
                    float
                ),
                vol.Optional(CONF_RANGE_MAX, default=DEFAULT_RANGE_MAX): vol.Coerce(
                    float
                ),
            }
        )

        if user_input is not None:
            self._async_abort_entries_match({CONF_NAME: user_input[CONF_NAME]})

            # Validate that range_min < range_max
            min_val = user_input.get(CONF_RANGE_MIN)
            max_val = user_input.get(CONF_RANGE_MAX)
            if min_val is not None and max_val is not None and min_val >= max_val:
                return self.async_show_form(
                    step_id="user", data_schema=schema, errors={"base": "range_min_max"}
                )

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_SENSOR_ENTITY_ID: user_input[CONF_SENSOR_ENTITY_ID],
                },
            )

        return self.async_show_form(step_id="user", data_schema=schema)


class PIDControllerOptionsFlowHandler(OptionsFlow):
    """Handle options for PID Controller."""

    def __init__(self) -> None:
        """Initialize options flow."""
        super().__init__()

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options form and save user input."""

        # Pre-fill form with existing options or sensible defaults
        current_sensor = self.config_entry.options.get(
            CONF_SENSOR_ENTITY_ID
        ) or self.config_entry.data.get(CONF_SENSOR_ENTITY_ID)
        current_min = self.config_entry.options.get(CONF_RANGE_MIN, DEFAULT_RANGE_MIN)
        current_max = self.config_entry.options.get(CONF_RANGE_MAX, DEFAULT_RANGE_MAX)

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_SENSOR_ENTITY_ID,
                    default=current_sensor,
                ): selector({"entity": {"domain": "sensor"}}),
                vol.Required(
                    CONF_RANGE_MIN,
                    default=current_min,
                ): vol.Coerce(float),
                vol.Required(
                    CONF_RANGE_MAX,
                    default=current_max,
                ): vol.Coerce(float),
            }
        )

        # If the user has submitted the form, create the entry
        if user_input is not None:
            # Validate that range_min < range_max
            min_val = user_input.get(CONF_RANGE_MIN)
            max_val = user_input.get(CONF_RANGE_MAX)
            if min_val is not None and max_val is not None and min_val >= max_val:
                return self.async_show_form(
                    step_id="init",
                    data_schema=options_schema,
                    errors={"base": "range_min_max"},
                )

            return self.async_create_entry(
                title=self.config_entry.title,
                data=user_input,
            )

        return self.async_show_form(step_id="init", data_schema=options_schema)
