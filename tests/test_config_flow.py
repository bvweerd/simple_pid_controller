import pytest

from homeassistant import config_entries
from custom_components.simple_pid_controller.const import DOMAIN, CONF_SENSOR_ENTITY_ID, CONF_NAME

@pytest.mark.parametrize("source,step_id", [
    (config_entries.SOURCE_USER, "user"),
])
async def test_show_form(hass, source, step_id):
    """When starting de flow, krijg je een form terug."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": source}
    )
    assert result["type"] == "form"
    assert result["step_id"] == step_id

async def test_create_entry(hass):
    """Na invullen van de form wordt er een ConfigEntry aangemaakt."""
    init = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        init["flow_id"],
        user_input={CONF_NAME: "My PID", CONF_SENSOR_ENTITY_ID: "sensor.test"},
    )
    assert result2["type"] == "create_entry"
    assert result2["title"] == "My PID"
    assert result2["data"][CONF_SENSOR_ENTITY_ID] == "sensor.test"
