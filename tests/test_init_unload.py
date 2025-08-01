import logging

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components.simple_pid_controller import async_setup_entry, async_unload_entry
from custom_components.simple_pid_controller.const import DOMAIN, CONF_SENSOR_ENTITY_ID, CONF_NAME

@pytest.fixture
async def skip_setup_integration():
    """Override autouse setup so tests can call setup manually."""
    yield


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


@pytest.mark.usefixtures("skip_setup_integration")
@pytest.mark.asyncio
async def test_setup_entry_not_ready_when_sensor_missing(hass, caplog):
    """async_setup_entry should raise when the sensor state is missing."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="PID_MISSING",
        title="Missing Sensor",
        data={CONF_SENSOR_ENTITY_ID: "sensor.missing", CONF_NAME: "Missing"},
    )
    entry.add_to_hass(hass)

    caplog.set_level(logging.WARNING)
    with pytest.raises(ConfigEntryNotReady):
        await async_setup_entry(hass, entry)

    assert "Sensor sensor.missing not ready" in caplog.text
