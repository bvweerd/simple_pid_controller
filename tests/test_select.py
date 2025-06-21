import pytest
from datetime import timedelta
from homeassistant.util.dt import utcnow
from pytest_homeassistant_custom_component.common import async_fire_time_changed


@pytest.mark.asyncio
async def test_pid_start_modes(hass, config_entry):
    """Vergelijk het effect van verschillende startmodi op de PID-uitgang."""

    sample_time = 5
    base_input = 40.0
    setpoint = 50.0

    results = {}

    for start_mode in ["Zero start", "Startup value", "Last known value"]:
        # reset de PID state per iteratie
        handle = config_entry.runtime_data.handle
        handle.init_phase = True
        handle.last_known_output = 80.0

        handle.get_input_sensor_value = lambda: base_input
        handle.get_select = lambda key: start_mode if key == "start_mode" else None
        handle.get_number = lambda key: {
            "kp": 1.0,
            "ki": 0.1,
            "kd": 0.01,
            "setpoint": setpoint,
            "starting_output": 50.0,
            "sample_time": sample_time,
            "output_min": 0.0,
            "output_max": 100.0,
        }[key]
        handle.get_switch = lambda key: True

        # trigger initial update
        hass.bus.async_fire("homeassistant_started")
        await hass.async_block_till_done()

        # simulate one PID update
        future = utcnow() + timedelta(seconds=sample_time)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

        out_entity = f"sensor.{config_entry.entry_id}_pid_output"
        state = hass.states.get(out_entity)
        assert state is not None

        output = float(state.state)
        results[start_mode] = output
        print(f"{start_mode} → output: {output:.2f}")

    # Check relatieve rangorde
    assert (
        results["Last known value"] > results["Startup value"] > results["Zero start"]
    )
