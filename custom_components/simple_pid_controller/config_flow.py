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
    CONF_INPUT_RANGE_MIN,
    CONF_INPUT_RANGE_MAX,
    CONF_OUTPUT_RANGE_MIN,
    CONF_OUTPUT_RANGE_MAX,
    DEFAULT_INPUT_RANGE_MIN,
    DEFAULT_INPUT_RANGE_MAX,
    DEFAULT_OUTPUT_RANGE_MIN,
    DEFAULT_OUTPUT_RANGE_MAX,
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
                vol.Optional(CONF_INPUT_RANGE_MIN, default=DEFAULT_INPUT_RANGE_MIN): vol.Coerce(
                    float
                ),
                vol.Optional(CONF_INPUT_RANGE_MAX, default=DEFAULT_INPUT_RANGE_MAX): vol.Coerce(
                    float
                ),
                vol.Optional(CONF_OUTPUT_RANGE_MIN, default=DEFAULT_OUTPUT_RANGE_MIN): vol.Coerce(
                    float
                ),
                vol.Optional(CONF_OUTPUT_RANGE_MAX, default=DEFAULT_OUTPUT_RANGE_MAX): vol.Coerce(
                    float
                ),
            }
        )

        if user_input is not None:
            self._async_abort_entries_match({CONF_NAME: user_input[CONF_NAME]})

            # Validate that range_min < range_max
            input_min_val = user_input.get(CONF_INPUT_RANGE_MIN)
            input_max_val = user_input.get(CONF_INPUT_RANGE_MAX)
            if input_min_val is not None and input_max_val is not None and input_min_val >= input_max_val:
                return self.async_show_form(
                    step_id="user", data_schema=schema, errors={"base": "input_range_min_max"}
                )
            output_min_val = user_input.get(CONF_OUTPUT_RANGE_MIN)
            output_max_val = user_input.get(CONF_OUTPUT_RANGE_MAX)
            if output_min_val is not None and output_max_val is not None and output_min_val >= output_max_val:
                return self.async_show_form(
                    step_id="user", data_schema=schema, errors={"base": "output_range_min_max"}
                )
                
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_SENSOR_ENTITY_ID: user_input[CONF_SENSOR_ENTITY_ID],
                    CONF_INPUT_RANGE_MIN: user_input[CONF_INPUT_RANGE_MIN],
                    CONF_INPUT_RANGE_MAX: user_input[CONF_INPUT_RANGE_MAX],
                    CONF_OUTPUT_RANGE_MIN: user_input[CONF_OUTPUT_RANGE_MIN],
                    CONF_OUTPUT_RANGE_MAX: user_input[CONF_OUTPUT_RANGE_MAX],
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
        current_input_min = self.config_entry.options.get(CONF_INPUT_RANGE_MIN, DEFAULT_INPUT_RANGE_MIN)
        current_input_max = self.config_entry.options.get(CONF_INPUT_RANGE_MAX, DEFAULT_INPUT_RANGE_MAX)

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_SENSOR_ENTITY_ID,
                    default=current_sensor,
                ): selector({"entity": {"domain": "sensor"}}),
                vol.Required(
                    CONF_INPUT_RANGE_MIN,
                    default=current_input_min,
                ): vol.Coerce(float),
                vol.Required(
                    CONF_INPUT_RANGE_MAX,
                    default=current_input_max,
                ): vol.Coerce(float),
                vol.Required(
                    CONF_OUTPUT_RANGE_MIN,
                    default=current_output_min,
                ): vol.Coerce(float),
                vol.Required(
                    CONF_OUTPUT_RANGE_MAX,
                    default=current_output_max,
                ): vol.Coerce(float),
            }
        )

        # If the user has submitted the form, create the entry
        if user_input is not None:
            # Validate that range_min < range_max
            input_min_val = user_input.get(CONF_INPUT_RANGE_MIN)
            input_max_val = user_input.get(CONF_INPUT_RANGE_MAX)
            if input_min_val is not None and input_max_val is not None and input_min_val >= input_max_val:
                return self.async_show_form(
                    step_id="user", data_schema=schema, errors={"base": "input_range_min_max"}
                )
            output_min_val = user_input.get(CONF_OUTPUT_RANGE_MIN)
            output_max_val = user_input.get(CONF_OUTPUT_RANGE_MAX)
            if output_min_val is not None and output_max_val is not None and output_min_val >= output_max_val:
                return self.async_show_form(
                    step_id="user", data_schema=schema, errors={"base": "output_range_min_max"}
                )

            return self.async_create_entry(
                title=self.config_entry.title,
                data=user_input,
            )

        return self.async_show_form(step_id="init", data_schema=options_schema)
