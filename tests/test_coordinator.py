import pytest
from custom_components.simple_pid_controller.coordinator import PIDDataCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed


async def test_async_update_data_success(hass):
    """Test that _async_update_data returns the value from update_method on success."""

    async def fake_update():
        return 42.0

    coordinator = PIDDataCoordinator(hass, "test", fake_update, interval=1)
    result = await coordinator._async_update_data()
    assert result == 42.0


async def test_async_update_data_failure(hass):
    """Test that _async_update_data raises UpdateFailed with proper message on exception."""

    async def fake_update():
        raise ValueError("test error")

    coordinator = PIDDataCoordinator(hass, "test", fake_update, interval=1)
    with pytest.raises(UpdateFailed) as excinfo:
        await coordinator._async_update_data()
    assert "PID update failed: test error" in str(excinfo.value)
