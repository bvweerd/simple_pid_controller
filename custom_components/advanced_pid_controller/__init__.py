"""The PID Controller integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.NUMBER]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Advanced PID Controller from a config entry."""

    # Zorg dat de vereiste input sensor beschikbaar is
    sensor_entity_id = entry.options.get("sensor_entity_id", entry.data.get("sensor_entity_id"))
    if sensor_entity_id is None:
        raise ConfigEntryNotReady("Sensor entity_id not configured")

    sensor_state = hass.states.get(sensor_entity_id)
    if sensor_state is None or sensor_state.state in ("unknown", "unavailable"):
        raise ConfigEntryNotReady(f"Input sensor {sensor_entity_id} not ready")

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
