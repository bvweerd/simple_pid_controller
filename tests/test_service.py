import pytest
from unittest.mock import MagicMock, AsyncMock
from custom_components.simple_pid_controller.const import DOMAIN


@pytest.mark.usefixtures("setup_integration")
@pytest.mark.asyncio
async def test_set_output_manual(hass, config_entry):
    handle = config_entry.runtime_data.handle
    coordinator = config_entry.runtime_data.coordinator

    await hass.services.async_call(
        DOMAIN,
        "set_output",
        {
            "entity_id": f"sensor.{config_entry.entry_id.lower()}_pid_output",
            "value": 0.5,
        },
        blocking=True,
    )

    assert handle.last_known_output == 0.5
    assert coordinator.data == 0.5


@pytest.mark.usefixtures("setup_integration")
@pytest.mark.asyncio
async def test_set_output_preset_startup(monkeypatch, hass, config_entry):
    handle = config_entry.runtime_data.handle
    coordinator = config_entry.runtime_data.coordinator

    await hass.services.async_call(
        "number",
        "set_value",
        {
            "entity_id": f"number.{config_entry.entry_id.lower()}_startup_value",
            "value": 0.4,
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    assert handle.get_number("starting_output") == 0.4

    handle.pid.auto_mode = True
    mock_set = MagicMock()
    handle.pid.set_auto_mode = mock_set
    mock_refresh = AsyncMock()
    coordinator.async_request_refresh = mock_refresh

    await hass.services.async_call(
        DOMAIN,
        "set_output",
        {
            "entity_id": f"sensor.{config_entry.entry_id.lower()}_pid_output",
            "preset": "startup_value",
        },
        blocking=True,
    )

    assert handle.last_known_output == 0.4
    mock_set.assert_called_with(True, 0.4)
    assert mock_refresh.await_count == 1
