import pytest
from datetime import timedelta
from homeassistant.util.dt import utcnow
from pytest_homeassistant_custom_component.common import async_fire_time_changed


@pytest.mark.parametrize(
    "start_mode,expected_output",
    [
        ("Zero start", 0.0),
        (
            "Last known value",
            0.0,
        ),  # default `last_known_output` = None → fallback naar 0
        ("Startup value", 50.0),
    ],
)
@pytest.mark.asyncio
async def test_pid_start_modes(hass, config_entry, start_mode, expected_output):
    """Test that each PID start_mode behaves as expected."""
    sample_time = 5

    handle = config_entry.runtime_data.handle
    handle.init_phase = True  # simulate init

    handle.get_input_sensor_value = lambda: 10.0
    handle.get_select = lambda key: start_mode if key == "start_mode" else None
    handle.get_number = lambda key: {
        "kp": 1.0,
        "ki": 0.1,
        "kd": 0.01,
        "setpoint": 20.0,
        "starting_output": 50.0,
        "sample_time": sample_time,
        "output_min": 0.0,
        "output_max": 100.0,
    }[key]
    handle.get_switch = lambda key: True

    # 1) trigger initial update
    hass.bus.async_fire("homeassistant_started")
    await hass.async_block_till_done()

    # 2) simulate scheduled update
    future = utcnow() + timedelta(seconds=sample_time)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()

    # Check PID output sensor
    out_entity = f"sensor.{config_entry.entry_id}_pid_output"
    state = hass.states.get(out_entity)

    assert state is not None
    output = float(state.state)

    # Output is not exactly predictable due to PID internals, but should not be None or error
    assert isinstance(output, float)

    # Optional: check expected startup behavior — initial output close to what was forced
    if start_mode == "Startup value":
        assert output == pytest.approx(50.0, abs=1.0)
    elif start_mode == "Zero start":
        assert output == pytest.approx(0.0, abs=1.0)
    elif start_mode == "Last known value":
        assert output == pytest.approx(0.0, abs=1.0)
