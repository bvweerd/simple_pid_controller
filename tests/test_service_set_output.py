import pytest

from custom_components.simple_pid_controller import DOMAIN, SERVICE_SET_OUTPUT


@pytest.mark.usefixtures("setup_integration")
@pytest.mark.asyncio
async def test_set_output_start_mode(hass, config_entry):
    """Service sets output based on start mode."""
    entity_id = f"sensor.{config_entry.entry_id}_pid_output"
    handle = config_entry.runtime_data.handle
    handle.get_number = lambda key: {"starting_output": 42.0}.get(key)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_OUTPUT,
        {"start_mode": "Startup value"},
        target={"entity_id": entity_id},
        blocking=True,
    )

    assert handle.last_known_output == 42.0
    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == 42.0


@pytest.mark.usefixtures("setup_integration")
@pytest.mark.asyncio
async def test_set_output_custom_value(hass, config_entry):
    """Service sets output to provided custom value."""
    entity_id = f"sensor.{config_entry.entry_id}_pid_output"
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_OUTPUT,
        {"value": 7.5},
        target={"entity_id": entity_id},
        blocking=True,
    )

    handle = config_entry.runtime_data.handle
    assert handle.last_known_output == 7.5
    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == 7.5
