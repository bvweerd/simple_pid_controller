import pytest
from datetime import timedelta
from homeassistant.util.dt import utcnow
from pytest_homeassistant_custom_component.common import async_fire_time_changed
from custom_components.simple_pid_controller.sensor import (
    PIDContributionSensor,
    PIDOutputSensor,
)
from custom_components.simple_pid_controller.coordinator import PIDDataCoordinator
from custom_components.simple_pid_controller.sensor import async_setup_entry
from custom_components.simple_pid_controller import sensor as sensor_module


@pytest.mark.asyncio
async def test_pid_output_and_contributions_update(hass, config_entry):
    """Test that PID output and contribution sensors update on Home Assistant start."""
    sample_time = 5

    handle = config_entry.runtime_data.handle

    handle.get_input_sensor_value = lambda: 10.0
    handle.get_select = lambda key: {
        "start_mode": "Startup value",
    }[key]
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

    # 2) fake time advancement to trigger scheduled update
    future = utcnow() + timedelta(seconds=sample_time)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()

    # Check PID output sensor
    out_entity = f"sensor.{config_entry.entry_id}_pid_output"
    state = hass.states.get(out_entity)
    assert state is not None
    assert float(state.state) != 0


@pytest.mark.asyncio
async def test_pid_contribution_native_value_rounding_and_none(hass, config_entry):
    """Test that PIDContributionSensor.native_value rounds correctly and returns None for unknown key."""
    handle = config_entry.runtime_data.handle
    # Provide known contributions
    handle.last_contributions = (0.1234, 1.9876, 2.5555, 3.3789)
    coordinator = PIDDataCoordinator(hass, "test", lambda: 0, interval=1)

    # Map contribution keys to expected values
    mapping = [
        ("pid_p_contrib", round(0.1234, 2)),
        ("pid_i_contrib", round(1.9876, 2)),
        ("pid_d_contrib", round(2.5555, 2)),
        ("error", -25),
        ("pid_i_delta", round(3.3789, 2)),
        ("unknown_key", None),  # Should return None
    ]

    for key, expected in mapping:
        sensor = PIDContributionSensor(
            hass,
            config_entry,
            key,
            f"sensor.{config_entry.entry_id}_{key}",
            coordinator,
        )
        sensor._handle = handle  # inject mock handle
        assert sensor.native_value == expected

    # Unknown key should return None
    sensor_none = PIDContributionSensor(
        hass,
        config_entry,
        "x",
        "sensor.{config_entry.entry_id}_pid_x_contrib",
        coordinator,
    )
    sensor_none._handle = handle
    assert sensor_none.native_value is None


@pytest.mark.asyncio
async def test_listeners_trigger_refresh_sensor(hass, config_entry, monkeypatch):
    """Lines 131-132: coordinator.async_request_refresh called on sensor state change."""
    # Prepare handle
    handle = config_entry.runtime_data.handle
    handle.get_input_sensor_value = lambda: 0.0
    handle.get_number = lambda key: 0.0
    handle.get_switch = lambda key: True

    # Capture listeners
    listeners = []
    monkeypatch.setattr(
        type(hass.bus),
        "async_listen",
        lambda self, event, cb: listeners.append((event, cb)),
    )

    # Run setup to register listeners
    entities = []
    await async_setup_entry(hass, config_entry, lambda ents: entities.extend(ents))
    coordinator = entities[0].coordinator

    # Patch refresh method
    called = []
    monkeypatch.setattr(
        coordinator, "async_request_refresh", lambda: called.append(True)
    )

    # Simulate state change event for kp
    entry_id = config_entry.entry_id
    test_entity = f"number.{entry_id}_kp"
    callback = next(cb for evt, cb in listeners if evt == "state_changed")

    from types import SimpleNamespace

    event = SimpleNamespace(data={"entity_id": test_entity})
    callback(event)
    assert (
        called
    ), "Coordinator.async_request_refresh was not called on sensor state change"


