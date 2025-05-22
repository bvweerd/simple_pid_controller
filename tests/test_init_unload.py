from custom_components.simple_pid_controller import (
    async_unload_entry,
)
from custom_components.simple_pid_controller.const import DOMAIN


async def test_setup_and_unload_entry(hass, config_entry):
    """Test setting up and tearing down the entry."""
    # runtime_data should exist…
    assert hasattr(config_entry, "runtime_data")

    # …and it should carry a PIDDeviceHandle…
    handle = config_entry.runtime_data.handle
    from custom_components.simple_pid_controller import PIDDeviceHandle

    assert isinstance(handle, PIDDeviceHandle)

    # …whose .entry has the same entry_id
    assert handle.entry.entry_id == config_entry.entry_id

    # Unload-entry returned True
    assert await async_unload_entry(hass, config_entry) is True
    await hass.async_block_till_done()

    # Runtime data is empty
    assert (
        not hasattr(config_entry, "runtime_data") or config_entry.runtime_data is None
    )

    # hass Data should be gone

    assert DOMAIN not in hass.data
