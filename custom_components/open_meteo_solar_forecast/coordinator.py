"""DataUpdateCoordinator for the Open-Meteo Solar Forecast integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.aiohttp_client import async_get_clientsession  # noqa: F811
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator  # noqa: F811
from open_meteo_solar_forecast import Estimate, OpenMeteoSolarForecast

from .const import (
    CONF_AZIMUTH,
    CONF_BASE_URL,
    CONF_DAMPING_EVENING,
    CONF_DAMPING_MORNING,
    CONF_DECLINATION,
    CONF_EFFICIENCY_FACTOR,
    CONF_INVERTER_POWER,
    CONF_MODULES_POWER,
    DOMAIN,
    LOGGER,
)
from .exceptions import OpenMeteoSolarForecastUpdateFailed

class OpenMeteoSolarForecastDataUpdateCoordinator(DataUpdateCoordinator):
    """DataUpdateCoordinator for the Open-Meteo Solar Forecast integration."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        latitude = entry.data[CONF_LATITUDE]
        longitude = entry.data[CONF_LONGITUDE]
        
        if not (-90 <= float(latitude) <= 90) or not (-180 <= float(longitude) <= 180):
            raise ValueError("Invalid latitude or longitude values")

        self.forecast = OpenMeteoSolarForecast(
            api_key=entry.data.get(CONF_API_KEY),
            session=async_get_clientsession(hass),
            latitude=float(latitude),
            longitude=float(longitude),
            azimuth=entry.options[CONF_AZIMUTH] - 180,
            base_url=entry.options[CONF_BASE_URL],
            ac_kwp=entry.options[CONF_INVERTER_POWER],
            dc_kwp=(entry.options[CONF_MODULES_POWER] / 1000),
            declination=entry.options[CONF_DECLINATION],
            efficiency_factor=entry.options[CONF_EFFICIENCY_FACTOR],
            damping_morning=entry.options.get(CONF_DAMPING_MORNING, 0.0),
            damping_evening=entry.options.get(CONF_DAMPING_EVENING, 0.0),
            weather_model=entry.options.get("model", "best_match"),
        )

        update_interval = timedelta(minutes=30)

        super().__init__(hass, LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self) -> Estimate:
        """Fetch Open-Meteo Solar Forecast estimates."""
        try:
            # Fetch hourly cloud cover from open-meteo.com
            cloud_cover_data = await self._fetch_hourly_cloud_cover()
            
            # Adjust the forecast with cloud cover data
            estimate = await self.forecast.estimate(cloud_cover_data)

            LOGGER.debug("Received estimate data: %s", estimate)
            return estimate
        except Exception as error:
            LOGGER.error("Error fetching data: %s", error)
            raise OpenMeteoSolarForecastUpdateFailed(f"Error fetching data: {error}") from error

    async def _fetch_hourly_cloud_cover(self) -> list:
        """Fetch hourly cloud cover data from open-meteo.com."""
        latitude = round(float(self.forecast.latitude), 2)
        longitude = round(float(self.forecast.longitude), 2)

        LOGGER.debug("Fetching cloud cover data for latitude: %s, longitude: %s", latitude, longitude)
        
        # Example URL: https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&hourly=cloud_cover
        url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=cloud_cover"

        LOGGER.debug("Fetching cloud cover data from URL: %s", url)
        
        async with self.forecast.session.get(url) as response:
            if response.status != 200:
                response_text = await response.text()
                LOGGER.error("Failed to fetch cloud cover data: %s. Response: %s", response.status, response_text)
                raise Exception(f"Failed to fetch cloud cover data: {response.status}")
            
            data = await response.json()
            LOGGER.debug("Received cloud cover data: %s", data)
            
            cloud_cover_data = data.get("hourly", {}).get("cloud_cover", [])
            LOGGER.debug("Extracted cloud_cover data: %s", cloud_cover_data)
            return cloud_cover_data