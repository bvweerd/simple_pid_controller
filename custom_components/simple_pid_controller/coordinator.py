"""Coordinator for Simple PID Controller."""

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PIDDataCoordinator(DataUpdateCoordinator[float]):
    """Coordinator scheduling PID updates."""

    def __init__(self, hass: HomeAssistant, name: str, update_method, interval: float = 10):
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{name}_coordinator",
            update_interval=timedelta(seconds=interval),
        )
        self.update_method = update_method

    async def _async_update_data(self) -> float:
        try:
            return await self.update_method()
        except Exception as err:
            raise UpdateFailed(f"PID update failed: {err}") from err
