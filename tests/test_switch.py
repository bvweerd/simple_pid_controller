import pytest
from custom_components.simple_pid_controller.switch import SWITCH_ENTITIES


@pytest.mark.asyncio
async def test_switch_operations(hass, config_entry):
    """Test that each switch entity is created and can be toggled on/off."""
    for desc in SWITCH_ENTITIES:
        entity_id = f"switch.{config_entry.entry_id}_{desc['key']}"

        # Default state should be 'on'
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
