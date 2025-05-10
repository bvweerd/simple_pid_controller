"""Switch platform for PID Controller."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory

from . import PIDDeviceHandle
from .const import DOMAIN

SWITCH_ENTITIES = [
    {"key": "auto_mode", "name": "Auto Mode"},
    {"key": "proportional_on_measurement", "name": "Proportional on Measurement"},
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    handle: PIDDeviceHandle = hass.data[DOMAIN][entry.entry_id]
    name = handle.name
    async_add_entities(
        [PIDOptionSwitch(entry.entry_id, name, desc) for desc in SWITCH_ENTITIES]
    )


class PIDOptionSwitch(SwitchEntity):
    def __init__(self, entry_id: str, device_name: str, desc: dict) -> None:
        self._entry_id = entry_id
        self._key = desc["key"]
        self._attr_name = f"{device_name} {desc['name']}"
        self._attr_unique_id = f"{entry_id}_{self._key}"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_entity_id = f"switch.{entry_id}_{self._key}"
        self._device_name = device_name
        self._state = True

    @property
    def is_on(self) -> bool:
        return self._state

    async def async_turn_on(self, **kwargs) -> None:
        self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self._state = False
        self.async_write_ha_state()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._device_name,
            "manufacturer": "Custom",
            "model": "Advanced PID Controller",
        }
