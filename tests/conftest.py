import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.helpers.device_registry import DeviceRegistry
from custom_components.simple_pid_controller.const import DOMAIN, CONF_SENSOR_ENTITY_ID
import custom_components.simple_pid_controller.sensor as sensor_mod

from homeassistant.const import CONF_NAME


@pytest.fixture
def dummy_pid_class():
    """Return a Dummy PID class used for testing."""

    class DummyPID:
        def __init__(
            self, kp=0, ki=0, kd=0, setpoint=0, sample_time=None, auto_mode=False
        ):
            self.Kp = kp
            self.Ki = ki
            self.Kd = kd
            self.setpoint = setpoint
            self.sample_time = sample_time
            self.auto_mode = auto_mode
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

    return DummyPID


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations):
    """Enable loading of custom integrations in custom_components/"""  # noqa: F811


@pytest.fixture
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
    await hass.async_block_till_done()

    # device_registry.async_get_or_create(
    #    config_entry_id=entry.entry_id,
    #    identifiers={(DOMAIN, entry.entry_id)},
    #    name=entry.entry_id,
    # )

    return entry


@pytest.fixture
async def sensor_entities(hass, config_entry):
    """
    catch all SensorEntity-instances
    """
    created = []
    # async_add_entities callback fills 'created'
    await sensor_mod.async_setup_entry(
        hass, config_entry, lambda entities: created.extend(entities)
    )
    # wait till all items are created
    await hass.async_block_till_done()
    return created
