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

    return {
        "entry_data": entry.as_dict(),
        "data": {
            "name": handle.name,
            "sensor_entity_id": handle.sensor_entity_id,
            "range_min": handle.range_min,
            "range_max": handle.range_max,
        },
    }
