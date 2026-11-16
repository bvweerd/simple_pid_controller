import pytest
from homeassistant.helpers import entity_registry as er
from custom_components.simple_pid_controller.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.simple_pid_controller.const import (
    DOMAIN,
    CONF_SENSOR_ENTITY_ID,
    CONF_NAME,
    DEFAULT_INPUT_RANGE_MIN,
    DEFAULT_INPUT_RANGE_MAX,
    DEFAULT_OUTPUT_RANGE_MIN,
    DEFAULT_OUTPUT_RANGE_MAX,
)


@pytest.mark.usefixtures("setup_integration")
async def test_config_entry_diagnostics(hass, config_entry):
    """Test that diagnostics returns correct data for config entry."""
    result = await async_get_config_entry_diagnostics(hass, config_entry)

    # Controleer de entry_data
    entry_data = result.get("entry_data")
    assert entry_data["domain"] == DOMAIN
    assert entry_data["entry_id"] == config_entry.entry_id
    assert (
        entry_data["data"][CONF_SENSOR_ENTITY_ID]
        == config_entry.data[CONF_SENSOR_ENTITY_ID]
    )
    assert entry_data["data"][CONF_NAME] == config_entry.data[CONF_NAME]

    # Controleer de diagnostische payload
    data = result.get("data")
    assert data["name"] == config_entry.data[CONF_NAME]
    assert data["sensor_entity_id"] == config_entry.data[CONF_SENSOR_ENTITY_ID]
    assert data["input_range_min"] == DEFAULT_INPUT_RANGE_MIN
    assert data["input_range_max"] == DEFAULT_INPUT_RANGE_MAX
    assert data["output_range_min"] == DEFAULT_OUTPUT_RANGE_MIN
    assert data["output_range_max"] == DEFAULT_OUTPUT_RANGE_MAX


@pytest.mark.usefixtures("setup_integration")
async def test_diagnostics_include_settings(hass, config_entry):
    """The values set on the device page are part of the diagnostics."""
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.pid2_output_max", "value": 60},
        blocking=True,
    )
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.pid2_windup_protection"},
        blocking=True,
    )

    result = await async_get_config_entry_diagnostics(hass, config_entry)
    settings = result["data"]["settings"]

    assert set(settings) == {
        "kp",
        "ki",
        "kd",
        "setpoint",
        "sample_time",
        "output_min",
        "output_max",
        "starting_output",
        "auto_mode",
        "proportional_on_measurement",
        "windup_protection",
        "start_mode",
    }
    assert settings["output_max"] == {
        "entity_id": "number.pid2_output_max",
        "state": "60.0",
    }
    assert settings["windup_protection"]["state"] == "off"
    assert settings["kp"]["state"] == "1.0"


@pytest.mark.usefixtures("setup_integration")
async def test_diagnostics_include_controller_state(hass, config_entry):
    """The internal controller and coordinator state is part of the diagnostics."""
    coordinator = config_entry.runtime_data.coordinator
    await coordinator.async_refresh()

    result = await async_get_config_entry_diagnostics(hass, config_entry)
    controller = result["data"]["controller"]

    pid = config_entry.runtime_data.handle.pid
    assert controller["auto_mode"] is pid.auto_mode
    assert controller["tunings"] == list(pid.tunings)
    assert controller["setpoint"] == pid.setpoint
    assert controller["output_limits"] == list(pid.output_limits)
    assert controller["integral"] == pid._integral
    assert controller["update_interval"] == coordinator.update_interval.total_seconds()
    assert controller["last_update_success"] is True
    assert controller["last_exception"] is None


@pytest.mark.usefixtures("setup_integration")
async def test_diagnostics_report_missing_setting_entity(hass, config_entry):
    """A removed setting entity is reported as such, not as a default."""
    registry = er.async_get(hass)
    registry.async_remove("switch.pid2_auto_mode")
    await hass.async_block_till_done()

    result = await async_get_config_entry_diagnostics(hass, config_entry)

    assert result["data"]["settings"]["auto_mode"] == {
        "entity_id": None,
        "state": None,
    }
