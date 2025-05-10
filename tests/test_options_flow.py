"""Test the options flow for Simple PID Controller."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.simple_pid_controller.options_flow import (
    AdvancedPIDOptionsFlowHandler,
)
from custom_components.simple_pid_controller.const import DOMAIN, CONF_SENSOR_ENTITY_ID


@pytest.fixture
def config_entry(hass: HomeAssistant):
    """Create a mock config entry for options flow."""
    entry = ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Test PID",
        data={CONF_SENSOR_ENTITY_ID: "sensor.initial"},
        options={},
        entry_id="test_entry",
    )
    return entry


async def test_show_options_form(hass: HomeAssistant, config_entry):
    """Test that the options flow form is served."""
    handler = AdvancedPIDOptionsFlowHandler(config_entry)
    result = await handler.async_step_init()
    assert result["type"] == "form"
    assert CONF_SENSOR_ENTITY_ID in result["data_schema"].schema


async def test_options_create_entry(hass: HomeAssistant, config_entry):
    """Test creating an options entry."""
    handler = AdvancedPIDOptionsFlowHandler(config_entry)
    new_data = {CONF_SENSOR_ENTITY_ID: "sensor.new"}
    result = await handler.async_step_init(user_input=new_data)
    assert result["type"] == "create_entry"
    assert result["data"] == new_data
