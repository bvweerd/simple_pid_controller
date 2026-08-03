from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity, DeviceInfo

from .const import DOMAIN

if TYPE_CHECKING:
    from . import PIDDeviceHandle


class BasePIDEntity(Entity):
    """Base entity for Simple PID Controller integration."""

    # Declared at class level so every subclass carries them: the platform
    # entities mix this class in alongside the Home Assistant entity bases,
    # and without these declarations self._handle is invisible to the type
    # checker in all of them.
    _entry: ConfigEntry
    _handle: PIDDeviceHandle
    _key: str

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
        self._handle = entry.runtime_data.handle
        self._key = key

        # Common entity attributes
        self._attr_name = f"{name}"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=self._handle.name,
        )
