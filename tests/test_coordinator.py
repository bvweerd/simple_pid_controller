import pytest
from custom_components.simple_pid_controller.coordinator import PIDDataCoordinator


@pytest.mark.asyncio
async def test_coordinator_update_method_assignment(hass):
    """Test that the coordinator assigns the update_method and calls it."""

    # Dummy async update method
    called = {}

    async def dummy_update_method():
        called["yes"] = True
        return 42.0

    coordinator = PIDDataCoordinator(
        hass=hass,
        name="test",
        update_method=dummy_update_method,
        interval=10,  # 10 seconds
    )

    # Check assignment
    assert coordinator.update_method == dummy_update_method

    # Call _async_update_data and ensure dummy_update_method is called and result is correct
    result = await coordinator._async_update_data()
    assert result == 42.0
    assert called["yes"] is True
