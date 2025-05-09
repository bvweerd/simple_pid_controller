from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PIDDeviceHandle
from .const import DOMAIN

SWITCHES = [
    {"key": "auto_mode", "name": "Auto Mode", "icon": "mdi:autorenew"},
    {"key": "proportional_on_measurement", "name": "P On Measurement", "icon": "mdi:chart-bell-curve"},
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    handle: PIDDeviceHandle = hass.data[DOMAIN][entry.entry_id]
    name = handle.name
    switches = [PIDOptionSwitch(entry.entry_id, name, s["key"], s["name"], s["icon"]) for s in SWITCHES]
    async_add_entities(switches)


class PIDOptionSwitch(SwitchEntity):
    def __init__(self, entry_id, name, key, label, icon):
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_name = f"{name} {label}"
        self._attr_icon = icon
        self._state = True  # default
        self._entry_id = entry_id
        self._device_name = name
        self._key = key

    @property
    def is_on(self) -> bool:
        return self._state

    async def async_turn_on(self):
        self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self):
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
