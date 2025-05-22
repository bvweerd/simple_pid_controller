import pytest
from datetime import timedelta
from homeassistant.util.dt import utcnow
from pytest_homeassistant_custom_component.common import async_fire_time_changed
from custom_components.simple_pid_controller.sensor import PIDContributionSensor
from custom_components.simple_pid_controller.coordinator import PIDDataCoordinator
from custom_components.simple_pid_controller.sensor import async_setup_entry


@pytest.mark.asyncio
async def test_pid_output_and_contributions_update(hass, config_entry):
    """Test that PID output and contribution sensors update on Home Assistant start."""
    sample_time = 5

    handle = config_entry.runtime_data.handle

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
    handle.last_contributions = (0.1234, 1.9876, 2.5555)
    coordinator = PIDDataCoordinator(hass, "test", lambda: 0, interval=1)

    # Map contribution key to expected index
    mapping = [
        ("p", round(0.1234, 2)),
        ("i", round(1.9876, 2)),
        ("d", round(2.5555, 2)),
    ]
    for key, expected in mapping:
        sensor = PIDContributionSensor(
            hass, config_entry, key, f"pid_{key}_contrib", coordinator
        )
        # Override internal handle to use test handle
        sensor._handle = handle
        assert sensor.native_value == expected

    # Unknown key should return None
    sensor_none = PIDContributionSensor(
        hass, config_entry, "x", "pid_x_contrib", coordinator
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
    """Line 68: update_pid should set output_limits to (None, None) when windup_protection is False."""
    from custom_components.simple_pid_controller import sensor as sensor_module

    # Dummy PID to inspect output_limits
    class DummyPID:
        def __init__(self, kp, ki, kd, setpoint):
            self._proportional = 1.0
            self._integral = 1.0
            self._last_output = None
            self.tunings = (kp, ki, kd)
            self.setpoint = setpoint
            self.sample_time = 1.0
            self.output_limits = (0.0, 0.0)
            self.auto_mode = True
            self.proportional_on_measurement = False

        def __call__(self, input_value):
            return 0.0

    monkeypatch.setattr(sensor_module, "PID", DummyPID)
    handle = config_entry.runtime_data.handle
    # Provide valid input and parameters
    handle.get_input_sensor_value = lambda: 1.0
    handle.get_number = lambda key: 0.0
    # windup_protection False, other switches True
    handle.get_switch = lambda key: False if key == "windup_protection" else True
    entities: list = []
    await async_setup_entry(hass, config_entry, lambda e: entities.extend(e))
    coordinator = entities[0].coordinator
    # Execute update_method
    await coordinator.update_method()
    # Extract pid from closure
    freevars = coordinator.update_method.__code__.co_freevars
    pid_idx = freevars.index("pid")
    pid = coordinator.update_method.__closure__[pid_idx].cell_contents
    assert pid.output_limits == (None, None)
