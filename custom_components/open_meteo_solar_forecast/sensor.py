"""Support for the Open-Meteo Solar Forecast sensor service."""

from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_utc_time_change
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from open_meteo_solar_forecast.models import Estimate

from .const import ATTR_WATTS, ATTR_WH_PERIOD, DOMAIN
from .coordinator import OpenMeteoSolarForecastDataUpdateCoordinator


@dataclass(frozen=True)
class OpenMeteoSolarForecastSensorEntityDescription(SensorEntityDescription):
    """Describes a Forecast.Solar Sensor."""

    state: Callable[[Estimate], Any] | None = None


SENSORS: tuple[OpenMeteoSolarForecastSensorEntityDescription, ...] = (
    OpenMeteoSolarForecastSensorEntityDescription(
        key="power_now",
        name="Power production now",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        state=lambda data: int(data.power_production_now),
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="energy_today",
        name="Energy production today",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        state=lambda data: int(data.energy_production_today),
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="energy_today_remaining",
        name="Energy production today remaining",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        state=lambda data: int(data.energy_production_today_remaining),
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="energy_tomorrow",
        name="Energy production tomorrow",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        state=lambda data: int(data.energy_production_tomorrow),
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="energy_current_hour",
        name="Energy current hour",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        state=lambda data: int(data.energy_current_hour),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Open-Meteo Solar Forecast sensor entries."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for description in SENSORS:
        entity = OpenMeteoSolarForecastSensor(
            entry_id=entry.entry_id,
            coordinator=coordinator,
            entity_description=description,
        )
        entities.append(entity)

    # Ajout du capteur de débogage de nébulosité
    entities.append(
        OpenMeteoSolarCloudCoverDebugSensor(
            entry_id=entry.entry_id,
            coordinator=coordinator,
        )
    )

    async_add_entities(entities)


class OpenMeteoSolarForecastSensor(CoordinatorEntity[OpenMeteoSolarForecastDataUpdateCoordinator], SensorEntity):
    """Representation of an Open-Meteo Solar Forecast sensor."""

    entity_description: OpenMeteoSolarForecastSensorEntityDescription

    def __init__(
        self,
        *,
        entry_id: str,
        coordinator: OpenMeteoSolarForecastDataUpdateCoordinator,
        entity_description: OpenMeteoSolarForecastSensorEntityDescription,
    ) -> None:
        """Initialize Open-Meteo Solar sensor."""
        super().__init__(coordinator=coordinator)
        self.entity_description = entity_description
        self.entity_id = f"{SENSOR_DOMAIN}.{entity_description.key}"
        self._attr_unique_id = f"{entry_id}_{entity_description.key}"

        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry_id)},
            manufacturer="Open-Meteo",
            name="Solar production forecast",
            configuration_url="https://open-meteo.com",
        )

    async def _update_callback(self, now: datetime) -> None:
        """Update the entity without fetching data from server."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> StateType:
        """Return the state of the entity."""
        if not self.coordinator.data:
            return None

        if self.entity_description.state:
            return self.entity_description.state(self.coordinator.data)

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}

        attrs = {}

        if self.entity_description.key == "power_now":
            attrs[ATTR_WATTS] = {
                watt_datetime.isoformat(): watt_value
                for watt_datetime, watt_value in self.coordinator.data.watts.items()
            }

        if self.entity_description.key in [
            "energy_today",
            "energy_tomorrow",
            "energy_current_hour",
        ]:
            attrs[ATTR_WH_PERIOD] = {
                wh_datetime.isoformat(): wh_value
                for wh_datetime, wh_value in self.coordinator.data.wh_period.items()
            }

        # Ajouter les informations d'ajustement de nébulosité pour tous les capteurs
        if hasattr(self.coordinator, "adjustment_stats"):
            attrs["cloud_cover_adjustment"] = self.coordinator.adjustment_stats

        return attrs


class OpenMeteoSolarCloudCoverDebugSensor(CoordinatorEntity[OpenMeteoSolarForecastDataUpdateCoordinator], SensorEntity):
    """Capteur de débogage pour les ajustements de nébulosité."""

    def __init__(
        self,
        *,
        entry_id: str,
        coordinator: OpenMeteoSolarForecastDataUpdateCoordinator,
    ) -> None:
        """Initialize the debug sensor."""
        super().__init__(coordinator=coordinator)
        self._attr_name = "Solar Forecast Cloud Cover Debug"
        self.entity_id = f"{SENSOR_DOMAIN}.solar_forecast_cloud_debug"
        self._attr_unique_id = f"{entry_id}_cloud_debug"
        self._attr_should_poll = False
        self._attr_entity_registry_enabled_default = False  # Désactivé par défaut

        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry_id)},
            manufacturer="Open-Meteo",
            name="Solar production forecast",
            configuration_url="https://open-meteo.com",
        )

    @property
    def native_value(self) -> str:
        """Return a simple state value."""
        if hasattr(self.coordinator, "adjustment_stats"):
            adjustment = self.coordinator.adjustment_stats.get("adjustment_percentage", 0)
            return f"{adjustment:.1f}%"
        return "No data"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed debug attributes."""
        if not self.coordinator.data:
            return {"status": "No data available"}

        attrs = {}
        
        # Échantillon de valeurs watts avant/après ajustement
        if hasattr(self.coordinator, "original_values") and self.coordinator.original_values:
            # Prendre jusqu'à 5 points de données pour l'échantillon
            sample_watts = {}
            sample_wh_period = {}
            
            # Original values
            orig_watts = self.coordinator.original_values.get("watts", {})
            orig_wh = self.coordinator.original_values.get("wh_period", {})
            
            # Current values
            current_watts = {
                dt.isoformat(): val 
                for dt, val in self.coordinator.data.watts.items()
            }
            current_wh = {
                dt.isoformat(): val 
                for dt, val in self.coordinator.data.wh_period.items()
            }
            
            # Échantillon des 5 premières heures
            timestamps = list(orig_watts.keys())[:5]
            for ts in timestamps:
                orig_val = orig_watts.get(ts, 0)
                curr_val = current_watts.get(ts, 0)
                diff_pct = ((curr_val - orig_val) / orig_val * 100) if orig_val else 0
                
                sample_watts[ts] = {
                    "original": orig_val,
                    "adjusted": curr_val,
                    "difference_percent": f"{diff_pct:.1f}%"
                }
                
                if ts in orig_wh:
                    orig_val = orig_wh.get(ts, 0)
                    curr_val = current_wh.get(ts, 0)
                    diff_pct = ((curr_val - orig_val) / orig_val * 100) if orig_val else 0
                    
                    sample_wh_period[ts] = {
                        "original": orig_val,
                        "adjusted": curr_val,
                        "difference_percent": f"{diff_pct:.1f}%"
                    }
            
            attrs["sample_watts"] = sample_watts
            attrs["sample_wh_period"] = sample_wh_period
        
        # Informations d'ajustement
        if hasattr(self.coordinator, "adjustment_stats"):
            attrs["adjustment_stats"] = self.coordinator.adjustment_stats
            
        # Échantillon de données de nébulosité
        if hasattr(self.coordinator, "cloud_cover_data"):
            # Prendre les 24 premières heures pour l'affichage
            cloud_data = self.coordinator.cloud_cover_data[:24] if self.coordinator.cloud_cover_data else []
            
            hours = {}
            for i, cover in enumerate(cloud_data):
                # Formater l'heure
                hour_str = f"{i:02d}:00"
                # Calculer le facteur d'ajustement
                adjustment = 1.0 - (cover / 100.0 * 0.7)
                hours[hour_str] = {
                    "cloud_cover": f"{cover}%",
                    "adjustment_factor": f"{adjustment:.2f}"
                }
            
            attrs["hourly_cloud_cover"] = hours
            attrs["cloud_cover_formula"] = "adjustment = 1.0 - (cloud_cover_percent / 100 * 0.7)"
            
        return attrs