@pytest.mark.asyncio
async def test_update_pid_raises_on_missing_input(hass, config_entry):
    """Line 47: update_pid should raise ValueError when input sensor unavailable."""
    handle = config_entry.runtime_data.handle
    # Force no input value
    handle.get_input_sensor_value = lambda: None
    # Provide defaults for numbers and switches
    handle.get_number = lambda key: 0.0
    handle.get_switch = lambda key: True
    # Setup entry to get coordinator with update_method
    entities: list = []
    await async_setup_entry(hass, config_entry, lambda e: entities.extend(e))
    coordinator = entities[0].coordinator
    with pytest.raises(ValueError) as excinfo:
        await coordinator.update_method()
    assert "Input sensor not available" in str(excinfo.value)


@pytest.mark.asyncio
async def test_update_pid_output_limits_none_when_windup_protection_disabled(
    monkeypatch, hass, config_entry
):
    """Test output_limits (None, None)"""

    # Dummy PID class
    class DummyPID:
        def __init__(self, kp=0, ki=0, kd=0, setpoint=0, sample_time=None):
            self.Kp = kp
            self.Ki = ki
            self.Kd = kd
            self.setpoint = setpoint
            self.sample_time = sample_time
            self.auto_mode = False
            self.proportional_on_measurement = False
            self.tunings = (kp, ki, kd)
            self.output_limits = (123, 456)  # dummy init waarde
            self._output = 42.0
            self.components = (1.0, 2.0, 3.0)  # dummy voor sensor.py

        def set_auto_mode(self, enabled, last_output=None):
            self.auto_mode = enabled
            if last_output is not None:
                self._output = last_output

        def __call__(self, input_value):
            return self._output

    # Patch the PID in sensor-module
    from custom_components.simple_pid_controller import sensor as sensor_module

    monkeypatch.setattr(sensor_module, "PID", DummyPID)

    # init handle
    handle = config_entry.runtime_data.handle
    handle.last_contributions = (0.0, 0.0, 0.0, 0.0)
    handle.last_known_output = 0.0
    handle.get_input_sensor_value = lambda: 10.0
    handle.get_number = lambda key: {
        "kp": 1.0,
        "ki": 0.1,
        "kd": 0.01,
        "setpoint": 5.0,
        "starting_output": 0.0,
        "sample_time": 5.0,
        "output_min": 0.0,
        "output_max": 100.0,
    }.get(key, 0.0)
    handle.get_switch = lambda key: False if key == "windup_protection" else True
    handle.get_select = lambda key: "Zero start" if key == "start_mode" else None

    # Set-up components and trigger update
    entities = []
    await async_setup_entry(hass, config_entry, lambda e: entities.extend(e))
    coordinator = entities[0].coordinator
    await coordinator.update_method()

    # Extract thee DummyPID from closure of update_method
    closure_vars = {
        var: cell.cell_contents
        for var, cell in zip(
            coordinator.update_method.__code__.co_freevars,
            coordinator.update_method.__closure__,
        )
    }
    pid = closure_vars["handle"].pid

    # check output_limits
    assert pid.output_limits == (None, None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "restored_state, expected_last_known",
    [
        ("12.34", 12.34),
        ("not_a_number", 0.0),
        (None, None),
    ],
)
async def test_async_added_to_hass_restores_last_known_output(
    hass, config_entry, monkeypatch, restored_state, expected_last_known
):
    """Test that async_added_to_hass sets handle.last_known_output from a saved state or falls back to 0.0."""
    handle = config_entry.runtime_data.handle

    # Disable the coordinator's periodic scheduling to avoid lingering timers in the test
    monkeypatch.setattr(PIDDataCoordinator, "_schedule_refresh", lambda self, *_: None)

    # Maak een coordinator aan (update interval is verder niet relevant voor deze test)
    coordinator = PIDDataCoordinator(
        hass, config_entry.entry_id, lambda: None, interval=1
    )
    sensor = PIDOutputSensor(hass, config_entry, coordinator)
    sensor.handle = handle

    # Simuleer het terughalen van de laatst bekende staat
    async def fake_get_last_state():
        if restored_state is None:
            return None
        return type("State", (), {"state": restored_state})

    monkeypatch.setattr(sensor, "async_get_last_state", fake_get_last_state)

    # Act: roep de restore-hook aan
    await sensor.async_added_to_hass()

    # Assert: handle.last_known_output is juist ingesteld
    assert handle.last_known_output == expected_last_known


