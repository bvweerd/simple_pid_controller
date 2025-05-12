import pytest
from homeassistant import data_entry_flow

from custom_components.simple_pid_controller.options_flow import (
    SimplePIDOptionsFlowHandler,
)
from custom_components.simple_pid_controller.const import CONF_SENSOR_ENTITY_ID


@pytest.mark.asyncio
async def test_update_existing_option(hass, config_entry):
    """
    Test that submitting a new sensor option updates the config_entry.options correctly.
    """
    # Pre-set an initial option
    config_entry.options = {CONF_SENSOR_ENTITY_ID: "sensor.old_value"}

    flow = SimplePIDOptionsFlowHandler(config_entry)

    user_input = {CONF_SENSOR_ENTITY_ID: "sensor.new_value"}
    result = await flow.async_step_init(user_input)

    # Flow should create entry with new data
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["data"][CONF_SENSOR_ENTITY_ID] == "sensor.new_value"

    # Apply the new options to the config entry and allow HA to process it
    hass.config_entries.async_update_entry(config_entry, options=result["data"])
    await hass.async_block_till_done()

    # Ensure the config_entry options were updated
    assert config_entry.options[CONF_SENSOR_ENTITY_ID] == "sensor.new_value"


@pytest.mark.asyncio
async def test_init_form_default_to_data_when_no_option(hass, config_entry):
    """
    Test that the init step default value comes from config_entry.data when no options are set.
    """
    # Pre-set data with a default sensor, and clear options
    config_entry.data = {CONF_SENSOR_ENTITY_ID: "sensor.data_value"}
    config_entry.options = {}

    flow = SimplePIDOptionsFlowHandler(config_entry)
    result = await flow.async_step_init()

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    # Apply the schema with no user input to get defaults
    schema = result["data_schema"]
    validated = schema({})
    assert validated[CONF_SENSOR_ENTITY_ID] == "sensor.data_value"


@pytest.mark.asyncio
async def test_init_form_default_to_option_when_option_set(hass, config_entry):
    """
    Test that the init step default value comes from config_entry.options when an option is set.
    """
    # Pre-set an option and clear data
    config_entry.options = {CONF_SENSOR_ENTITY_ID: "sensor.option_value"}
    config_entry.data = {}

    flow = SimplePIDOptionsFlowHandler(config_entry)
    result = await flow.async_step_init()

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    # Apply the schema with no user input to get defaults
    schema = result["data_schema"]
    validated = schema({})
    assert validated[CONF_SENSOR_ENTITY_ID] == "sensor.option_value"
