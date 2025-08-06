import math

import pytest

from custom_components.simple_pid_controller.autotune import RelayAutoTuner


def test_relay_autotuner_sine_wave():
    """Relay autotuner computes correct gains from sine oscillation."""
    sample_time = 0.05
    relay_amplitude = 1.5
    period = 5.0  # seconds
    amplitude = 2.0

    steps = int(period * 5 / sample_time)  # five periods
    data = [
        amplitude * math.sin(2 * math.pi * i * sample_time / period)
        for i in range(steps)
    ]

    kp, ki, kd = RelayAutoTuner.tune(data, sample_time, relay_amplitude)

    ku = 4 * relay_amplitude / (math.pi * amplitude)
    assert kp == pytest.approx(0.6 * ku, rel=2e-2)
    assert ki == pytest.approx(1.2 * ku / period, rel=2e-2)
    assert kd == pytest.approx(0.075 * ku * period, rel=2e-2)


@pytest.mark.asyncio
async def test_autotune_switch_sets_gains_and_turns_off(
    hass, config_entry, monkeypatch
):
    """Turning on the autotune switch should populate gains and switch off."""

    # Patch autotuner to return deterministic values immediately
    def fake_tune(data, sample_time, relay):
        return (2.0, 3.0, 4.0)

    monkeypatch.setattr(RelayAutoTuner, "tune", staticmethod(fake_tune))

    handle = config_entry.runtime_data.handle
    handle.get_input_sensor_value = lambda: 1.0
    handle.get_number = lambda key: {
        "sample_time": 1.0,
        "output_min": 0.0,
        "output_max": 10.0,
        "setpoint": 0.0,
        "starting_output": 0.0,
    }[key]

    # Turn on autotune switch
    entity_id = f"switch.{config_entry.entry_id}_autotune"
    await hass.services.async_call("switch", "turn_on", {"entity_id": entity_id}, blocking=True)

    coordinator = config_entry.runtime_data.coordinator
    await coordinator.update_method()

    assert hass.states.get(entity_id).state == "off"
    assert hass.states.get(f"number.{config_entry.entry_id}_kp").state == "2.0"
    assert hass.states.get(f"number.{config_entry.entry_id}_ki").state == "3.0"
    assert hass.states.get(f"number.{config_entry.entry_id}_kd").state == "4.0"
