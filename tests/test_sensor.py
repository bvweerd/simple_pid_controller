import pytest
from datetime import timedelta
from homeassistant.util.dt import utcnow
from pytest_homeassistant_custom_component.common import async_fire_time_changed
from custom_components.simple_pid_controller.const import DOMAIN
from custom_components.simple_pid_controller.sensor import PIDContributionSensor
from custom_components.simple_pid_controller.coordinator import PIDDataCoordinator
from custom_components.simple_pid_controller.sensor import async_setup_entry


@pytest.mark.asyncio
async def test_pid_output_and_contributions_update(hass, config_entry):
    """Test that PID output and contribution sensors update on Home Assistant start."""
    sample_time = 5

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
    handle = hass.data[DOMAIN][config_entry.entry_id]
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
            hass, config_entry, key, f"pid_{key}_contrib", handle, coordinator
        )
        # Override internal handle to use test handle
        sensor._handle = handle
        assert sensor.native_value == expected

    # Unknown key should return None
    sensor_none = PIDContributionSensor(
        hass, config_entry, "x", "pid_x_contrib", handle, coordinator
    )
    sensor_none._handle = handle
    assert sensor_none.native_value is None


@pytest.mark.asyncio
async def test_listeners_trigger_refresh_sensor(hass, config_entry, monkeypatch):
    """Lines 131-132: coordinator.async_request_refresh called on sensor state change."""
    # Prepare handle
    handle = hass.data[DOMAIN][config_entry.entry_id]
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
