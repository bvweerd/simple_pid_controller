import pytest
from custom_components.simple_pid_controller.number import PID_NUMBER_ENTITIES

async def test_number_platform(hass, config_entry):
    """Check that all Number entities from PID_NUMBER_ENTITIES are created."""

    numbers = hass.states.async_entity_ids("number")
    assert len(numbers) == len(PID_NUMBER_ENTITIES)

@pytest.mark.parametrize("desc", PID_NUMBER_ENTITIES)
async def test_number_entity_attributes(hass, config_entry, desc):
    # Build the entity_id from the entry and the key in the descriptor
    entity_id = f"number.{config_entry.entry_id}_{desc['key']}"

    # Check that the entity exists
    state = hass.states.get(entity_id)
    assert state is not None, f"{entity_id} bestaat niet"

    attrs = state.attributes

    # Verifieer de basis-attributen
    assert attrs["min"] == desc["min"]
    assert attrs["max"] == desc["max"]
    assert attrs["step"] == desc["step"]
    assert attrs.get("unit_of_measurement", "") == desc.get("unit", "")

    # Entity category (optioneel!)
    #expected_category = desc.get("entity_category", None)
    #if expected_category:
    #    assert attrs["entity_category"] == expected_category
    #else:
    #    # als de descriptor geen entity_category opgeeft,
    #    # moet de attribuut ook écht niet aanwezig zijn
    #    assert "entity_category" not in attrs

    # Default value in the state
    assert state.state == str(desc.get("default", 0))

    ## Unique ID and name
    #assert state.object_id == f"{config_entry.entry_id}_{desc['key']}"
    #assert state.name == desc.get("name", state.name)
