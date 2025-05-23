import pytest
import logging
from custom_components.simple_pid_controller.number import (
    PID_NUMBER_ENTITIES,
    CONTROL_NUMBER_ENTITIES,
    PIDParameterNumber,
    ControlParameterNumber,
)
from custom_components.simple_pid_controller.const import (
    DEFAULT_RANGE_MIN,
    DEFAULT_RANGE_MAX,
)


async def test_number_platform(hass, config_entry):
    """Check that all Number entities from PID_NUMBER_ENTITIES are created."""

    numbers = hass.states.async_entity_ids("number")
    assert len(numbers) == len(PID_NUMBER_ENTITIES) + len(CONTROL_NUMBER_ENTITIES)


@pytest.mark.parametrize("desc", PID_NUMBER_ENTITIES)
async def test_number_entity_attributes(hass, config_entry, desc):
    entity_id = f"number.{config_entry.entry_id}_{desc['key']}"
    state = hass.states.get(entity_id)

    attrs = state.attributes

    # Verify base attributes
    assert attrs["min"] == desc["min"]
    assert attrs["max"] == desc["max"]
    assert attrs["step"] == desc["step"]
    assert attrs.get("unit_of_measurement", "") == desc.get("unit", "")

    # Default value in the state
    assert state.state == str(desc.get("default", 0))

    ## Unique ID and name
    # assert state.object_id == f"{config_entry.entry_id}_{desc['key']}"
    # assert state.name == desc.get("name", state.name)


@pytest.mark.parametrize(
    "last_value, expected",
    [
        (PID_NUMBER_ENTITIES[0]["min"] - 1, PID_NUMBER_ENTITIES[0]["min"]),
        (PID_NUMBER_ENTITIES[0]["max"] + 1, PID_NUMBER_ENTITIES[0]["max"]),
        (
            (PID_NUMBER_ENTITIES[0]["min"] + PID_NUMBER_ENTITIES[0]["max"]) / 2,
            (PID_NUMBER_ENTITIES[0]["min"] + PID_NUMBER_ENTITIES[0]["max"]) / 2,
        ),
    ],
)
async def test_async_added_to_hass_clamps_pid_value(
    hass, config_entry, monkeypatch, last_value, expected
):
    """Test that restored PIDParameterNumber clamps values outside range to min/max."""
    desc = PID_NUMBER_ENTITIES[0]
    num = PIDParameterNumber(hass, config_entry, desc)

    async def fake_get_last_number_data():
        return type("Last", (), {"native_value": last_value})

    monkeypatch.setattr(num, "async_get_last_number_data", fake_get_last_number_data)

    await num.async_added_to_hass()
    assert num.native_value == expected


async def test_async_added_to_hass_clamps_control_value(
    hass, config_entry, monkeypatch
):
    """Test that restored ControlParameterNumber clamps values outside dynamic range to min/max."""
    for desc in CONTROL_NUMBER_ENTITIES:
        num = ControlParameterNumber(hass, config_entry, desc)
        min_val = num._attr_native_min_value
        max_val = num._attr_native_max_value

        # Below minimum should clamp to min_val
        async def fake_last_below():
            return type("Last", (), {"native_value": min_val - 1})

        monkeypatch.setattr(num, "async_get_last_number_data", fake_last_below)
        await num.async_added_to_hass()
        assert num.native_value == min_val

        # Above maximum should clamp to max_val
        async def fake_last_above():
            return type("Last", (), {"native_value": max_val + 1})

        monkeypatch.setattr(num, "async_get_last_number_data", fake_last_above)
        await num.async_added_to_hass()
        assert num.native_value == max_val

        # Value within range should be set as is
        mid = (min_val + max_val) / 2

        async def fake_last_within():
            return type("Last", (), {"native_value": mid})

        monkeypatch.setattr(num, "async_get_last_number_data", fake_last_within)
        await num.async_added_to_hass()
        assert num.native_value == mid


@pytest.mark.parametrize(
    "clazz, desc, sample_value",
    [
        (PIDParameterNumber, PID_NUMBER_ENTITIES[0], PID_NUMBER_ENTITIES[0]["default"]),
        (
            ControlParameterNumber,
            CONTROL_NUMBER_ENTITIES[0],
            CONTROL_NUMBER_ENTITIES[0]["default"],
        ),
    ],
)
async def test_async_set_native_value_triggers_write(
    hass, config_entry, monkeypatch, clazz, desc, sample_value
):
    """Test that async_set_native_value sets value and calls async_write_ha_state."""
    num = clazz(hass, config_entry, desc)
    write_calls = []

    def fake_write_state():
        write_calls.append(True)

    monkeypatch.setattr(num, "async_write_ha_state", fake_write_state)

    await num.async_set_native_value(sample_value)
    assert num.native_value == sample_value
    assert write_calls, "async_write_ha_state was not called"


@pytest.mark.parametrize("invalid_key", ["invalid1", "invalid2"])
async def test_controlparameter_number_unexpected_key(
    hass, config_entry, caplog, invalid_key
):
    """Test that ControlParameterNumber logs error and uses default range for unexpected key."""
    desc = {
        "name": "Invalid",
        "key": invalid_key,
        "unit": "",
        "step": 1.0,
        "default": 0.0,
        "entity_category": None,
    }
    caplog.set_level(logging.ERROR)
    num = ControlParameterNumber(hass, config_entry, desc)
    assert f"Unexpected PID parameter key: {invalid_key}" in caplog.text
    assert num._attr_native_min_value == DEFAULT_RANGE_MIN
    assert num._attr_native_max_value == DEFAULT_RANGE_MAX
