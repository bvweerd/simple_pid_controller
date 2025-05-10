"""Test the PIDDataCoordinator."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.simple_pid_controller.coordinator import PIDDataCoordinator


async def test_coordinator_success(hass: HomeAssistant):
    """Test that coordinator returns update_method value."""

    async def dummy_update():
        return 42.0

    coordinator = PIDDataCoordinator(hass, "test", dummy_update, interval=1)
    result = await coordinator._async_update_data()
    assert result == 42.0


async def test_coordinator_failure(hass: HomeAssistant):
    """Test that coordinator raises UpdateFailed on exception."""

    async def dummy_fail():
        raise RuntimeError("fail")

    coordinator = PIDDataCoordinator(hass, "test", dummy_fail, interval=1)
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
