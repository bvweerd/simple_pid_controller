import pytest
import voluptuous as vol

from custom_components.simple_pid_controller import DOMAIN, SERVICE_SET_OUTPUT


@pytest.mark.usefixtures("setup_integration")
@pytest.mark.asyncio
async def test_set_output_start_mode(hass, config_entry):
    """Service sets output based on start mode."""
    entity_id = f"sensor.{config_entry.entry_id}_pid_output"
    handle = config_entry.runtime_data.handle
    handle.get_number = lambda key: {"starting_output": 42.0}.get(key)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_OUTPUT,
        {"start_mode": "Startup value"},
        target={"entity_id": entity_id},
        blocking=True,
    )

    assert handle.last_known_output == 42.0
    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == 42.0


@pytest.mark.usefixtures("setup_integration")
@pytest.mark.asyncio
async def test_set_output_custom_value(hass, config_entry):
    """Service sets output to provided custom value."""
    entity_id = f"sensor.{config_entry.entry_id}_pid_output"
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_OUTPUT,
        {"value": 7.5},
        target={"entity_id": entity_id},
        blocking=True,
    )

    handle = config_entry.runtime_data.handle
    assert handle.last_known_output == 7.5
    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == 7.5


@pytest.mark.usefixtures("setup_integration")
@pytest.mark.asyncio
async def test_set_output_value_out_of_range(hass, config_entry):
    """Service raises error when value is outside configured range."""
    entity_id = f"sensor.{config_entry.entry_id}_pid_output"
    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_OUTPUT,
            {"value": 150.0},
            target={"entity_id": entity_id},
            blocking=True,
        )


@pytest.mark.usefixtures("setup_integration")
@pytest.mark.asyncio
async def test_set_output_respects_zero_min(hass, config_entry):
    """Ensure zero output_min doesn't fall back to range minimum."""
    entity_id = f"sensor.{config_entry.entry_id}_pid_output"
    handle = config_entry.runtime_data.handle
    handle.output_range_min = -10.0
    handle.output_range_max = 10.0
    handle.get_number = lambda key: {"output_min": 0.0, "output_max": 10.0}.get(key)

    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_OUTPUT,
            {"value": -5.0},
            target={"entity_id": entity_id},
            blocking=True,
        )


@pytest.mark.usefixtures("setup_integration")
@pytest.mark.asyncio
async def test_output_not_overwritten_when_auto_mode_off(hass, config_entry):
    """Output remains unchanged after coordinator refresh when auto_mode is off."""
    entity_id = f"sensor.{config_entry.entry_id}_pid_output"
    handle = config_entry.runtime_data.handle

    handle.get_input_sensor_value = lambda: 10.0
    handle.get_number = lambda key: {
        "kp": 1.0,
        "ki": 0.1,
        "kd": 0.01,
        "setpoint": 20.0,
        "starting_output": 0.0,
        "sample_time": 5.0,
        "output_min": 0.0,
        "output_max": 200.0,
    }[key]
    handle.get_select = lambda key: "Zero start"
    handle.get_switch = lambda key: False if key == "auto_mode" else True

    coordinator = config_entry.runtime_data.coordinator

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_OUTPUT,
        {"value": 123.0},
        target={"entity_id": entity_id},
        blocking=True,
    )

    assert handle.last_known_output == 123.0
    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == 123.0

    await coordinator.async_request_refresh()
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == 123.0
    assert handle.last_known_output == 123.0
