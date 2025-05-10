"""Test sensor platform for Simple PID Controller."""
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.simple_pid_controller.const import DOMAIN, CONF_SENSOR_ENTITY_ID
from custom_components.simple_pid_controller import async_setup_entry

async def test_sensor_platform(hass: HomeAssistant):
    """Test that sensor entities are created on setup."""
    entry = ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Test PID",
        data={CONF_SENSOR_ENTITY_ID: "sensor.test"},
        options={},
        entry_id="test_entry",
    )
    # Set a dummy sensor state
    hass.states.async_set("sensor.test", "3.0", {})

    before = len(hass.states.async_entity_ids("sensor"))
    await async_setup_entry(hass, entry)
    await hass.async_block_till_done()
    after = len(hass.states.async_entity_ids("sensor"))
    # Expect 4 new sensors: output + 3 contributions
    assert after - before == 4
