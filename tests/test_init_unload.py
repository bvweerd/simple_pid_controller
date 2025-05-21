from custom_components.simple_pid_controller import (
    async_unload_entry,
)
from custom_components.simple_pid_controller.const import DOMAIN


async def test_setup_and_unload_entry(hass, config_entry):
    """Test setting up and tearing down the entry."""
    handle = config_entry.runtime_data.handle
    assert config_entry.entry_id in handle

    assert await async_unload_entry(hass, config_entry) is True
    await hass.async_block_till_done()
    assert config_entry.entry_id not in hass.data[DOMAIN]
