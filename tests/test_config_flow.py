"""Test the config flow for Simple PID Controller."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.simple_pid_controller.const import (
    DOMAIN,
    CONF_NAME,
    CONF_SENSOR_ENTITY_ID,
)


async def test_show_form(hass: HomeAssistant):
    """Test that the config flow form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_create_entry(hass: HomeAssistant):
    """Test creating an entry."""
    data = {
        CONF_NAME: "Test PID",
        CONF_SENSOR_ENTITY_ID: "sensor.test",
    }
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=data,
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == data[CONF_NAME]
    assert result["data"] == data
