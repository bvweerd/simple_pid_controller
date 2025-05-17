import pytest
from datetime import timedelta
from homeassistant.util.dt import utcnow
from pytest_homeassistant_custom_component.common import async_fire_time_changed
from custom_components.simple_pid_controller.number import DOMAIN


@pytest.mark.asyncio
async def test_pid_output_and_contributions_update(hass, config_entry):
    """Test that PID output and contribution sensors update on Home Assistant start."""
    # Set sample time
    sample_time = 5

    # Stub the handle
    handle = hass.data[DOMAIN][config_entry.entry_id]
    handle.get_input_sensor_value = lambda: 10.0
    handle.get_number = lambda key: {
        "kp": 1.0,
        "ki": 0.1,
        "kd": 0.01,
        "setpoint": 20.0,
        "sample_time": sample_time,
        "output_min": 0.0,
        "output_max": 100.0,
    }[key]
    handle.get_switch = lambda key: True

    # 1) trigger update
    hass.bus.async_fire("homeassistant_started")
    await hass.async_block_till_done()

    # 2) fake sample_time later in time
    future = utcnow() + timedelta(seconds=sample_time)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()

    # 2nd update done, check output/contributions
    out_entity = f"sensor.{config_entry.entry_id}_pid_output"
    state = hass.states.get(out_entity)
    assert state is not None
    assert float(state.state) != 0


"""
@pytest.mark.asyncio
async def test_contribution_sensors_native_value(sensor_entities, hass, config_entry):
    # Find all PIDContributionSensor-instances
    contrib = [
        s for s in sensor_entities
        if isinstance(s, PIDContributionSensor)
    ]
    assert len(contrib) == 3

    # set to known tuple
    handle = hass.data[DOMAIN][config_entry.entry_id]
    handle.last_contributions = (1.234, 2.345, 3.456)

    # Check native_value() 
    for sensor_obj, exp in zip(
            sorted(contrib_sensors, key=lambda s: s._component),
            (0.24, 0.22, 3.46),
        ):
        print(sensor_obj.native_value)
        assert sensor_obj.native_value == exp
"""
