import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.simple_pid_controller.const import DOMAIN
from custom_components.simple_pid_controller import _async_update_options_listener


@pytest.fixture(autouse=True)
async def skip_setup_integration():
    """Override autouse setup from conftest."""
    yield


@pytest.mark.asyncio
async def test_async_update_options_listener_reload_called_once(hass, monkeypatch):
    entry = MockConfigEntry(domain=DOMAIN, entry_id="test_entry", data={})

    calls = []

    async def fake_reload(entry_id):
        calls.append(entry_id)

    monkeypatch.setattr(hass.config_entries, "async_reload", fake_reload)

    await _async_update_options_listener(hass, entry)

    assert calls == [entry.entry_id]
