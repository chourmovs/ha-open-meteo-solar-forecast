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
    CONF_API_KEY,  # noqa: F811
    CONF_LATITUDE,  # noqa: F811
    CONF_LONGITUDE,  # noqa: F811
)
from .exceptions import OpenMeteoSolarForecastUpdateFailed
from openmeteo_requests import Client
import requests_cache
from retry_requests import retry
import pandas as pd  # noqa: F401

class OpenMeteoSolarForecastDataUpdateCoordinator(DataUpdateCoordinator):
    """DataUpdateCoordinator for the Open-Meteo Solar Forecast integration."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        # Setup the Open-Meteo API client with cache and retry on error
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.openmeteo = Client(session=retry_session)

        self.forecast = OpenMeteoSolarForecast(
            api_key=entry.data.get(CONF_API_KEY),
            session=async_get_clientsession(hass),
            latitude=entry.data[CONF_LATITUDE],
            longitude=entry.data[CONF_LONGITUDE],
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
            # Log the parameters for the API call
            LOGGER.debug("Fetching hourly cloud cover data with parameters: %s", {
                "latitude": self.forecast.latitude,
                "longitude": self.forecast.longitude,
                "hourly": "cloud_cover"
            })

            # Fetch hourly cloud cover data
            cloud_cover_data = await self._fetch_hourly_cloud_cover()

            # Log the cloud cover data
            LOGGER.debug("Received hourly cloud cover data: %s", cloud_cover_data)

            # Adjust the forecast with cloud cover data
            estimate = await self.forecast.estimate(cloud_cover_data)

            # Log the final estimate data
            LOGGER.debug("Received estimate data: %s", estimate)
            return estimate
        except Exception as error:
            LOGGER.error("Error fetching data: %s", error)
            raise OpenMeteoSolarForecastUpdateFailed(f"Error fetching data: {error}") from error

    async def _fetch_hourly_cloud_cover(self) -> dict:
        """Fetch hourly cloud cover data from open-meteo.com."""
        url = f"https://api.open-meteo.com/v1/forecast?latitude={self.forecast.latitude}&longitude={self.forecast.longitude}&hourly=cloud_cover"
        response = await self.openmeteo.weather_api(url, params={"latitude": self.forecast.latitude, "longitude": self.forecast.longitude, "hourly": "cloud_cover"})
        response = response[0]
        hourly = response.Hourly()
        hourly_cloud_cover = hourly.Variables(0).ValuesAsNumpy()

        # Log the response details
        LOGGER.debug("Open-Meteo API response details: %s", {
            "Coordinates": f"{response.Latitude()}°N {response.Longitude()}°E",
            "Elevation": f"{response.Elevation()} m asl",
            "Timezone": f"{response.Timezone()}{response.TimezoneAbbreviation()}",
            "Timezone difference to GMT+0": f"{response.UtcOffsetSeconds()} s",
            "Hourly cloud cover data": hourly_cloud_cover
        })

        return hourly_cloud_cover
