
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import DOMAIN, CONF_SENSOR_ENTITY_ID

class SimplePIDOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = (
            self.config_entry.options.get(CONF_SENSOR_ENTITY_ID)
            or self.config_entry.data.get(CONF_SENSOR_ENTITY_ID)
            or ""
        )
        schema = vol.Schema({
            vol.Required(CONF_SENSOR_ENTITY_ID, default=current): cv.entity_id
        })
        return self.async_show_form(step_id="init", data_schema=schema)
