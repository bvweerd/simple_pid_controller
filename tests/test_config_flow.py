import pytest

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.simple_pid_controller.const import (
    DOMAIN,
    CONF_NAME,
    CONF_SENSOR_ENTITY_ID,
    CONF_RANGE_MIN,
    CONF_RANGE_MAX,
)
from custom_components.simple_pid_controller.config_flow import (
    PIDControllerFlowHandler,
    PIDControllerOptionsFlowHandler,
)

SENSOR_ENTITY = "sensor.test_input"


@pytest.mark.parametrize(
    "user_input, expected_type, expected_data, expected_errors",
    [
        # Happy path without specifying ranges
        (
            {CONF_NAME: "My PID", CONF_SENSOR_ENTITY_ID: SENSOR_ENTITY},
            FlowResultType.CREATE_ENTRY,
            {CONF_NAME: "My PID", CONF_SENSOR_ENTITY_ID: SENSOR_ENTITY},
            None,
        ),
        # Happy path specifying explicit valid ranges (ignored in create)
        (
            {
                CONF_NAME: "My PID 2",
                CONF_SENSOR_ENTITY_ID: SENSOR_ENTITY,
                CONF_RANGE_MIN: 1.0,
                CONF_RANGE_MAX: 10.0,
            },
            FlowResultType.CREATE_ENTRY,
            {CONF_NAME: "My PID 2", CONF_SENSOR_ENTITY_ID: SENSOR_ENTITY},
            None,
        ),
        # Invalid ranges (min >= max)
        (
            {
                CONF_NAME: "Bad PID",
                CONF_SENSOR_ENTITY_ID: SENSOR_ENTITY,
                CONF_RANGE_MIN: 10.0,
                CONF_RANGE_MAX: 5.0,
            },
            FlowResultType.FORM,
            None,
            {"base": "range_min_max"},
        ),
    ],
)
async def test_async_step_user(
    hass, user_input, expected_type, expected_data, expected_errors
):
    """Test the user step: happy paths and validation errors."""
    # Start the user flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    # Submit the form
    flow_id = result["flow_id"]
    result2 = await hass.config_entries.flow.async_configure(
        flow_id, user_input=user_input
    )

    # Verify outcome
    assert result2["type"] == expected_type
    if expected_type == FlowResultType.CREATE_ENTRY:
        assert result2["title"] == user_input[CONF_NAME]
        assert result2["data"] == expected_data
    else:
        assert result2.get("errors") == expected_errors


def test_async_get_options_flow():
    """Test that async_get_options_flow returns the correct handler."""
    handler = PIDControllerFlowHandler()
    options_flow = handler.async_get_options_flow(config_entry=None)
    assert isinstance(options_flow, PIDControllerOptionsFlowHandler)


@pytest.mark.parametrize(
    "new_options, expected_errors",
    [
        # Valid options update
        (
            {
                CONF_SENSOR_ENTITY_ID: "sensor.new",
                CONF_RANGE_MIN: 1.0,
                CONF_RANGE_MAX: 10.0,
            },
            None,
        ),
        # Invalid options ranges
        (
            {
                CONF_SENSOR_ENTITY_ID: "sensor.new",
                CONF_RANGE_MIN: 10.0,
                CONF_RANGE_MAX: 5.0,
            },
            {"base": "range_min_max"},
        ),
    ],
)
async def test_options_flow(hass, config_entry, new_options, expected_errors):
    """Test the options flow: happy and error scenarios."""
    # Initialize options flow
    init_result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert init_result["type"] == FlowResultType.FORM
    assert init_result["step_id"] == "init"

    # Submit options
    result2 = await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input=new_options
    )

    if expected_errors:
        assert result2["type"] == FlowResultType.FORM
        assert result2.get("errors") == expected_errors
    else:
        assert result2["type"] == FlowResultType.CREATE_ENTRY
        assert result2.get("data") == new_options


async def test_user_flow_duplicate_abort(hass):
    """Test that a duplicate config entry aborts the flow."""
    user_input = {CONF_NAME: "Duplicate PID", CONF_SENSOR_ENTITY_ID: SENSOR_ENTITY}

    # Create initial entry
    init_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await hass.config_entries.flow.async_configure(
        init_result["flow_id"], user_input=user_input
    )

    # Attempt duplicate
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=user_input
    )

    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "already_configured"
