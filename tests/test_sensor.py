import pytest

async def test_sensor_platform(hass, config_entry):
    """Er moet minstens één sensor worden aangemaakt."""

    sensors = hass.states.async_entity_ids("sensor")
    assert len(sensors) >= 1
