"""The Advanced PID Controller integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, CONF_SENSOR_ENTITY_ID

_LOGGER = logging.getLogger(__name__)

_PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.NUMBER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Advanced PID Controller from a config entry."""

    # Zorg dat de sensor beschikbaar is voordat we de platforms opstarten
    sensor_entity_id = entry.options.get(CONF_SENSOR_ENTITY_ID, entry.data.get(CONF_SENSOR_ENTITY_ID))
    if sensor_entity_id is None:
        _LOGGER.error("Sensor entity ID not configured")
        raise ConfigEntryNotReady("Sensor entity_id missing in config")

    sensor_state = hass.states.get(sensor_entity_id)
    if sensor_state is None or sensor_state.state in ("unknown", "unavailable"):
        _LOGGER.warning("Input sensor %s not ready, deferring setup", sensor_entity_id)
        raise ConfigEntryNotReady(f"Input sensor {sensor_entity_id} not available")

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
