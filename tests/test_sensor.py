async def test_sensor_platform(hass, config_entry):
    """At least one sensor must be created."""

    sensors = hass.states.async_entity_ids("sensor")
    assert len(sensors) >= 1
