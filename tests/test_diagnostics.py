import pytest

from custom_components.simple_pid_controller.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.simple_pid_controller.const import (
    DOMAIN,
    CONF_SENSOR_ENTITY_ID,
    CONF_NAME,
    DEFAULT_RANGE_MIN,
    DEFAULT_RANGE_MAX,
)


async def test_config_entry_diagnostics(hass, config_entry):
    """Test that diagnostics returns correct data for config entry."""
    result = await async_get_config_entry_diagnostics(hass, config_entry)

    # Controleer de entry_data
    entry_data = result.get("entry_data")
    assert entry_data["domain"] == DOMAIN
    assert entry_data["entry_id"] == config_entry.entry_id
    assert entry_data["data"][CONF_SENSOR_ENTITY_ID] == config_entry.data[CONF_SENSOR_ENTITY_ID]
    assert entry_data["data"][CONF_NAME] == config_entry.data[CONF_NAME]

    # Controleer de diagnostische payload
    data = result.get("data")
    assert data["name"] == config_entry.data[CONF_NAME]
    assert data["sensor_entity_id"] == config_entry.data[CONF_SENSOR_ENTITY_ID]
    assert data["range_min"] == DEFAULT_RANGE_MIN
    assert data["range_max"] == DEFAULT_RANGE_MAX
