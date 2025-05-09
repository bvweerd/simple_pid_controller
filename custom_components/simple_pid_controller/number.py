"""Number platform for Simple PID Controller."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PIDDeviceHandle
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PID_NUMBER_ENTITIES = [
    {"name": "Kp", "key": "kp", "icon": "mdi:alpha-k-circle-outline", "unit": "", "min": 0.0, "max": 10.0, "step": 0.01, "default": 1.0},
    {"name": "Ki", "key": "ki", "icon": "mdi:alpha-i-circle-outline", "unit": "", "min": 0.0, "max": 10.0, "step": 0.01, "default": 0.1},
    {"name": "Kd", "key": "kd", "icon": "mdi:alpha-d-circle-outline", "unit": "", "min": 0.0, "max": 10.0, "step": 0.01, "default": 0.05},
    {"name": "Setpoint", "key": "setpoint", "icon": "mdi:target-variant", "unit": "%", "min": 0.0, "max": 100.0, "step": 1.0, "default": 50.0},
    {"name": "Output Min", "key": "output_min", "icon": "mdi:arrow-down-bold", "unit": "", "min": -100.0, "max": 0.0, "step": 1.0, "default": -10.0},
    {"name": "Output Max", "key": "output_max", "icon": "mdi:arrow-up-bold", "unit": "", "min": 0.0, "max": 100.0, "step": 1.0, "default": 10.0},
    {"name": "Sample Time", "key": "sample_time", "icon": "mdi:timer-outline", "unit": "s", "min": 0.01, "max": 60.0, "step": 0.01, "default": 10.0},
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities from config entry."""
    handle: PIDDeviceHandle = hass.data[DOMAIN][entry.entry_id]
    name = handle.name

    entities = [PIDParameterNumber(entry.entry_id, name, desc) for desc in PID_NUMBER_ENTITIES]
    async_add_entities(entities)


class PIDParameterNumber(RestoreNumber):
    """Number entity for a PID parameter."""

    def __init__(self, entry_id: str, device_name: str, description: dict[str, Any]) -> None:
        self._entry_id = entry_id
        self._device_name = device_name
        self._key = description["key"]
        self._attr_name = f"{device_name} {description['name']}"
        self._attr_unique_id = f"{entry_id}_{self._key}"
        self._attr_icon = description["icon"]
        self._attr_native_unit_of_measurement = description["unit"]
        self._attr_native_min_value = description["min"]
        self._attr_native_max_value = description["max"]
        self._attr_native_step = description["step"]
        self._attr_native_value = description["default"]

    async def async_added_to_hass(self) -> None:
        """Restore last state if available."""
        await super().async_added_to_hass()
        if (last_val := await self.async_get_last_number_data()) is not None:
            self._attr_native_value = last_val.native_value

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        """Set a new value."""
        self._attr_native_value = value
        self.async_write_ha_state()

    @property
    def device_info(self):
        """Return device information for entity grouping."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._device_name,
            "manufacturer": "Custom",
            "model": "Simple PID Controller",
        }
