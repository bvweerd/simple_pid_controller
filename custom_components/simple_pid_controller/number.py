"""Number platform for PID Controller."""

from __future__ import annotations

from homeassistant.components.number import RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory

from . import PIDDeviceHandle
from .const import DOMAIN

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
        "name": "Setpoint",
        "key": "setpoint",
        "unit": "%",
        "min": 0.0,
        "max": 100.0,
        "step": 1.0,
        "default": 50.0,
        "entity_category": None,
    },
    {
        "name": "Output Min",
        "key": "output_min",
        "unit": "",
        "min": -100.0,
        "max": 0.0,
        "step": 1.0,
        "default": -10.0,
        "entity_category": EntityCategory.CONFIG,
    },
    {
        "name": "Output Max",
        "key": "output_max",
        "unit": "",
        "min": 0.0,
        "max": 100.0,
        "step": 1.0,
        "default": 10.0,
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


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    handle: PIDDeviceHandle = hass.data[DOMAIN][entry.entry_id]
    name = handle.name
    entities = [PIDParameterNumber(entry, name, desc) for desc in PID_NUMBER_ENTITIES]
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
