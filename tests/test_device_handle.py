import pytest
from homeassistant.helpers import entity_registry as er
from custom_components.simple_pid_controller import PIDDeviceHandle
from custom_components.simple_pid_controller.const import DOMAIN


class DummyRegistry:
    def __init__(self, entity_id):
        self._entity_id = entity_id

    def async_get_entity_id(self, platform, domain, unique_id):
        # Return entity_id or None
        if self._entity_id and domain == DOMAIN:
            return self._entity_id
        return None


@pytest.mark.parametrize(
    "state_value, expected",
    [
        ("12.34", 12.34),  # valid number
        ("abc", None),  # no number → exception
        ("unknown", None),  # unknown → skip
        ("unavailable", None),  # unavailable → skip
    ],
)
def test_get_number_various_states(
    monkeypatch, hass, config_entry, state_value, expected
):
    """Cover lines 45–54 of get_number."""
    # 1) Stel een fake entity in de state machine
    fake_eid = "number.pid_entry_test"
    hass.states.async_set(fake_eid, state_value)

    # 2) Mock de registry so _get_entity_id gives fake_eid
    monkeypatch.setattr(er, "async_get", lambda hass_: DummyRegistry(fake_eid))

    # 3) Create handle and call get_number
    handle = PIDDeviceHandle(hass, config_entry)
    result = handle.get_number("test")

    assert result == expected


def test_get_number_no_entity(monkeypatch, hass, config_entry):
    """If _get_entity_id is None, get_number should be None."""
    # Mock registry zonder entity
    monkeypatch.setattr(er, "async_get", lambda hass_: DummyRegistry(None))

    handle = PIDDeviceHandle(hass, config_entry)
    assert handle.get_number("anything") is None


def test_get_switch_on_off(monkeypatch, hass, config_entry):
    """Cover on/off in get_switch."""
    fake_entity = "switch.pid_entry_test"
    # Force _get_entity_id terug te geven
    handle = PIDDeviceHandle(hass, config_entry)
    monkeypatch.setattr(handle, "_get_entity_id", lambda platform, key: fake_entity)

    # Eerst “on” → True
    hass.states.async_set(fake_entity, "on")
    assert handle.get_switch("any_key") is True

    # Dan “off” → False
    hass.states.async_set(fake_entity, "off")
    assert handle.get_switch("any_key") is False


def test_get_input_sensor_value_invalid(hass, config_entry):
    """Cover the ValueError branch in get_input_sensor_value (lines 73–77)."""
    handle = PIDDeviceHandle(hass, config_entry)
    # Set the sensor_entity_id
    handle.sensor_entity_id = "sensor.pid_entry_test"

    # Provide a non-numeric value
    hass.states.async_set(handle.sensor_entity_id, "not_a_number")

    # Should handle gracefully and return None
    assert handle.get_input_sensor_value() is None
