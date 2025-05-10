"""Test switch platform for Simple PID Controller."""

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.simple_pid_controller.const import DOMAIN, CONF_SENSOR_ENTITY_ID
from custom_components.simple_pid_controller.switch import SWITCH_ENTITIES
from custom_components.simple_pid_controller import async_setup_entry


async def test_switch_platform(hass: HomeAssistant):
    """Test that switch entities are created on setup."""
    entry = ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Test PID",
        data={CONF_SENSOR_ENTITY_ID: "sensor.test"},
        options={},
        entry_id="test_entry",
    )
    hass.states.async_set("sensor.test", "3.0", {})

    before = len(hass.states.async_entity_ids("switch"))
    await async_setup_entry(hass, entry)
    await hass.async_block_till_done()
    after = len(hass.states.async_entity_ids("switch"))
    # Entities created for each SWITCH_ENTITIES item
    expected = len(SWITCH_ENTITIES)
    assert after - before == expected
