from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity, DeviceInfo

from .const import DOMAIN
from . import PIDDeviceHandle


class BasePIDEntity(Entity):
    """Base entity for Simple PID Controller integration."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        key: str,
        name: str,
    ) -> None:
        """Initialize the base PID entity."""
        self.hass = hass
        self._entry = entry
        self._handle = PIDDeviceHandle(hass, entry)
        self._key = key

        # Common entity attributes
        self._attr_name = f"{name}"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=self._handle.name,
        )
