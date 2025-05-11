import pytest
from custom_components.simple_pid_controller.number import PID_NUMBER_ENTITIES

async def test_number_platform(hass, config_entry):
    """Controleer dat alle Number-entities uit PID_NUMBER_ENTITIES worden aangemaakt."""

    numbers = hass.states.async_entity_ids("number")
    assert len(numbers) == len(PID_NUMBER_ENTITIES)

@pytest.mark.parametrize("desc", PID_NUMBER_ENTITIES)
async def test_number_entity_attributes(hass, config_entry, desc):
    # Bouw de entity_id op vanuit de entry en de key uit de descriptor
    entity_id = f"number.{config_entry.entry_id}_{desc['key']}"

    # Controleer dat de entity bestaat
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

    # Default-waarde in de state
    assert state.state == str(desc.get("default", 0))

    ## Unieke ID en name
    #assert state.object_id == f"{config_entry.entry_id}_{desc['key']}"
    #assert state.name == desc.get("name", state.name)
