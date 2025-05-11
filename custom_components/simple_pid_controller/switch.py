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
        [PIDOptionSwitch(entry, name, desc) for desc in SWITCH_ENTITIES]
    )


class PIDOptionSwitch(SwitchEntity):
    def __init__(self, entry: ConfigEntry, device_name: str, desc: dict) -> None:
        self._entry = entry
        self._attr_name = f"{desc['name']}"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{entry.entry_id}_{desc['key']}"
        self._attr_entity_category = EntityCategory.CONFIG
        self._state = True
        self._device_name = entry.entry_id

        # Device-info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.entry_id,
            "manufacturer": "N/A",
            "model": "Simple PID Controller",
        }
        
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
            "manufacturer": "N/A",
            "model": "Simple PID Controller",
        }