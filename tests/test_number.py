"""Test number platform for Simple PID Controller."""
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.simple_pid_controller.const import DOMAIN, CONF_SENSOR_ENTITY_ID
from custom_components.simple_pid_controller.number import PID_NUMBER_ENTITIES
from custom_components.simple_pid_controller import async_setup_entry

async def test_number_platform(hass: HomeAssistant):
    """Test that number entities are created on setup."""
    entry = ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Test PID",
        data={CONF_SENSOR_ENTITY_ID: "sensor.test"},
        options={},
        entry_id="test_entry",
    )
    hass.states.async_set("sensor.test", "3.0", {})

    before = len(hass.states.async_entity_ids("number"))
    await async_setup_entry(hass, entry)
    await hass.async_block_till_done()
    after = len(hass.states.async_entity_ids("number"))
    # Entities created for each PID_NUMBER_ENTITIES item, twice
    expected = len(PID_NUMBER_ENTITIES) * 2
    assert after - before == expected
