import pytest

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.simple_pid_controller.const import (
    DOMAIN,
    CONF_SENSOR_ENTITY_ID,
    CONF_NAME,
    CONF_RANGE_MIN,
    CONF_RANGE_MAX,
)


@pytest.mark.parametrize(
    "source,step_id",
    [
        (config_entries.SOURCE_USER, "user"),
    ],
)
async def test_show_form(hass, source, step_id):
    """When starting the flow, you get a form back."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": source}
    )
    assert result["type"] == "form"
    assert result["step_id"] == step_id


async def test_create_entry(hass):
    """After filling out the form, a ConfigEntry is created."""
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


async def test_options_flow(hass, config_entry):
    """After submitting the OptionsFlow, entry.options is updated."""
    # 1) Start de options flow via de dedicated helper
    init_result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert init_result["type"] == FlowResultType.FORM
    assert init_result["step_id"] == "init"

    # 2) Dien nieuwe opties in
    new_options = {
        CONF_SENSOR_ENTITY_ID: "sensor.new",
        CONF_RANGE_MIN: 1.0,
        CONF_RANGE_MAX: 10.0,
    }
    finish_result = await hass.config_entries.options.async_configure(
        init_result["flow_id"],
        user_input=new_options,
    )

    # 3) Verifieer dat de flow CREATE_ENTRY teruggeeft en options zijn bijgewerkt
    assert finish_result["type"] == FlowResultType.CREATE_ENTRY
    assert config_entry.options[CONF_SENSOR_ENTITY_ID] == "sensor.new"
    assert config_entry.options[CONF_RANGE_MIN] == 1.0
    assert config_entry.options[CONF_RANGE_MAX] == 10.0
