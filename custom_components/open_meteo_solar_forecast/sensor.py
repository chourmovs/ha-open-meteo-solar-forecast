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
        key="energy_production_today",
        translation_key="energy_production_today",
        state=lambda estimate: estimate.energy_production_today,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=1,
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="energy_production_today_remaining",
        translation_key="energy_production_today_remaining",
        state=lambda estimate: estimate.energy_production_today_remaining,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=1,
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="energy_production_tomorrow",
        translation_key="energy_production_tomorrow",
        state=lambda estimate: estimate.energy_production_tomorrow,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=1,
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="energy_production_d2",
        translation_key="energy_production_d2",
        state=lambda estimate: estimate.day_production(
            estimate.now().date() + timedelta(days=2)
        ),
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=1,
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="energy_production_d3",
        translation_key="energy_production_d3",
        state=lambda estimate: estimate.day_production(
            estimate.now().date() + timedelta(days=3)
        ),
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=1,
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="energy_production_d4",
        translation_key="energy_production_d4",
        state=lambda estimate: estimate.day_production(
            estimate.now().date() + timedelta(days=4)
        ),
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=1,
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="energy_production_d5",
        translation_key="energy_production_d5",
        state=lambda estimate: estimate.day_production(
            estimate.now().date() + timedelta(days=5)
        ),
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=1,
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="energy_production_d6",
        translation_key="energy_production_d6",
        state=lambda estimate: estimate.day_production(
            estimate.now().date() + timedelta(days=6)
        ),
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=1,
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="energy_production_d7",
        translation_key="energy_production_d7",
        state=lambda estimate: estimate.day_production(
            estimate.now().date() + timedelta(days=7)
        ),
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=1,
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="power_highest_peak_time_today",
        translation_key="power_highest_peak_time_today",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="power_highest_peak_time_tomorrow",
        translation_key="power_highest_peak_time_tomorrow",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="power_production_now",
        translation_key="power_production_now",
        device_class=SensorDeviceClass.POWER,
        state=lambda estimate: estimate.power_production_now,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="power_production_next_15minutes",
        translation_key="power_production_next_15minutes",
        state=lambda estimate: estimate.power_production_at_time(
            estimate.now() + timedelta(minutes=15)
        ),
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="power_production_next_30minutes",
        translation_key="power_production_next_30minutes",
        state=lambda estimate: estimate.power_production_at_time(
            estimate.now() + timedelta(minutes=30)
        ),
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="power_production_next_hour",
        translation_key="power_production_next_hour",
        state=lambda estimate: estimate.power_production_at_time(
            estimate.now() + timedelta(hours=1)
        ),
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="power_production_next_12hours",
        translation_key="power_production_next_12hours",
        state=lambda estimate: estimate.power_production_at_time(
            estimate.now() + timedelta(hours=12)
        ),
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="power_production_next_24hours",
        translation_key="power_production_next_24hours",
        state=lambda estimate: estimate.power_production_at_time(
            estimate.now() + timedelta(hours=24)
        ),
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="energy_current_hour",
        translation_key="energy_current_hour",
        state=lambda estimate: estimate.energy_current_hour,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=1,
    ),
    OpenMeteoSolarForecastSensorEntityDescription(
        key="energy_next_hour",
        translation_key="energy_next_hour",
        state=lambda estimate: estimate.sum_energy_production(1),
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=1,
    ),
)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Defer sensor setup to the shared sensor module."""
    coordinator: OpenMeteoSolarForecastDataUpdateCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]
    entities = []
    
    # Ajouter tous les capteurs standard
    for entity_description in SENSORS:
        entities.append(
            OpenMeteoSolarForecastSensorEntity(
                entry_id=entry.entry_id,
                coordinator=coordinator,
                entity_description=entity_description,
            )
        )
    
    # Ajouter le capteur de débogage de nébulosité
    entities.append(
        OpenMeteoSolarCloudCoverDebugSensor(
            entry_id=entry.entry_id,
            coordinator=coordinator,
        )
    )
    
    async_add_entities(entities)

class OpenMeteoSolarForecastSensorEntity(
    CoordinatorEntity[OpenMeteoSolarForecastDataUpdateCoordinator], SensorEntity
):
    """Defines a Open-Meteo sensor."""
    entity_description: OpenMeteoSolarForecastSensorEntityDescription
    _attr_has_entity_name = True
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
        """Update the entity without fetching data from server.
        This is required for the power_production_* sensors to update
        as they take data in 15-minute intervals and the update interval
        is 30 minutes."""
        self.async_write_ha_state()
    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        await super().async_added_to_hass()
        # Update the state of the sensor every minute without
        # fetching new data from the server.
        async_track_utc_time_change(
            self.hass,
            self._update_callback,
            second=0,
        )
    @property
    def native_value(self) -> datetime | StateType:
        """Return the state of the sensor."""
        if self.entity_description.state is None:
            state: StateType | datetime = getattr(
                self.coordinator.data, self.entity_description.key
            )
        else:
            state = self.entity_description.state(self.coordinator.data)
        return state
    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        attrs = None
        
        if self.entity_description.key.startswith(
            "energy_production_d"
        ) or self.entity_description.key in (
            "energy_production_today",
            "energy_production_tomorrow",
        ):
            target_date = self.coordinator.data.now().date()
            if self.entity_description.key == "energy_production_tomorrow":
                target_date += timedelta(days=1)
            elif self.entity_description.key.startswith("energy_production_d"):
                target_date += timedelta(
                    days=int(self.entity_description.key[len("energy_production_d") :])
                )
            elif self.entity_description.key == "energy_production_today":
                pass  # target_date is already set to today
            else:
                raise ValueError(
                    f"Unexpected key {self.entity_description.key} for extra_state_attributes"
                )
            attrs = {
                ATTR_WATTS: {
                    watt_datetime.isoformat(): watt_value
                    for watt_datetime, watt_value in self.coordinator.data.watts.items()
                    if watt_datetime.date() == target_date
                },
                ATTR_WH_PERIOD: {
                    wh_datetime.isoformat(): wh_value
                    for wh_datetime, wh_value in self.coordinator.data.wh_period.items()
                    if wh_datetime.date() == target_date
                },
            }
        else:
            attrs = {}
            
        # Ajouter les informations d'ajustement de nébulosité seulement pour les capteurs d'énergie
        if hasattr(self.coordinator, "adjustment_stats") and self.entity_description.key.startswith("energy_"):
            cloud_info = {
                "average_cloud_cover": f"{self.coordinator.adjustment_stats.get('average_cloud_cover', 0):.1f}%",
                "adjustment": f"{self.coordinator.adjustment_stats.get('adjustment_percentage', 0):.1f}%"
            }
            
            if not attrs:
                attrs = {}
                
            attrs["cloud_adjustment"] = cloud_info
            
        return attrs
        
# Pas de modification à la classe OpenMeteoSolarCloudCoverDebugSensor
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