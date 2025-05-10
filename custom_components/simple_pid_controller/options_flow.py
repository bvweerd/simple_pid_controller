from homeassistant import config_entries
from homeassistant.helpers.selector import selector
import voluptuous as vol

from .const import CONF_SENSOR_ENTITY_ID


class AdvancedPIDOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a config flow for updating PID options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_sensor = self.config_entry.options.get(
            CONF_SENSOR_ENTITY_ID, self.config_entry.data.get(CONF_SENSOR_ENTITY_ID, "")
        )

        options_schema = vol.Schema(
            {
                vol.Required(CONF_SENSOR_ENTITY_ID, default=current_sensor): selector(
                    {"entity": {"domain": "sensor"}}
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)