@pytest.mark.asyncio
async def test_update_pid_invalid_start_mode_defaults(monkeypatch, hass, config_entry):
    """Line 86: invalid start_mode calls set_auto_mode(True) without changing output."""

    # Dummy PID class matching existing tests
    class DummyPID:
        def __init__(self, kp=0, ki=0, kd=0, setpoint=0, sample_time=None):
            self.Kp = kp
            self.Ki = ki
            self.Kd = kd
            self.setpoint = setpoint
            self.sample_time = sample_time
            self.auto_mode = False
            self.proportional_on_measurement = False
            self.tunings = (kp, ki, kd)
            self.output_limits = (123, 456)
            self._output = 42.0
            self.components = (1.0, 2.0, 3.0)

        def set_auto_mode(self, enabled, last_output=None):
            self.auto_mode = enabled
            if last_output is not None:
                self._output = last_output

        def __call__(self, input_value):
            return self._output

    # Patch the PID class in the sensor module
    monkeypatch.setattr(sensor_module, "PID", DummyPID)

    # Prepare the handle
    handle = config_entry.runtime_data.handle
    handle.last_contributions = (0.0, 0.0, 0.0, 0.0)
    handle.last_known_output = 99.9  # some non‐zero initial
    handle.get_input_sensor_value = lambda: 10.0
    handle.get_number = lambda key: {
        "kp": 1.0,
        "ki": 0.1,
        "kd": 0.01,
        "setpoint": 5.0,
        "starting_output": 0.0,
        "sample_time": 5.0,
        "output_min": 0.0,
        "output_max": 100.0,
    }[key]
    handle.get_switch = lambda key: True
    handle.get_select = lambda key: "Invalid Mode" if key == "start_mode" else None

    # Run setup and trigger one PID update
    entities = []
    await sensor_module.async_setup_entry(
        hass, config_entry, lambda e: entities.extend(e)
    )
    coordinator = entities[0].coordinator
    await coordinator.update_method()

    # Extract the PID instance from the closure
    closure_vars = {
        var: cell.cell_contents
        for var, cell in zip(
            coordinator.update_method.__code__.co_freevars,
            coordinator.update_method.__closure__,
        )
    }
    pid = closure_vars["handle"].pid

    # Assert that auto_mode turned True and output stayed at the DummyPID default
    assert pid.auto_mode is True
    assert pid._output == 42.0


def test_pid_contribution_error_when_input_or_setpoint_none(hass, config_entry):
    """Line 258: native_value for 'error' should be 0 when input or setpoint is None."""
    handle = config_entry.runtime_data.handle
    handle.last_contributions = (1.0, 2.0, 3.0, 4.0)
    coordinator = PIDDataCoordinator(hass, "test", lambda: 0, interval=1)

    # Case 1: input_value is None → error = 0
    handle.get_input_sensor_value = lambda: None
    handle.get_number = lambda key: 5.0
    sensor = PIDContributionSensor(
        hass, config_entry, "error", "Error Sensor", coordinator
    )
    sensor._handle = handle
    assert sensor.native_value == 0

    # Case 2: setpoint is None → error = 0
    handle.get_input_sensor_value = lambda: 10.0
    handle.get_number = lambda key: None
    sensor = PIDContributionSensor(
        hass, config_entry, "error", "Error Sensor", coordinator
    )
    sensor._handle = handle
    assert sensor.native_value == 0
