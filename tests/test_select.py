import pytest
from datetime import timedelta
from homeassistant.util.dt import utcnow
from pytest_homeassistant_custom_component.common import async_fire_time_changed
from custom_components.simple_pid_controller.select import (
    START_MODE_OPTIONS,
    PIDStartModeSelect,
)


@pytest.mark.asyncio
async def test_pid_start_modes(hass, config_entry):
    """Check start modes."""

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


@pytest.mark.asyncio
async def test_async_select_option_applies_only_valid_options(
    hass, config_entry, monkeypatch
):
    """Test that async_select_option applies valid options and ignores invalid ones."""
    # Arrange: setup coordinator and select entity as in async_setup_entry
    coordinator = config_entry.runtime_data.coordinator
    select = PIDStartModeSelect(
        hass, config_entry, "start_mode", "PID Start Mode", coordinator
    )

    # Default current option should be the first entry
    assert select._attr_current_option == START_MODE_OPTIONS[0]

    # Stub out HA state write calls to track invocations
    write_calls = []
    monkeypatch.setattr(
        select, "async_write_ha_state", lambda: write_calls.append(True)
    )

    # Act & Assert 1: choosing a valid option updates current_option and writes state
    valid_option = START_MODE_OPTIONS[1]
    await select.async_select_option(valid_option)
    assert select._attr_current_option == valid_option
    assert write_calls, "async_write_ha_state should be called for a valid option"

    # Act & Assert 2: choosing an invalid option leaves current_option unchanged and does not write
    write_calls.clear()
    await select.async_select_option("not_an_option")
    assert select._attr_current_option == valid_option
    assert (
        not write_calls
    ), "async_write_ha_state should not be called for an invalid option"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "last_state, expected_option",
    [(opt, opt) for opt in START_MODE_OPTIONS],
)
async def test_async_added_to_hass_restores_previous_state(
    hass, config_entry, monkeypatch, last_state, expected_option
):
    """Test that async_added_to_hass restores last_state when it's a valid option."""
    # Arrange
    coordinator = config_entry.runtime_data.coordinator
    select = PIDStartModeSelect(
        hass, config_entry, "start_mode", "PID Start Mode", coordinator
    )

    class LastState:
        state = last_state

    async def fake_get_last_state():
        return LastState

    monkeypatch.setattr(select, "async_get_last_state", fake_get_last_state)

    # Set the current option to something else to ensure restoration occurs
    for opt in START_MODE_OPTIONS:
        if opt != expected_option:
            select._attr_current_option = opt
            break

    # Act
    await select.async_added_to_hass()

    # Assert
    assert select._attr_current_option == expected_option
