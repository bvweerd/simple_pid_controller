import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.helpers.device_registry import DeviceRegistry
from custom_components.simple_pid_controller.const import DOMAIN, CONF_SENSOR_ENTITY_ID
import custom_components.simple_pid_controller.sensor as sensor_mod

from homeassistant.const import CONF_NAME


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations):
    """Enable loading of custom integrations in custom_components/"""  # noqa: F811


@pytest.fixture(autouse=True)
async def setup_integration(hass, config_entry):
    """Set up the integration automatically for each test."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()


@pytest.fixture
async def config_entry(hass, device_registry: DeviceRegistry):
    """Create and add a MockConfigEntry for the Simple PID Controller integration."""
    input_sensor = "sensor.test_input"
    hass.states.async_set(input_sensor, "25.0")

    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="PID2",
        title="Test PID Controller",
        data={CONF_SENSOR_ENTITY_ID: input_sensor, CONF_NAME: "PID2"},
    )

    entry.add_to_hass(hass)

    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.entry_id,
    )

    return entry


class FakePID:
    instances = []

    def __init__(self, kp, ki, kd, setpoint=None):
        FakePID.instances.append(self)
        self.sample_time = None
        self.output_limits = None
        self.auto_mode = None
        self.proportional_on_measurement = None
        self._integral = 0.5
        self._last_output = None
        self._outputs = [10.0, 12.0]

    def __call__(self, input_value):
        if self._outputs:
            out = self._outputs.pop(0)
        else:
            out = self._last_output or 0.0
        self._last_output = out
        return out


@pytest.fixture(autouse=True)
def fake_pid(monkeypatch):
    FakePID.instances.clear()
    monkeypatch.setattr(sensor_mod, "PID", FakePID)
    return FakePID
