"""Tests for the bundled 'send output to an entity' automation blueprint."""

from pathlib import Path
import shutil

import pytest
from pytest_homeassistant_custom_component.common import async_mock_service

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

BLUEPRINT = (
    Path(__file__).parent.parent
    / "blueprints"
    / "automation"
    / "simple_pid_controller"
    / "pid_output_to_entity.yaml"
)
PID_OUTPUT = "sensor.spid_x_pid_output"


async def _setup(hass: HomeAssistant, target: str) -> None:
    dest = Path(hass.config.path("blueprints/automation/simple_pid_controller"))
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(BLUEPRINT, dest / BLUEPRINT.name)

    hass.states.async_set(PID_OUTPUT, "unknown")
    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": {
                "use_blueprint": {
                    "path": f"simple_pid_controller/{BLUEPRINT.name}",
                    "input": {"pid_output": PID_OUTPUT, "target_entity": target},
                }
            }
        },
    )
    await hass.async_block_till_done()


@pytest.mark.parametrize(
    "target, attrs, service_domain, service, field",
    [
        ("number.heater", {"min": 0, "max": 100}, "number", "set_value", "value"),
        (
            "input_number.heater",
            {"min": 0, "max": 100},
            "input_number",
            "set_value",
            "value",
        ),
        (
            "climate.living",
            {"min_temp": 5, "max_temp": 30, "supported_features": 1},
            "climate",
            "set_temperature",
            "temperature",
        ),
    ],
)
async def test_output_is_forwarded(
    hass: HomeAssistant, target, attrs, service_domain, service, field
):
    """The PID output is sent to the target with the matching action."""
    hass.states.async_set(
        target, "heat" if target.startswith("climate") else "10", attrs
    )
    calls = async_mock_service(hass, service_domain, service)
    await _setup(hass, target)

    hass.states.async_set(PID_OUTPUT, "21.5")
    await hass.async_block_till_done()

    assert len(calls) == 1
    assert target in calls[0].data["entity_id"]
    assert float(calls[0].data[field]) == 21.5


async def test_output_is_clamped(hass: HomeAssistant):
    """Values outside the target's min/max are clamped."""
    hass.states.async_set("number.heater", "10", {"min": 0, "max": 50})
    calls = async_mock_service(hass, "number", "set_value")
    await _setup(hass, "number.heater")

    hass.states.async_set(PID_OUTPUT, "80")
    await hass.async_block_till_done()
    hass.states.async_set(PID_OUTPUT, "-5")
    await hass.async_block_till_done()

    assert [float(c.data["value"]) for c in calls] == [50.0, 0.0]


async def test_nothing_sent_without_numeric_output(hass: HomeAssistant):
    """No action runs while the PID output is unknown or unavailable."""
    hass.states.async_set("number.heater", "10", {"min": 0, "max": 100})
    calls = async_mock_service(hass, "number", "set_value")
    await _setup(hass, "number.heater")

    hass.states.async_set(PID_OUTPUT, "unavailable")
    await hass.async_block_till_done()

    assert calls == []


async def test_nothing_sent_to_unavailable_target(hass: HomeAssistant):
    """No action runs while the target entity is unavailable."""
    hass.states.async_set("number.heater", "unavailable", {"min": 0, "max": 100})
    calls = async_mock_service(hass, "number", "set_value")
    await _setup(hass, "number.heater")

    hass.states.async_set(PID_OUTPUT, "42")
    await hass.async_block_till_done()

    assert calls == []


@pytest.mark.parametrize(
    "state, features",
    [
        ("heat_cool", 1 | 2),  # dual setpoint mode needs target_temp_low/high
        ("heat", 2),  # only TARGET_TEMPERATURE_RANGE supported
    ],
)
async def test_climate_without_single_setpoint_is_skipped(
    hass: HomeAssistant, state, features
):
    """Nothing is sent to a thermostat that cannot take a single temperature."""
    hass.states.async_set(
        "climate.living",
        state,
        {"min_temp": 5, "max_temp": 30, "supported_features": features},
    )
    calls = async_mock_service(hass, "climate", "set_temperature")
    await _setup(hass, "climate.living")

    hass.states.async_set(PID_OUTPUT, "21.5")
    await hass.async_block_till_done()

    assert calls == []
