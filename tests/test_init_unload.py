import pytest

from custom_components.simple_pid_controller import async_setup_entry, async_unload_entry
from custom_components.simple_pid_controller.const import DOMAIN

async def test_setup_and_unload_entry(hass, config_entry):
    """Test setting up and tearing down the entry."""
    assert config_entry.entry_id in hass.data[DOMAIN]

    assert await async_unload_entry(hass, config_entry) is True
    await hass.async_block_till_done()
    assert config_entry.entry_id not in hass.data[DOMAIN]
