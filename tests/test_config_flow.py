import pytest
from homeassistant import config_entries
from custom_components.simple_pid_controller.config_flow import SimplePIDConfigFlow
from custom_components.simple_pid_controller.const import DOMAIN, CONF_NAME, CONF_SENSOR_ENTITY_ID

@pytest.mark.asyncio
async def test_config_flow_form(hass):
    flow = SimplePIDConfigFlow()
    result = await flow.async_step_user({})
    assert result["type"] == "form"
    user_input = {CONF_NAME: "Test PID", CONF_SENSOR_ENTITY_ID: "sensor.test_input"}
    result2 = await flow.async_step_user(user_input)
    assert result2["type"] == "create_entry"
    assert result2["data"][CONF_NAME] == "Test PID"
    assert result2["data"][CONF_SENSOR_ENTITY_ID] == "sensor.test_input"
