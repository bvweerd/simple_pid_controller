"""Simple PID Controller integration."""

from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, CONF_NAME, CONF_SENSOR_ENTITY_ID

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.NUMBER, Platform.SWITCH]


class PIDDeviceHandle:
    """Shared device handle for a PID controller config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.name = entry.data.get(CONF_NAME)
        self.sensor_entity_id = entry.options.get(
            CONF_SENSOR_ENTITY_ID, entry.data.get(CONF_SENSOR_ENTITY_ID)
        )
        self.last_contributions = (None, None, None)  # (P, I, D)

    def _get_entity_id(self, platform: str, key: str) -> str | None:
        """Lookup the real entity_id in the registry by unique_id == '<entry_id>_<key>'."""
        registry = er.async_get(self.hass)
        unique = f"{self.entry.entry_id}_{key}"
        entity_id = registry.async_get_entity_id(platform, DOMAIN, unique)
        if not entity_id:
            _LOGGER.debug("No %s entity found for unique_id '%s'", platform, unique)
        return entity_id

    def get_number(self, key: str) -> float | None:
        """Return the current value of the number entity, or None."""
        entity_id = self._get_entity_id("number", key)
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        _LOGGER.debug("get_number(%s) → %s = %s", key, entity_id, state and state.state)
        if state and state.state not in ("unknown", "unavailable"):
            try:
                return float(state.state)
            except ValueError:
                _LOGGER.error(
                    "Could not parse state '%s' of %s as float", state.state, entity_id
                )
        return None

    def get_switch(self, key: str) -> bool:
        """Return True/False of switch entity, default True if missing."""
        entity_id = self._get_entity_id("switch", key)
        if not entity_id:
            return True
        state = self.hass.states.get(entity_id)
        _LOGGER.debug("get_switch(%s) → %s = %s", key, entity_id, state and state.state)
        if state and state.state not in ("unknown", "unavailable"):
            return state.state == "on"
        return True

    def get_input_sensor_value(self) -> float | None:
        """Return the input value from configured sensor."""
        state = self.hass.states.get(self.sensor_entity_id)
        if state and state.state not in ("unknown", "unavailable"):
            try:
                return float(state.state)
            except ValueError:
                _LOGGER.warning(
                    f"Sensor {self.sensor_entity_id} has invalid value. PID-calculation skipped."
                )
        return None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Simple PID Controller from a config entry."""

    sensor_entity_id = entry.options.get(
        CONF_SENSOR_ENTITY_ID, entry.data.get(CONF_SENSOR_ENTITY_ID)
    )
    state = hass.states.get(sensor_entity_id)
    if state is None or state.state in ("unknown", "unavailable"):
        _LOGGER.warning("Sensor %s not ready; delaying setup", sensor_entity_id)
        raise ConfigEntryNotReady(f"Sensor {sensor_entity_id} not ready")

    handle = PIDDeviceHandle(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = handle

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload PID Controller entry."""
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
