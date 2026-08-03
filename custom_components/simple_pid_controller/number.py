"""Number platform for PID Controller."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberMode, RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import BasePIDEntity
from .const import (
    CONF_INPUT_RANGE_MIN,
    CONF_INPUT_RANGE_MAX,
    CONF_OUTPUT_RANGE_MIN,
    CONF_OUTPUT_RANGE_MAX,
    CONF_STEP_PREFIX,
    DEFAULT_INPUT_RANGE_MIN,
    DEFAULT_INPUT_RANGE_MAX,
    DEFAULT_OUTPUT_RANGE_MIN,
    DEFAULT_OUTPUT_RANGE_MAX,
    DEFAULT_STEPS,
)

# Coordinator is used to centralize the data updates
PARALLEL_UPDATES = 0

_LOGGER = logging.getLogger(__name__)


PID_NUMBER_ENTITIES: list[dict[str, Any]] = [
    {
        "name": "Kp",
        "key": "kp",
        "unit": "",
        "min": -1000.0,
        "max": 1000.0,
        "step": 0.0001,
        "default": 1.0,
        "entity_category": EntityCategory.CONFIG,
    },
    {
        "name": "Ki",
        "key": "ki",
        "unit": "",
        "min": -1000.0,
        "max": 1000.0,
        "step": 0.0001,
        "default": 0.1,
        "entity_category": EntityCategory.CONFIG,
    },
    {
        "name": "Kd",
        "key": "kd",
        "unit": "",
        "min": -1000.0,
        "max": 1000.0,
        "step": 0.0001,
        "default": 0.05,
        "entity_category": EntityCategory.CONFIG,
    },
    {
        "name": "Sample Time",
        "key": "sample_time",
        "unit": "s",
        "min": 0.01,
        "max": 600.0,
        "step": 0.01,
        "default": 10.0,
        "entity_category": EntityCategory.CONFIG,
    },
]

CONTROL_NUMBER_ENTITIES: list[dict[str, Any]] = [
    {
        "name": "Setpoint",
        "key": "setpoint",
        "unit": "",
        "step": 0.01,
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
    {
        "name": "Startup Value",
        "key": "starting_output",
        "unit": "",
        "step": 1.0,
        "default": 0.0,
        "entity_category": EntityCategory.CONFIG,
    },
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(
        [PIDParameterNumber(hass, entry, desc) for desc in PID_NUMBER_ENTITIES]
    )

    async_add_entities(
        [ControlParameterNumber(hass, entry, desc) for desc in CONTROL_NUMBER_ENTITIES]
    )


class PIDParameterNumber(BasePIDEntity, RestoreNumber):
    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, desc: dict[str, Any]
    ) -> None:
        super().__init__(hass, entry, desc["key"], desc["name"])
        RestoreNumber.__init__(self)

        opts: dict[str, Any] = dict(entry.options or {})

        self._attr_icon = "mdi:ray-vertex"
        self._attr_mode = NumberMode.BOX
        self._attr_native_unit_of_measurement = desc["unit"]
        self._attr_native_min_value = desc["min"]
        self._attr_native_max_value = desc["max"]
        self._attr_native_step = opts.get(
            f"{CONF_STEP_PREFIX}{desc['key']}", DEFAULT_STEPS[desc["key"]]
        )
        self._attr_native_value = desc["default"]
        self._attr_entity_category = desc["entity_category"]

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # native_value is optional on the restored data: a previous run that
        # never produced a value stores None, and comparing that against the
        # limits raises TypeError.
        if (
            last := await self.async_get_last_number_data()
        ) is not None and last.native_value is not None:
            if last.native_value < self._attr_native_min_value:
                self._attr_native_value = self._attr_native_min_value
            elif last.native_value > self._attr_native_max_value:
                self._attr_native_value = self._attr_native_max_value
            else:
                self._attr_native_value = last.native_value

    @property
    def native_value(self) -> float | None:
        return self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()


class ControlParameterNumber(BasePIDEntity, RestoreNumber):
    """Number entity for PID control parameters."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, desc: dict[str, Any]
    ) -> None:
        super().__init__(hass, entry, desc["key"], desc["name"])
        RestoreNumber.__init__(self)

        self._attr_icon = "mdi:ray-vertex"
        self._attr_mode = NumberMode.BOX
        self._attr_native_unit_of_measurement = desc["unit"]
        self._attr_native_value = desc["default"]
        self._attr_entity_category = desc["entity_category"]
        self._key = desc["key"]

        # Compute range limits based on key
        opts: dict[str, Any] = dict(entry.options or {})
        data: dict[str, Any] = dict(entry.data or {})
        input_range_min = opts.get(
            CONF_INPUT_RANGE_MIN,
            data.get(CONF_INPUT_RANGE_MIN, DEFAULT_INPUT_RANGE_MIN),
        )
        input_range_max = opts.get(
            CONF_INPUT_RANGE_MAX,
            data.get(CONF_INPUT_RANGE_MAX, DEFAULT_INPUT_RANGE_MAX),
        )
        output_range_min = opts.get(
            CONF_OUTPUT_RANGE_MIN,
            data.get(CONF_OUTPUT_RANGE_MIN, DEFAULT_OUTPUT_RANGE_MIN),
        )
        output_range_max = opts.get(
            CONF_OUTPUT_RANGE_MAX,
            data.get(CONF_OUTPUT_RANGE_MAX, DEFAULT_OUTPUT_RANGE_MAX),
        )

        if self._key == "setpoint":
            min_val, max_val = input_range_min, input_range_max
        elif self._key == "starting_output":
            min_val, max_val = output_range_min, output_range_max
        elif self._key == "output_min":
            min_val, max_val = output_range_min, output_range_max
        elif self._key == "output_max":
            min_val, max_val = output_range_min, output_range_max
        else:
            _LOGGER.error(
                "Unknown PID key '%s'. Using default values: input_min=%s, input_max=%s, output_min=%s, output_max=%s",
                self._key,
                DEFAULT_INPUT_RANGE_MIN,
                DEFAULT_INPUT_RANGE_MAX,
                DEFAULT_OUTPUT_RANGE_MIN,
                DEFAULT_OUTPUT_RANGE_MAX,
            )
            min_val, max_val = DEFAULT_INPUT_RANGE_MIN, DEFAULT_INPUT_RANGE_MAX

        self._attr_native_min_value = min_val
        self._attr_native_max_value = max_val
        self._attr_native_step = opts.get(
            f"{CONF_STEP_PREFIX}{self._key}",
            DEFAULT_STEPS.get(self._key, desc.get("step", 1.0)),
        )

        # Initialize current value
        if self._key == "setpoint":
            self._attr_native_value = input_range_min + (
                input_range_max - input_range_min
            ) * float(desc["default"])
        elif self._key == "starting_output":
            self._attr_native_value = output_range_min + (
                output_range_max - output_range_min
            ) * float(desc["default"])
        elif self._key == "output_min":
            self._attr_native_value = output_range_min
        elif self._key == "output_max":
            self._attr_native_value = output_range_max
        else:
            _LOGGER.error("Unexpected error, unknown state in number.py")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # See PIDParameterNumber: a restored native_value of None cannot be
        # compared against the limits.
        if (
            last := await self.async_get_last_number_data()
        ) is not None and last.native_value is not None:
            if last.native_value < self._attr_native_min_value:
                self._attr_native_value = self._attr_native_min_value
            elif last.native_value > self._attr_native_max_value:
                self._attr_native_value = self._attr_native_max_value
            else:
                self._attr_native_value = last.native_value

    @property
    def native_value(self) -> float | None:
        return self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()
