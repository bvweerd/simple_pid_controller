import pytest
from datetime import timedelta
from homeassistant.util.dt import utcnow
from pytest_homeassistant_custom_component.common import async_fire_time_changed
from custom_components.simple_pid_controller.number import DOMAIN


@pytest.mark.asyncio
async def test_pid_output_and_contributions_update(hass, config_entry):
    """Test that PID output and contribution sensors update on Home Assistant start."""
    # Stel sample_time in op 5 seconden voor dit voorbeeld
    sample_time = 5

    # Stub de handle zodat hij sample_time teruggeeft
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

    # 1) trigger eerste update
    hass.bus.async_fire("homeassistant_started")
    await hass.async_block_till_done()

    # 2) simuleer sample_time seconden later
    future = utcnow() + timedelta(seconds=sample_time)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()

    # Nu is de tweede update gelopen; controleer output/contributions
    out_entity = f"sensor.{config_entry.entry_id}_pid_output"
    state = hass.states.get(out_entity)
    assert state is not None
    # print("result: " + str(state.state))
    assert float(state.state) == 12.0

    """
    output_entity = f"sensor.{config_entry.entry_id}_pid_output"

    output_state = hass.states.get(output_entity)
    assert output_state is not None, f"PID output sensor {output_entity} not found"
    # State should be numeric
    try:
        float(output_state.state)
    except (ValueError, TypeError):
        pytest.fail(f"PID output state {output_state.state!r} is not numeric")

    # PID Contribution Sensors (P, I, D)
    for comp in ("p", "i", "d"):
        contrib_entity = f"sensor.{config_entry.entry_id}_pid_{comp}_contrib"
        contrib_state = hass.states.get(contrib_entity)
        assert contrib_state is not None, f"PID {comp.upper()} contribution sensor {contrib_entity} not found"
        # Contribution should be numeric (even zero)
        try:
            float(contrib_state.state)
        except (ValueError, TypeError):
            pytest.fail(f"PID {comp.upper()} contribution state {contrib_state.state!r} is not numeric")
    """
