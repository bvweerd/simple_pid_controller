"""Switch platform for Simple PID Controller."""

from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory

from . import PIDDeviceHandle
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SWITCH_ENTITIES = [
    {"key": "auto_mode", "name": "Auto Mode", "icon": "mdi:autorenew"},
    {"key": "proportional_on_measurement", "name": "P on Measurement", "icon": "mdi:chart-bell-curve"},
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities from config entry."""
    handle: PIDDeviceHandle = hass.data[DOMAIN][entry.entry_id]
    name = handle.name

    entities = [PIDOptionSwitch(entry.entry_id, name, desc) for desc in SWITCH_ENTITIES]
    async_add_entities(entities)


class PIDOptionSwitch(SwitchEntity):
    """Switch entity for a PID option."""

    def __init__(self, entry_id: str, device_name: str, description: dict) -> None:
        self._entry_id = entry_id
        self._device_name = device_name
        self._key = description["key"]
        self._attr_name = f"{device_name} {description['name']}"
        self._attr_unique_id = f"{entry_id}_{self._key}"
        self._attr_icon = description["icon"]
        self._attr_entity_category = EntityCategory.CONFIG
        self._state = True

    @property
    def is_on(self) -> bool:
        """Return switch state."""
        return self._state

    async def async_turn_on(self, **kwargs) -> None:
        """Turn switch on."""
        self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn switch off."""
        self._state = False
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
