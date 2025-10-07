"""Simple PID Controller integration."""

from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import entity_registry as er
from collections import deque
from dataclasses import dataclass
import re
from typing import Any

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from .coordinator import PIDDataCoordinator

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
ATTR_VALUE = "value"
ATTR_PRESET = "preset"
PRESET_OPTIONS = ["zero_start", "last_known_value", "startup_value"]

SET_OUTPUT_SCHEMA = cv.make_entity_service_schema(
    {
        vol.Optional(ATTR_ENTITY_ID): cv.entity_id,
        vol.Optional(ATTR_VALUE): vol.Coerce(float),
        vol.Optional(ATTR_PRESET): vol.In(PRESET_OPTIONS),
    }
)


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
        self.last_known_output = None

        self.input_history: deque[float] = deque(maxlen=10)
        self.output_history: deque[float] = deque(maxlen=10)
        self.pid_parameter_history: deque[dict[str, float | None]] = deque(maxlen=10)
        self.pid_contribution_history: deque[dict[str, float | None]] = deque(maxlen=10)
        self.sample_time_history: deque[float | None] = deque(maxlen=10)
        self.last_update_timestamp: float | None = None
        self.last_measured_sample_time: float | None = None

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

    def _coerce_float(self, value: Any) -> float | None:
        """Coerce a Home Assistant state or attribute value into a float."""
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None

            cleaned = stripped.replace(" ", "")

            # Support locales that use comma as decimal separator ("0,32").
            if "," in cleaned and cleaned.count(",") == 1 and "." not in cleaned:
                cleaned = cleaned.replace(",", ".")
            elif "," in cleaned and "." in cleaned:
                # If both comma and dot are present, treat the comma as a thousands
                # separator, mirroring Python's behaviour for underscores.
                cleaned = cleaned.replace(",", "")

            # Only allow digits plus an optional leading sign and decimal point.
            if not re.fullmatch(r"[+-]?(\d+(\.\d*)?|\.\d+)", cleaned):
                return None

            try:
                return float(cleaned)
            except ValueError:
                return None

        return None

    def get_input_sensor_value(self) -> float | None:
        """Return the input value from configured sensor."""
        state = self.hass.states.get(self.sensor_entity_id)
        if state and state.state not in ("unknown", "unavailable"):
            value = self._coerce_float(state.state)
            if value is not None:
                return value
            _LOGGER.warning(
                "Sensor %s invalid value '%s'. PID-calculation skipped.",
                self.sensor_entity_id,
                state.state,
            )
        return None

    def get_forecast_series(self) -> list[dict[str, Any]]:
        """Return forecast entries from the input sensor if available.

        The energy price integrations in Home Assistant expose a ``forecast``
        attribute that contains a list of dictionaries with at least a
        ``value``/``price`` entry.  Previously we ignored these entries and only
        used the current sensor value, causing every point of the planning
        horizon to use the same price.  This helper extracts all usable
        forecast values so other parts of the integration can consume them.
        """

        state = self.hass.states.get(self.sensor_entity_id)
        if state is None:
            return []

        raw_forecast = state.attributes.get("forecast")
        if not isinstance(raw_forecast, list):
            return []

        parsed: list[dict[str, Any]] = []
        for item in raw_forecast:
            if not isinstance(item, dict):
                continue

            # Electricity price sensors sometimes expose the price under
            # ``value`` while others use ``price``.  Accept both and ignore
            # unparseable entries so a single malformed datapoint does not
            # break the entire forecast.
            raw_value = item.get("value")
            if raw_value is None:
                raw_value = item.get("price")

            value = self._coerce_float(raw_value)
            if value is None:
                continue

            parsed.append({
                "datetime": item.get("datetime") or item.get("time"),
                "value": value,
            })

        return parsed


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

    if not hass.services.has_service(DOMAIN, SERVICE_SET_OUTPUT):

        async def async_set_output(call: ServiceCall) -> None:
            entity_id: str | list[str] | None = call.data.get(ATTR_ENTITY_ID)
            if entity_id is None:
                raise HomeAssistantError("entity_id is required")
            if isinstance(entity_id, list):
                if len(entity_id) != 1:
                    raise HomeAssistantError("Exactly one entity_id is required")
                entity_id = entity_id[0]
            preset: str | None = call.data.get(ATTR_PRESET)
            value: float | None = call.data.get(ATTR_VALUE)

            registry = er.async_get(hass)
            ent = registry.async_get(entity_id)
            if ent is None:
                raise HomeAssistantError(f"Unknown entity {entity_id}")
            config_entry = hass.config_entries.async_get_entry(ent.config_entry_id)
            if config_entry is None or config_entry.runtime_data is None:
                raise HomeAssistantError("PID controller not loaded")
            dev_handle: PIDDeviceHandle = config_entry.runtime_data.handle
            out_min = dev_handle.get_number("output_min") or 0.0
            out_max = dev_handle.get_number("output_max") or 0.0

            if (preset is None and value is None) or (
                preset is not None and value is not None
            ):
                raise HomeAssistantError("Either preset or value required")

            if preset is not None:
                if preset == "zero_start":
                    target = 0.0
                elif preset == "last_known_value":
                    target = dev_handle.last_known_output or 0.0
                elif preset == "startup_value":
                    target = dev_handle.get_number("starting_output") or 0.0
                else:
                    raise HomeAssistantError("Invalid preset")
            else:
                target = value
                if target is None:
                    raise HomeAssistantError("Value required")
                if target < out_min or target > out_max:
                    raise HomeAssistantError(
                        f"Value {target} out of range {out_min}-{out_max}"
                    )

            dev_handle.last_known_output = target
            coordinator: PIDDataCoordinator = config_entry.runtime_data.coordinator
            if dev_handle.pid.auto_mode:
                dev_handle.pid.set_auto_mode(False)
                dev_handle.pid.set_auto_mode(True, target)
                coordinator.async_set_updated_data(target)
                await coordinator.async_request_refresh()
            else:
                coordinator.async_set_updated_data(target)
                # Update the internal PID output when in manual mode so that
                # future calls to the controller return the newly set target.
                dev_handle.pid._last_output = target

        hass.services.async_register(
            DOMAIN, SERVICE_SET_OUTPUT, async_set_output, schema=SET_OUTPUT_SCHEMA
        )

    # register updatelistener for optionsflow
    entry.async_on_unload(entry.add_update_listener(_async_update_options_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
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
