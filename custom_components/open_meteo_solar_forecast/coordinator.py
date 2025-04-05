"""DataUpdateCoordinator for the Open-Meteo Solar Forecast integration."""
from __future__ import annotations

from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
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
    CONF_MODEL,
    DOMAIN,
    LOGGER,
)
from .exceptions import OpenMeteoSolarForecastUpdateFailed

def clean_value(value) -> float:
    """Convertit robustement n'importe quel format de coordonnées en float."""
    try:
        # Gère les listes, strings avec crochets et autres formats
        if isinstance(value, (list, tuple)):
            value = value[0]
        return round(float(str(value).strip('[]')), 6)
    except (TypeError, ValueError, IndexError) as err:
        LOGGER.error("Erreur de conversion GPS : %s", err)
        raise ValueError(f"Coordonnée invalide : {value}") from err

class OpenMeteoSolarForecastDataUpdateCoordinator(DataUpdateCoordinator[Estimate]):
    """Coordinateur de mise à jour des données solaires."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialisation du coordinateur."""
        self.config_entry = entry
        
        api_key = entry.options.get(CONF_API_KEY) or None
        ac_kwp = entry.options.get(CONF_INVERTER_POWER, 0) / 1000

        # Validation et nettoyage des coordonnées
        latitude = clean_value(entry.data[CONF_LATITUDE])
        longitude = clean_value(entry.data[CONF_LONGITUDE])
        
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            raise ValueError("Coordonnées GPS invalides")

        # Configuration du client Open-Meteo
        self.forecast = OpenMeteoSolarForecast(
            api_key=api_key,
            session=async_get_clientsession(hass),
            latitude=latitude,
            longitude=longitude,
            azimuth=entry.options[CONF_AZIMUTH] - 180,
            base_url=entry.options[CONF_BASE_URL],
            ac_kwp=ac_kwp,
            dc_kwp=entry.options[CONF_MODULES_POWER] / 1000,
            declination=entry.options[CONF_DECLINATION],
            efficiency_factor=entry.options[CONF_EFFICIENCY_FACTOR],
            damping_morning=entry.options.get(CONF_DAMPING_MORNING, 0.0),
            damping_evening=entry.options.get(CONF_DAMPING_EVENING, 0.0),
            weather_model=entry.options.get(CONF_MODEL, "best_match"),
        )

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=30)
        )

    async def _async_update_data(self) -> Estimate:
        """Mise à jour des données avec intégration de la nébulosité."""
        try:
            # Récupération des données de nébulosité
            cloud_data = await self._fetch_cloud_cover()
            
            # Mise à jour de l'estimation avec les nouvelles données
            estimate = await self.forecast.estimate()
            
            # Intégration manuelle des données de nébulosité
            self._apply_cloud_adjustments(estimate, cloud_data)
            
            return estimate
            
        except Exception as err:
            LOGGER.error("Erreur de mise à jour : %s", err, exc_info=True)
            raise OpenMeteoSolarForecastUpdateFailed(f"Erreur : {err}") from err

    async def _fetch_cloud_cover(self) -> list[float]:
        """Récupère les données de couverture nuageuse avec validation finale."""
        # Extraction sécurisée des valeurs numériques
        lat = self.forecast.latitude
        lon = self.forecast.longitude
        
        # Validation de type redondante
        if isinstance(lat, (list, tuple)):
            lat = lat[0]
            LOGGER.warning("Latitude corrigée (liste -> float) : %s", lat)
            
        url = (
            f"{self.forecast.base_url}/v1/forecast?"
            f"latitude={float(lat):.6f}&"
            f"longitude={float(lon):.6f}&"
            "hourly=cloud_cover"
        )

    def _apply_cloud_adjustments(self, estimate: Estimate, cloud_data: list[float]) -> None:
        """Application manuelle des ajustements liés à la nébulosité."""
        if cloud_data:
            adjustment_factor = 1 - sum(cloud_data) / (len(cloud_data) * 100)
            estimate.energy_production_today *= adjustment_factor
            estimate.energy_production_tomorrow *= adjustment_factor
            LOGGER.debug("Ajustement appliqué avec facteur : %.2f", adjustment_factor)