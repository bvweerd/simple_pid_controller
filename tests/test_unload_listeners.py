import pytest

from custom_components.simple_pid_controller.sensor import async_setup_entry


@pytest.mark.usefixtures("setup_integration")
@pytest.mark.asyncio
async def test_listeners_removed_after_unload(hass, config_entry, monkeypatch):
    """Ensure state change listeners are unsubscribed when the entry unloads."""
    created = []
    called = []

    def fake_listen(self, event, callback):
        def unsub():
            called.append(True)

        created.append(unsub)
        return unsub

    monkeypatch.setattr(type(hass.bus), "async_listen", fake_listen)

    await async_setup_entry(hass, config_entry, lambda e: None)

    # Expect listeners created for all parameters
    assert len(created) > 0

    await hass.config_entries.async_unload(config_entry.entry_id)

    assert len(called) == len(created)
