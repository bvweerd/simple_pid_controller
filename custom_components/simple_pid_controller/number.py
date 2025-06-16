"""Number platform for PID Controller."""

from __future__ import annotations

import logging

from homeassistant.components.number import RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory

from .entity import BasePIDEntity
from .const import (
    CONF_INPUT_RANGE_MIN,
    CONF_INPUT_RANGE_MAX,
    CONF_OUTPUT_RANGE_MIN,
    CONF_OUTPUT_RANGE_MAX,
    DEFAULT_INPUT_RANGE_MIN,
    DEFAULT_INPUT_RANGE_MAX,
    DEFAULT_OUTPUT_RANGE_MIN,
    DEFAULT_OUTPUT_RANGE_MAX,
)

# Coordinator is used to centralize the data updates
PARALLEL_UPDATES = 0

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
    entities = [PIDParameterNumber(hass, entry, desc) for desc in PID_NUMBER_ENTITIES]
    async_add_entities(entities)

    entities = [
        ControlParameterNumber(hass, entry, desc) for desc in CONTROL_NUMBER_ENTITIES
    ]
    async_add_entities(entities)


class PIDParameterNumber(RestoreNumber):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, desc: dict) -> None:
        BasePIDEntity.__init__(self, hass, entry, desc["key"], desc["name"])
        RestoreNumber.__init__(self)

        self._attr_icon = "mdi:ray-vertex"
        self._attr_mode = "box"
        self._attr_native_unit_of_measurement = desc["unit"]
        self._attr_native_min_value = desc["min"]
        self._attr_native_max_value = desc["max"]
        self._attr_native_step = desc["step"]
        self._attr_native_value = desc["default"]
        self._attr_entity_category = desc["entity_category"]

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_number_data()) is not None:
            if last.native_value < self._attr_native_min_value:
                self._attr_native_value = self._attr_native_min_value
            elif last.native_value > self._attr_native_max_value:
                self._attr_native_value = self._attr_native_max_value
            else:
                self._attr_native_value = last.native_value

    @property
    def native_value(self) -> float:
        return self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()


class ControlParameterNumber(RestoreNumber):
    """Number entity for PID control parameters."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, desc: dict) -> None:
        BasePIDEntity.__init__(self, hass, entry, desc["key"], desc["name"])
        RestoreNumber.__init__(self)

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
        input_range_min = opts.get(
            CONF_INPUT_RANGE_MIN, data.get(CONF_INPUT_RANGE_MIN, DEFAULT_INPUT_RANGE_MIN)
        )
        input_range_max = opts.get(
            CONF_INPUT_RANGE_MAX, data.get(CONF_INPUT_RANGE_MAX, DEFAULT_INPUT_RANGE_MAX)
        )
        output_range_min = opts.get(
            CONF_INPUT_RANGE_MIN, data.get(CONF_OUTPUT_RANGE_MIN, DEFAULT_OUTPUT_RANGE_MIN)
        )
        output_range_max = opts.get(
            CONF_OUTPUT_RANGE_MAX, data.get(CONF_OUTPUT_RANGE_MAX, DEFAULT_OUTPUT_RANGE_MAX)
        )

        if self._key == "setpoint":
            min_val, max_val = input_range_min, input_range_max
        elif self._key == "output_min":
            min_val, max_val = -abs(output_range_max), output_range_min
        elif self._key == "output_max":
            min_val, max_val = output_range_min, output_range_max
        else:
            _LOGGER.error("Unexpected PID parameter key: %s", self._key)
            input_min_val, input_max_val, output_min_val, output_max_val = DEFAULT_INPUT_RANGE_MIN, INPUT_DEFAULT_RANGE_MAX, DEFAULT_OUTPUT_RANGE_MIN, OUTPUT_DEFAULT_RANGE_MAX

        self._attr_native_min_value = min_val
        self._attr_native_max_value = max_val
        self._attr_native_step = desc.get("step", 1.0)

        # Initialize current value
        if self._key == "setpoint":
            self._attr_native_value = input_range_min + (input_range_max - input_range_min) * float(
                desc["default"]
            )
        elif self._key == "output_min":
            self._attr_native_value = output_range_min
        elif self._key == "output_max":
            self._attr_native_value = output_range_max
        else:
            _LOGGER.error("Unexpected error, unknown state in number.py")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_number_data()) is not None:
            if last.native_value < self._attr_native_min_value:
                self._attr_native_value = self._attr_native_min_value
            elif last.native_value > self._attr_native_max_value:
                self._attr_native_value = self._attr_native_max_value
            else:
                self._attr_native_value = last.native_value

    @property
    def native_value(self) -> float:
        return self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()
