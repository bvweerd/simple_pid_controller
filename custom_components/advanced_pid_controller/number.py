from homeassistant.components.number import RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import Entity

from .const import DOMAIN

PID_NUMBER_SETTINGS = [
    {
        "name": "Setpoint",
        "key": "setpoint",
        "icon": "mdi:target-variant",
        "unit": "units",  # pas aan op je toepassing
        "precision": 0.1,
        "min": 0.0,
        "max": 100.0,
        "default": 20.0,
    },
    {
        "name": "Kp",
        "key": "kp",
        "icon": "mdi:alpha-k-box",
        "unit": "",
        "precision": 0.01,
        "min": 0.0,
        "max": 10.0,
        "default": 1.0,
    },
    {
        "name": "Ki",
        "key": "ki",
        "icon": "mdi:alpha-i-box",
        "unit": "",
        "precision": 0.01,
        "min": 0.0,
        "max": 10.0,
        "default": 0.0,
    },
    {
        "name": "Kd",
        "key": "kd",
        "icon": "mdi:alpha-d-box",
        "unit": "",
        "precision": 0.01,
        "min": 0.0,
        "max": 10.0,
        "default": 0.0,
    },
    {
        "name": "Output Min",
        "key": "output_min",
        "icon": "mdi:arrow-down",
        "unit": "",
        "precision": 0.1,
        "min": -100.0,
        "max": 0.0,
        "default": -10.0,
    },
    {
        "name": "Output Max",
        "key": "output_max",
        "icon": "mdi:arrow-up",
        "unit": "",
        "precision": 0.1,
        "min": 0.0,
        "max": 100.0,
        "default": 10.0,
    },
    {
        "name": "Sample Time",
        "key": "sample_time",
        "icon": "mdi:clock-outline",
        "unit": "s",
        "precision": 0.1,
        "min": 0.1,
        "max": 60.0,
        "default": 1.0,
    },
]

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities for PID controller settings."""
    name = entry.data.get("name", "PID Controller")
    entities = [
        PIDNumberEntity(entry.entry_id, name, setting)
        for setting in PID_NUMBER_SETTINGS
    ]
    async_add_entities(entities)


class PIDNumberEntity(RestoreNumber):
    """A PID controller setting represented as a number entity."""

    def __init__(self, entry_id: str, base_name: str, setting: dict) -> None:
        self._entry_id = entry_id
        self._key = setting["key"]
        self._attr_name = f"{base_name} {setting['name']}"
        self._attr_unique_id = f"{entry_id}_{self._key}"
        self._attr_icon = setting.get("icon")
        self._attr_native_unit_of_measurement = setting.get("unit")
        self._attr_native_min_value = setting.get("min")
        self._attr_native_max_value = setting.get("max")
        self._attr_native_step = setting.get("precision")
        self._value = setting.get("default")

    @property
    def native_value(self) -> float:
        return self._value

    async def async_set_native_value(self, value: float) -> None:
        self._value = value
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Restore previous value if available."""
        await super().async_added_to_hass()
        if (last := await self.async_get_last_number_data()) is not None:
            self._value = last.native_value
