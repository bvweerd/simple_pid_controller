import pytest

import pytest

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType, InvalidData

from custom_components.simple_pid_controller.const import (
    CONF_STEP_PREFIX,
    DOMAIN,
    CONF_NAME,
    CONF_SENSOR_ENTITY_ID,
    CONF_INPUT_RANGE_MIN,
    CONF_INPUT_RANGE_MAX,
    CONF_OUTPUT_RANGE_MIN,
    CONF_OUTPUT_RANGE_MAX,
    DEFAULT_INPUT_RANGE_MIN,
    DEFAULT_INPUT_RANGE_MAX,
    DEFAULT_OUTPUT_RANGE_MIN,
    DEFAULT_OUTPUT_RANGE_MAX,
    DEFAULT_STEPS,
)
from custom_components.simple_pid_controller.config_flow import (
    PIDControllerFlowHandler,
    PIDControllerOptionsFlowHandler,
)

SENSOR_ENTITY = "sensor.test_input"


@pytest.mark.parametrize(
    "user_input, expected_type, expected_data, expected_errors",
    [
        # Happy path without specifying ranges (defaults applied)
        (
            {
                CONF_NAME: "My PID",
                CONF_SENSOR_ENTITY_ID: SENSOR_ENTITY,
                CONF_INPUT_RANGE_MIN: DEFAULT_INPUT_RANGE_MIN,
                CONF_INPUT_RANGE_MAX: DEFAULT_INPUT_RANGE_MAX,
                CONF_OUTPUT_RANGE_MIN: DEFAULT_OUTPUT_RANGE_MIN,
                CONF_OUTPUT_RANGE_MAX: DEFAULT_OUTPUT_RANGE_MAX,
            },
            FlowResultType.CREATE_ENTRY,
            {
                CONF_NAME: "My PID",
                CONF_SENSOR_ENTITY_ID: SENSOR_ENTITY,
                CONF_INPUT_RANGE_MIN: DEFAULT_INPUT_RANGE_MIN,
                CONF_INPUT_RANGE_MAX: DEFAULT_INPUT_RANGE_MAX,
                CONF_OUTPUT_RANGE_MIN: DEFAULT_OUTPUT_RANGE_MIN,
                CONF_OUTPUT_RANGE_MAX: DEFAULT_OUTPUT_RANGE_MAX,
            },
            None,
        ),
        # Happy path specifying explicit valid ranges
        (
            {
                CONF_NAME: "My PID 2",
                CONF_SENSOR_ENTITY_ID: SENSOR_ENTITY,
                CONF_INPUT_RANGE_MIN: 1.0,
                CONF_INPUT_RANGE_MAX: 10.0,
                CONF_OUTPUT_RANGE_MIN: 1.0,
                CONF_OUTPUT_RANGE_MAX: 10.0,
            },
            FlowResultType.CREATE_ENTRY,
            {
                CONF_NAME: "My PID 2",
                CONF_SENSOR_ENTITY_ID: SENSOR_ENTITY,
                CONF_INPUT_RANGE_MIN: 1.0,
                CONF_INPUT_RANGE_MAX: 10.0,
                CONF_OUTPUT_RANGE_MIN: 1.0,
                CONF_OUTPUT_RANGE_MAX: 10.0,
            },
            None,
        ),
        # Invalid ranges (min >= max)
        (
            {
                CONF_NAME: "Bad PID",
                CONF_SENSOR_ENTITY_ID: SENSOR_ENTITY,
                CONF_INPUT_RANGE_MIN: 10.0,
                CONF_INPUT_RANGE_MAX: 5.0,
                CONF_OUTPUT_RANGE_MIN: 1.0,
                CONF_OUTPUT_RANGE_MAX: 10.0,
            },
            FlowResultType.FORM,
            None,
            {"base": "input_range_min_max"},
        ),
        # Invalid ranges (min >= max)
        (
            {
                CONF_NAME: "Bad PID",
                CONF_SENSOR_ENTITY_ID: SENSOR_ENTITY,
                CONF_INPUT_RANGE_MIN: 1.0,
                CONF_INPUT_RANGE_MAX: 10.0,
                CONF_OUTPUT_RANGE_MIN: 10.0,
                CONF_OUTPUT_RANGE_MAX: 5.0,
            },
            FlowResultType.FORM,
            None,
            {"base": "output_range_min_max"},
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
        (
            {
                CONF_SENSOR_ENTITY_ID: "sensor.new",
                CONF_INPUT_RANGE_MIN: 1.0,
                CONF_INPUT_RANGE_MAX: 10.0,
                CONF_OUTPUT_RANGE_MIN: 1.0,
                CONF_OUTPUT_RANGE_MAX: 10.0,
            },
            None,
        ),
        (
            {
                CONF_SENSOR_ENTITY_ID: "sensor.new",
                CONF_INPUT_RANGE_MIN: 10.0,
                CONF_INPUT_RANGE_MAX: 5.0,
                CONF_OUTPUT_RANGE_MIN: 1.0,
                CONF_OUTPUT_RANGE_MAX: 10.0,
            },
            {"base": "input_range_min_max"},
        ),
        (
            {
                CONF_SENSOR_ENTITY_ID: "sensor.new",
                CONF_INPUT_RANGE_MIN: 1.0,
                CONF_INPUT_RANGE_MAX: 10.0,
                CONF_OUTPUT_RANGE_MIN: 10.0,
                CONF_OUTPUT_RANGE_MAX: 5.0,
            },
            {"base": "output_range_min_max"},
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
        # Step defaults are added by voluptuous; check submitted fields are present
        assert new_options.items() <= result2.get("data", {}).items()


async def test_options_flow_with_custom_steps(hass, config_entry):
    """Test that step options round-trip correctly through the options flow."""
    custom_steps = {f"{CONF_STEP_PREFIX}{key}": 0.5 for key in DEFAULT_STEPS}
    new_options = {
        CONF_SENSOR_ENTITY_ID: "sensor.new",
        CONF_INPUT_RANGE_MIN: 1.0,
        CONF_INPUT_RANGE_MAX: 10.0,
        CONF_OUTPUT_RANGE_MIN: 1.0,
        CONF_OUTPUT_RANGE_MAX: 10.0,
        **custom_steps,
    }

    init_result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result2 = await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input=new_options
    )

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    for key, val in custom_steps.items():
        assert result2["data"][key] == val


_BASE_OPTIONS = {
    CONF_SENSOR_ENTITY_ID: "sensor.new",
    CONF_INPUT_RANGE_MIN: 1.0,
    CONF_INPUT_RANGE_MAX: 10.0,
    CONF_OUTPUT_RANGE_MIN: 1.0,
    CONF_OUTPUT_RANGE_MAX: 10.0,
}


@pytest.mark.usefixtures("setup_integration")
@pytest.mark.parametrize("invalid_step", [0.0, -1.0, -0.0001])
async def test_options_flow_step_below_min_rejected(hass, config_entry, invalid_step):
    """Test that a step value below the selector minimum raises InvalidData."""
    init_result = await hass.config_entries.options.async_init(config_entry.entry_id)
    with pytest.raises(InvalidData):
        await hass.config_entries.options.async_configure(
            init_result["flow_id"],
            user_input={**_BASE_OPTIONS, f"{CONF_STEP_PREFIX}kp": invalid_step},
        )


@pytest.mark.usefixtures("setup_integration")
@pytest.mark.parametrize("invalid_step", [100.001, 200.0, 1000.0])
async def test_options_flow_step_above_max_rejected(hass, config_entry, invalid_step):
    """Test that a step value above the selector maximum raises InvalidData."""
    init_result = await hass.config_entries.options.async_init(config_entry.entry_id)
    with pytest.raises(InvalidData):
        await hass.config_entries.options.async_configure(
            init_result["flow_id"],
            user_input={**_BASE_OPTIONS, f"{CONF_STEP_PREFIX}setpoint": invalid_step},
        )


@pytest.mark.usefixtures("setup_integration")
@pytest.mark.parametrize(
    "boundary_step", [0.0001, 100.0]
)
async def test_options_flow_step_boundary_values_accepted(hass, config_entry, boundary_step):
    """Test that step values at the exact selector boundaries are accepted."""
    init_result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        init_result["flow_id"],
        user_input={**_BASE_OPTIONS, f"{CONF_STEP_PREFIX}kp": boundary_step},
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][f"{CONF_STEP_PREFIX}kp"] == boundary_step


async def test_user_flow_duplicate_abort(hass):
    """Test that a duplicate config entry aborts the flow."""
    user_input = {
        CONF_NAME: "Duplicate PID",
        CONF_SENSOR_ENTITY_ID: SENSOR_ENTITY,
        CONF_INPUT_RANGE_MIN: DEFAULT_INPUT_RANGE_MIN,
        CONF_INPUT_RANGE_MAX: DEFAULT_INPUT_RANGE_MAX,
        CONF_OUTPUT_RANGE_MIN: DEFAULT_OUTPUT_RANGE_MIN,
        CONF_OUTPUT_RANGE_MAX: DEFAULT_OUTPUT_RANGE_MAX,
    }

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


