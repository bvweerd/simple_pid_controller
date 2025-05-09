from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.selector import selector
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import DOMAIN, CONF_SENSOR_ENTITY_ID


STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_SENSOR_ENTITY_ID): selector({"entity": {"domain": "sensor"}}),
})


@config_entries.HANDLERS.register(DOMAIN)
class SimplePIDConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Simple PID Controller."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_SENSOR_ENTITY_ID: user_input[CONF_SENSOR_ENTITY_ID],
                },
            )
        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        from .options_flow import SimplePIDOptionsFlowHandler
        return SimplePIDOptionsFlowHandler(config_entry)
