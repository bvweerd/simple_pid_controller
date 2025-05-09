# custom_components/advanced_pid_controller/number.py

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_SENSOR_ENTITY_ID

_LOGGER = logging.getLogger(__name__)

PID_NUMBER_ENTITIES = [
    {
        "name": "Kp",
        "key": "kp",
        "icon": "mdi:alpha-k-circle-outline",
        "unit": "",
        "min": 0.0,
        "max": 10.0,
        "step": 0.01,
        "default": 1.0,
    },
    {
        "name": "Ki",
        "key": "ki",
        "icon": "mdi:alpha-i-circle-outline",
        "unit": "",
        "min": 0.0,
        "max": 10.0,
        "step": 0.01,
        "default": 0.1,
    },
    {
        "name": "Kd",
        "key": "kd",
        "icon": "mdi:alpha-d-circle-outline",
        "unit": "",
        "min": 0.0,
        "max": 10.0,
        "step": 0.01,
        "default": 0.05,
    },
    {
        "name": "Setpoint",
        "key": "setpoint",
        "icon": "mdi:target-variant",
        "unit": "%",
        "min": 0.0,
        "max": 100.0,
        "step": 1.0,
        "default": 50.0,
    },
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities from config entry."""

    sensor_entity_id = entry.options.get(CONF_SENSOR_ENTITY_ID, entry.data.get(CONF_SENSOR_ENTITY_ID))

    entities = []
    for desc in PID_NUMBER_ENTITIES:
        entities.append(PIDParameterNumber(entry.entry_id, desc))

    async_add_entities(entities)


class PIDParameterNumber(RestoreNumber):
    """Number entity for PID parameter."""

    def __init__(self, entry_id: str, description: dict[str, Any]) -> None:
        """Initialize a PID number entity."""
        self._entry_id = entry_id
        self._attr_name = f"{entry_id} {description['name']}"
        self._attr_unique_id = f"{entry_id}_{description['key']}"
        self._attr_icon = description["icon"]
        self._attr_native_unit_of_measurement = description["unit"]
        self._attr_native_value = description["default"]
        self._attr_min_value = description["min"]
        self._attr_max_value = description["max"]
        self._attr_step = description["step"]
        self._key = description["key"]

    async def async_added_to_hass(self) -> None:
        """Restore last value if available."""
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
