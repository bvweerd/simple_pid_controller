"""Diagnostics support for Simple PID Controller integration."""

from __future__ import annotations

from typing import Any
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

# The settings a user changes on the device page live in these entities, not
# in the config entry, so they have to be read from the state machine.
SETTING_ENTITIES: dict[str, tuple[str, ...]] = {
    "number": (
        "kp",
        "ki",
        "kd",
        "setpoint",
        "sample_time",
        "output_min",
        "output_max",
        "starting_output",
    ),
    "switch": ("auto_mode", "proportional_on_measurement", "windup_protection"),
    "select": ("start_mode",),
}


def _settings(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    """Return the raw state of every setting entity of this entry.

    The raw state is reported rather than the value the controller derives
    from it: a missing or unavailable entity falls back to a default there
    (switches count as on), and that fallback is exactly what a diagnosis
    needs to see.
    """
    registry = er.async_get(hass)
    settings: dict[str, Any] = {}
    for platform, keys in SETTING_ENTITIES.items():
        for key in keys:
            entity_id = registry.async_get_entity_id(
                platform, DOMAIN, f"{entry.entry_id}_{key}"
            )
            state = hass.states.get(entity_id) if entity_id else None
            settings[key] = {
                "entity_id": entity_id,
                "state": state.state if state is not None else None,
            }
    return settings


def _controller(entry: ConfigEntry) -> dict[str, Any] | None:
    """Return the internal state of the PID controller and its coordinator."""
    handle = entry.runtime_data.handle
    pid = getattr(handle, "pid", None)
    if pid is None:
        return None
    coordinator = entry.runtime_data.coordinator
    interval = coordinator.update_interval if coordinator is not None else None
    return {
        "auto_mode": pid.auto_mode,
        "tunings": list(pid.tunings),
        "setpoint": pid.setpoint,
        "output_limits": list(pid.output_limits),
        "proportional_on_measurement": pid.proportional_on_measurement,
        # simple_pid exposes the accumulated integral only as a private
        # attribute; it is what shows whether the I-term is wound up.
        "integral": getattr(pid, "_integral", None),
        "last_known_output": handle.last_known_output,
        "last_measured_sample_time": handle.last_measured_sample_time,
        "update_interval": interval.total_seconds() if interval else None,
        "last_update_success": (
            coordinator.last_update_success if coordinator is not None else None
        ),
        "last_exception": (
            repr(coordinator.last_exception)
            if coordinator is not None and coordinator.last_exception
            else None
        ),
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    handle = entry.runtime_data.handle

    sensor_state = hass.states.get(handle.sensor_entity_id)
    input_sensor_info: dict[str, Any] | None = None
    if sensor_state is not None:
        input_sensor_info = {
            "entity_id": sensor_state.entity_id,
            "state": sensor_state.state,
            "attributes": dict(sensor_state.attributes),
            "last_changed": sensor_state.last_changed.isoformat(),
            "last_updated": sensor_state.last_updated.isoformat(),
        }

    return {
        "entry_data": entry.as_dict(),
        "data": {
            "name": handle.name,
            "sensor_entity_id": handle.sensor_entity_id,
            # The bounds the setpoint and output numbers may be set within,
            # not the Output Min/Max values themselves (see "settings").
            "input_range_min": handle.input_range_min,
            "input_range_max": handle.input_range_max,
            "output_range_min": handle.output_range_min,
            "output_range_max": handle.output_range_max,
            "input_sensor": input_sensor_info,
            "settings": _settings(hass, entry),
            "controller": _controller(entry),
            "history": {
                "input": list(handle.input_history),
                "output": list(handle.output_history),
                "pid_contributions": list(handle.pid_contribution_history),
                "sample_time": list(handle.sample_time_history),
            },
        },
    }
