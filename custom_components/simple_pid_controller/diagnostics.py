"""Diagnostics support for Simple PID Controller integration."""

from __future__ import annotations

from typing import Any
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry


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
            "sensor_forecast": handle.get_forecast_series(),
            "input_range_min": handle.input_range_min,
            "input_range_max": handle.input_range_max,
            "output_range_min": handle.output_range_min,
            "output_range_max": handle.output_range_max,
            "input_sensor": input_sensor_info,
            "history": {
                "input": list(handle.input_history),
                "output": list(handle.output_history),
                "pid_contributions": list(handle.pid_contribution_history),
                "sample_time": list(handle.sample_time_history),
            },
        },
    }
