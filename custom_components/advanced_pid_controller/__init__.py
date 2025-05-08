"""The PID Controller integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_PLATFORMS: list[Platform] = [Platform.sensor, Platform.number]

# TODO Update entry annotation
async def async_setup_entry(hass: HomeAssistant, entry: AdvancedPIDControllerConfigEntry) -> bool:
    """Set up PID Controller from a config entry."""

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


# TODO Update entry annotation
async def async_unload_entry(hass: HomeAssistant, entry: AdvancedPIDControllerConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
