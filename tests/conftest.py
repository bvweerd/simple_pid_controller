import asyncio
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.helpers.device_registry import DeviceRegistry
from custom_components.simple_pid_controller.const import DOMAIN, CONF_SENSOR_ENTITY_ID
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
        name={CONF_NAME},
        manufacturer="Test",
        model="PID Controller",
    )

    return entry
