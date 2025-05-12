import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.simple_pid_controller.const import DOMAIN, CONF_SENSOR_ENTITY_ID


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations):
    """Enable loading of custom integrations in custom_components/"""  # noqa: F811


@pytest.fixture(autouse=True)
async def setup_integration(hass, config_entry):
    """Set up the integration automatically for each test."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()


@pytest.fixture
def config_entry(hass):
    """Create and add a MockConfigEntry for the Simple PID Controller integration."""
    input_sensor = "sensor.test_input"
    hass.states.async_set(input_sensor, "25.0")

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test PID Controller",
        data={CONF_SENSOR_ENTITY_ID: input_sensor},
        options={},
        entry_id="pid_entry",
    )
    entry.add_to_hass(hass)

    return entry
