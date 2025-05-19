"""Number platform for PID Controller."""

from __future__ import annotations

import logging

from homeassistant.components.number import RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
from . import PIDDeviceHandle

from .const import (
    DOMAIN,
    CONF_RANGE_MIN,
    CONF_RANGE_MAX,
    DEFAULT_RANGE_MIN,
    DEFAULT_RANGE_MAX,
)

_LOGGER = logging.getLogger(__name__)


PID_NUMBER_ENTITIES = [
    {
        "name": "Kp",
        "key": "kp",
        "unit": "",
        "min": 0.0,
        "max": 10.0,
        "step": 0.01,
        "default": 1.0,
        "entity_category": EntityCategory.CONFIG,
    },
    {
        "name": "Ki",
        "key": "ki",
        "unit": "",
        "min": 0.0,
        "max": 10.0,
        "step": 0.01,
        "default": 0.1,
        "entity_category": EntityCategory.CONFIG,
    },
    {
        "name": "Kd",
        "key": "kd",
        "unit": "",
        "min": 0.0,
        "max": 10.0,
        "step": 0.01,
        "default": 0.05,
        "entity_category": EntityCategory.CONFIG,
    },
    {
        "name": "Sample Time",
        "key": "sample_time",
        "unit": "s",
        "min": 0.01,
        "max": 60.0,
        "step": 0.01,
        "default": 10.0,
        "entity_category": EntityCategory.CONFIG,
    },
]

CONTROL_NUMBER_ENTITIES = [
    {
        "name": "Setpoint",
        "key": "setpoint",
        "unit": "",
        "step": 1.0,
        "default": 0.5,
        "entity_category": None,
    },
    {
        "name": "Output Min",
        "key": "output_min",
        "unit": "",
        "step": 1.0,
        "default": 0,
        "entity_category": EntityCategory.CONFIG,
    },
    {
        "name": "Output Max",
        "key": "output_max",
        "unit": "",
        "step": 1.0,
        "default": 1,
        "entity_category": EntityCategory.CONFIG,
    },
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    handle: PIDDeviceHandle = hass.data[DOMAIN][entry.entry_id]
    name = handle.name

    entities = [PIDParameterNumber(entry, name, desc) for desc in PID_NUMBER_ENTITIES]
    async_add_entities(entities)

    entities = [
        ControlParameterNumber(entry, name, desc) for desc in CONTROL_NUMBER_ENTITIES
    ]
    async_add_entities(entities)


class PIDParameterNumber(RestoreNumber):
    def __init__(self, entry: ConfigEntry, device_name: str, desc: dict) -> None:
        self._attr_name = f"{desc['name']}"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{entry.entry_id}_{desc['key']}"
        self._attr_icon = "mdi:ray-vertex"
        self._attr_mode = "box"
        self._attr_native_unit_of_measurement = desc["unit"]
        self._attr_native_min_value = desc["min"]
        self._attr_native_max_value = desc["max"]
        self._attr_native_step = desc["step"]
        self._attr_native_value = desc["default"]
        self._attr_entity_category = desc["entity_category"]

        # Device-info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": device_name,
        }

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_number_data()) is not None:
            self._attr_native_value = last.native_value

    @property
    def native_value(self) -> float:
        return self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()


class ControlParameterNumber(RestoreNumber):
    """Number entity for PID control parameters."""

    def __init__(self, entry: ConfigEntry, device_name: str, desc: dict) -> None:
        self._attr_name = f"{desc['name']}"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{entry.entry_id}_{desc['key']}"
        self._attr_icon = "mdi:ray-vertex"
        self._attr_mode = "box"
        self._attr_native_unit_of_measurement = desc["unit"]
        self._attr_native_step = desc["step"]
        self._attr_native_value = desc["default"]
        self._attr_entity_category = desc["entity_category"]
        self._key = desc["key"]

        # Compute range limits based on key
        opts = entry.options or {}
        data = entry.data or {}
        range_min = opts.get(
            CONF_RANGE_MIN, data.get(CONF_RANGE_MIN, DEFAULT_RANGE_MIN)
        )
        range_max = opts.get(
            CONF_RANGE_MAX, data.get(CONF_RANGE_MAX, DEFAULT_RANGE_MAX)
        )

        if self._key == "setpoint":
            min_val, max_val = range_min, range_max
        elif self._key == "output_min":
            min_val, max_val = -abs(range_max), 0.0
        elif self._key == "output_max":
            min_val, max_val = 0.0, range_max
        else:
            _LOGGER.error("Unexpected PID parameter key: %s", self._key)
            min_val, max_val = DEFAULT_RANGE_MIN, DEFAULT_RANGE_MAX

        self._attr_native_min_value = min_val
        self._attr_native_max_value = max_val
        self._attr_native_step = desc.get("step", 1.0)

        # Initialize current value
        self._attr_native_value = self._key

        if self._key == "setpoint":
            self._attr_native_value = range_min + (range_max + range_min) * float(
                desc["default"]
            )
        elif self._key == "output_min":
            self._attr_native_value = range_min
        elif self._key == "output_max":
            self._attr_native_value = range_max
        else:
            _LOGGER.error("Unexpected error, unknown state in number.py")

        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": device_name,
        }

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_number_data()) is not None:
            self._attr_native_value = last.native_value

    @property
    def native_value(self) -> float:
        return self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()
