"""Common fixtures for Simple PID Controller tests."""

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.simple_pid_controller.const import DOMAIN, CONF_SENSOR_ENTITY_ID

@pytest.fixture
def config_entry(hass: HomeAssistant):
    """Create a mock config entry."""
    entry = ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Test PID",
        data={CONF_SENSOR_ENTITY_ID: "sensor.test"},
        options={},
        entry_id="test_entry",
    )
    return entry
