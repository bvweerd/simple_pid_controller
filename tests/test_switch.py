import pytest
from custom_components.simple_pid_controller.switch import (
    SWITCH_ENTITIES,
    PIDOptionSwitch,
)


@pytest.mark.asyncio
async def test_switch_operations(hass, config_entry):
    """Test that each switch entity is created and can be toggled on/off."""
    for desc in SWITCH_ENTITIES:
        entity_id = f"switch.{config_entry.entry_id}_{desc['key']}"

        # Default state should match description
        state = hass.states.get(entity_id)
        assert state is not None, f"Switch {entity_id} does not exist"
        if desc["default_state"]:
            assert state.state == "on"
        else:
            assert state.state == "off"

        # Turn off and verify
        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": entity_id}, blocking=True
        )
        assert hass.states.get(entity_id).state == "off"

        # Turn on and verify
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": entity_id}, blocking=True
        )
        assert hass.states.get(entity_id).state == "on"


@pytest.mark.asyncio
@pytest.mark.parametrize("last_state, expected", [("on", True), ("off", False)])
async def test_async_added_to_hass_restores_previous_state(
    hass, config_entry, monkeypatch, last_state, expected
):
    """Test that PIDOptionSwitch.async_added_to_hass restores previous state (lines 47-48)."""
    # Use first entity descriptor
    desc = SWITCH_ENTITIES[0]
    switch = PIDOptionSwitch(hass, config_entry, desc)

    # Fake a previous state
    class LastState:
        def __init__(self, state):
            self.state = state

    async def fake_get_last_state():
        return LastState(last_state)

    monkeypatch.setattr(switch, "async_get_last_state", fake_get_last_state)
    # Set initial state opposite to expected to ensure restoration occurs
    switch._state = not expected

    await switch.async_added_to_hass()
    assert switch.is_on is expected
