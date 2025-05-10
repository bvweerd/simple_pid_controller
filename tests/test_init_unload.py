"""Test setup and unload entry for Simple PID Controller."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.simple_pid_controller import async_setup_entry, async_unload_entry
from custom_components.simple_pid_controller.const import DOMAIN, CONF_SENSOR_ENTITY_ID

async def test_setup_and_unload_entry(hass: HomeAssistant):
    """Test setting up and unloading the config entry."""
    entry = ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Test PID",
        data={CONF_SENSOR_ENTITY_ID: "sensor.test"},
        options={},
        entry_id="test_entry",
    )
    # Set the sensor state so setup does not fail
    hass.states.async_set("sensor.test", "5.0", {})

    # Test setup
    assert await async_setup_entry(hass, entry)
    await hass.async_block_till_done()
    assert DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]

    # Test unload
    assert await async_unload_entry(hass, entry)
    assert entry.entry_id not in hass.data.get(DOMAIN, {})
