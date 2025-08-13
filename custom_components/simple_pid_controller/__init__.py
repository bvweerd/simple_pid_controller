"""Simple PID Controller integration."""

from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er, config_validation as cv
from dataclasses import dataclass
import voluptuous as vol
from .coordinator import PIDDataCoordinator
from .select import START_MODE_OPTIONS

from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_SENSOR_ENTITY_ID,
    CONF_INPUT_RANGE_MIN,
    CONF_INPUT_RANGE_MAX,
    CONF_OUTPUT_RANGE_MIN,
    CONF_OUTPUT_RANGE_MAX,
    DEFAULT_INPUT_RANGE_MIN,
    DEFAULT_INPUT_RANGE_MAX,
    DEFAULT_OUTPUT_RANGE_MIN,
    DEFAULT_OUTPUT_RANGE_MAX,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.SELECT,
]

SERVICE_SET_OUTPUT = "set_output"


@dataclass
class MyData:
    handle: PIDDeviceHandle
    coordinator: PIDDataCoordinator = None


class PIDDeviceHandle:
    """Shared device handle for a PID controller config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.name = entry.data.get(CONF_NAME)
        self.input_range_min = entry.options.get(
            CONF_INPUT_RANGE_MIN,
            entry.data.get(CONF_INPUT_RANGE_MIN, DEFAULT_INPUT_RANGE_MIN),
        )
        self.input_range_max = entry.options.get(
            CONF_INPUT_RANGE_MAX,
            entry.data.get(CONF_INPUT_RANGE_MAX, DEFAULT_INPUT_RANGE_MAX),
        )
        self.output_range_min = entry.options.get(
            CONF_OUTPUT_RANGE_MIN,
            entry.data.get(CONF_OUTPUT_RANGE_MIN, DEFAULT_OUTPUT_RANGE_MIN),
        )
        self.output_range_max = entry.options.get(
            CONF_OUTPUT_RANGE_MAX,
            entry.data.get(CONF_OUTPUT_RANGE_MAX, DEFAULT_OUTPUT_RANGE_MAX),
        )
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

    def get_select(self, key: str) -> str | None:
        """Return the current value of the select entity, or None."""
        entity_id = self._get_entity_id("select", key)
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        _LOGGER.debug("get_select(%s) → %s = %s", key, entity_id, state and state.state)

        if state and state.state not in ("unknown", "unavailable"):
            return state.state  # Selects geven strings terug, geen conversie nodig

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
                    f"Sensor {self.sensor_entity_id} invalid value. PID-calculation skipped."
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
    entry.runtime_data = MyData(handle=handle)

    # register updatelistener for optionsflow
    entry.async_on_unload(entry.add_update_listener(_async_update_options_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.services.has_service(DOMAIN, SERVICE_SET_OUTPUT):

        async def async_set_output(call: ServiceCall) -> None:
            entity_id = call.data["entity_id"]
            start_mode = call.data.get("start_mode")
            value = call.data.get("value")

            registry = er.async_get(hass)
            entity_entry = registry.async_get(entity_id)
            if entity_entry is None:
                raise ValueError(f"Entity {entity_id} not found")

            cfg_entry = hass.config_entries.async_get_entry(
                entity_entry.config_entry_id
            )
            if cfg_entry is None or cfg_entry.domain != DOMAIN:
                raise ValueError(f"Entity {entity_id} does not belong to {DOMAIN}")

            handle = cfg_entry.runtime_data.handle
            coordinator = cfg_entry.runtime_data.coordinator

            if start_mode == "Zero start":
                output = 0.0
            elif start_mode == "Last known value":
                output = handle.last_known_output or 0.0
            elif start_mode == "Startup value":
                output = handle.get_number("starting_output") or 0.0
            else:
                output = value

            handle.pid.reset()
            handle.pid.set_auto_mode(True, output)
            handle.last_known_output = output
            if coordinator:
                coordinator.async_set_updated_data(output)

        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_OUTPUT,
            async_set_output,
            schema=vol.All(
                vol.Schema(
                    {
                        vol.Required("entity_id"): cv.entity_id,
                        vol.Optional("start_mode"): vol.In(START_MODE_OPTIONS),
                        vol.Optional("value"): vol.Coerce(float),
                    }
                ),
                cv.has_at_least_one_key("start_mode", "value"),
            ),
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # reset runtime_data zodat tests slagen
        entry.runtime_data = None
        if not hass.config_entries.async_entries(DOMAIN):
            hass.services.async_remove(DOMAIN, SERVICE_SET_OUTPUT)
    return unload_ok


async def _async_update_options_listener(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Update after options are changed in optionsflow"""
    await hass.config_entries.async_reload(entry.entry_id)
