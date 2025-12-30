"""DataUpdateCoordinator for Koolnova."""

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed

from koolnova_api.client import KoolnovaAPIRestClient
from koolnova_api.exceptions import KoolnovaError

from .const import (
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

class KoolnovaDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch data from Koolnova API."""

    def __init__(self, hass: HomeAssistant, config_entry):
        """Initialize coordinator."""
        # Obtener intervalo de actualizacion configurado
        config_data = config_entry.data
        options_data = config_entry.options
        
        update_interval_seconds = options_data.get(
            CONF_UPDATE_INTERVAL,
            config_data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        )
        
        super().__init__(
            hass,
            _LOGGER,
            name="koolnova",
            update_interval=timedelta(seconds=update_interval_seconds),
        )

        self.client = KoolnovaAPIRestClient(
            config_data["email"], config_data["password"]
        )
        self.config_entry = config_entry
        self.data = {"projects": [], "sensors": []}

    def _fetch_data(self) -> dict:
        """Fetch all data from Koolnova API. Called every UPDATE_INTERVAL."""
        try:
            _LOGGER.debug("Fetching all data from Koolnova API (scheduled update)")
            projects = self.client.get_project()
            sensors = self.client.get_sensors()
            _LOGGER.debug("Successfully fetched %d projects and %d sensors", 
                         len(projects), len(sensors))
            return {"projects": projects, "sensors": sensors}
        except KoolnovaError as err:
            _LOGGER.error("Koolnova API error: %s", err)
            raise UpdateFailed(f"Error communicating with Koolnova API: {err}")
        except Exception as err:
            _LOGGER.error("Unexpected error fetching data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}")

    async def _async_update_data(self) -> dict:
        """Update all data asynchronously (projects and sensors)."""
        return await self.hass.async_add_executor_job(self._fetch_data)

    def _fetch_projects(self):
        """Fetch only projects from API."""
        try:
            _LOGGER.debug("Fetching projects from Koolnova API (on-demand)")
            return self.client.get_project()
        except Exception as err:
            _LOGGER.error("Error fetching projects: %s", err)
            raise UpdateFailed(f"Error fetching projects: {err}")

    def _fetch_sensors(self):
        """Fetch only sensors from API."""
        try:
            _LOGGER.debug("Fetching sensors from Koolnova API (on-demand)")
            return self.client.get_sensors()
        except Exception as err:
            _LOGGER.error("Error fetching sensors: %s", err)
            raise UpdateFailed(f"Error fetching sensors: {err}")

    async def async_refresh_projects(self):
        """Refresh only the projects (for project entities when accessed)."""
        projects = await self.hass.async_add_executor_job(self._fetch_projects)
        self.data["projects"] = projects
        self.async_update_listeners()
        return projects

    async def async_refresh_sensors(self):
        """Refresh only the sensors (for zone entities when accessed)."""
        sensors = await self.hass.async_add_executor_job(self._fetch_sensors)
        self.data["sensors"] = sensors
        self.async_update_listeners()
        return sensors

    def _update_sensor_in_cache(self, sensor_id: int, updated_sensor_data: dict):
        """Update specific sensor in local cache using complete API response."""
        if "sensors" in self.data:
            for i, sensor in enumerate(self.data["sensors"]):
                if sensor.get("Room_id") == sensor_id:
                    self.data["sensors"][i].update({
                        "Room_setpoint_temp": updated_sensor_data.get("setpoint_temperature"),
                        "Room_actual_temp": updated_sensor_data.get("temperature"),
                        "Room_status": updated_sensor_data.get("status"),
                        "Room_speed": updated_sensor_data.get("speed"),
                        "Room_id": updated_sensor_data.get("id"),
                        "Room_Name": updated_sensor_data.get("name"),
                        "Topic_id": updated_sensor_data.get("topic_info", {}).get("id") if updated_sensor_data.get("topic_info") else None,
                        "Room_update_at": updated_sensor_data.get("updated_at"),
                    })
                    _LOGGER.debug("Updated sensor %s in local cache using API response", sensor_id)
                    return True
        return False

    def _update_project_in_cache(self, topic_id: int, updated_project_data: dict):
        """Update specific project in local cache using complete API response."""
        if "projects" in self.data:
            for i, project in enumerate(self.data["projects"]):
                if project.get("Topic_Id") == topic_id:
                    if "mode" in updated_project_data:
                        self.data["projects"][i]["Mode"] = updated_project_data["mode"]
                    if "is_online" in updated_project_data:
                        self.data["projects"][i]["is_online"] = updated_project_data["is_online"]
                    if "eco" in updated_project_data:
                        self.data["projects"][i]["eco"] = updated_project_data["eco"]
                    if "last_sync" in updated_project_data:
                        self.data["projects"][i]["last_sync"] = updated_project_data["last_sync"]
                    if "is_stop" in updated_project_data:
                        self.data["projects"][i]["is_stop"] = updated_project_data["is_stop"]
                    _LOGGER.debug("Updated project %s in local cache using API response", topic_id)
                    return True
        return False

    async def async_update_sensor_data(self, sensor_id: int, payload: dict) -> dict:
        """Update sensor using API and update local cache - NO additional API calls."""
        try:
            _LOGGER.debug("Updating sensor %s with payload: %s", sensor_id, payload)
            result = await self.hass.async_add_executor_job(
                self.client.update_sensor, sensor_id, payload
            )
            _LOGGER.debug("API response for sensor %s: %s", sensor_id, result)
            self._update_sensor_in_cache(sensor_id, result)
            self.async_update_listeners()
            return result
        except Exception as err:
            _LOGGER.error("Error updating sensor %s: %s", sensor_id, err)
            raise

    async def async_update_project_data(self, topic_id: int, payload: dict) -> dict:
        """Update project using API and update local cache - NO additional API calls."""
        try:
            _LOGGER.debug("Updating project %s with payload: %s", topic_id, payload)
            result = await self.hass.async_add_executor_job(
                self.client.update_project, topic_id, payload
            )
            _LOGGER.debug("API response for project %s: %s", topic_id, result)
            self._update_project_in_cache(topic_id, result)
            self.async_update_listeners()
            return result
        except Exception as err:
            _LOGGER.error("Error updating project %s: %s", topic_id, err)
            raise

    async def async_update_all_sensors_temperature(self, temperature: float):
        """Update temperature setpoint for ALL sensors in the project."""
        try:
            _LOGGER.info("Updating temperature to %s degrees for all sensors in project", temperature)
            sensors_to_update = self.data.get("sensors", [])
            updated_count = 0
            failed_count = 0
            
            for sensor in sensors_to_update:
                sensor_id = sensor.get("Room_id")
                if sensor_id is not None:
                    try:
                        await self.async_update_sensor_data(sensor_id, {"setpoint_temperature": temperature})
                        updated_count += 1
                        _LOGGER.debug("Updated temperature for sensor %s (%s) to %s degrees", 
                                    sensor_id, sensor.get("Room_Name", "Unknown"), temperature)
                    except Exception as err:
                        failed_count += 1
                        _LOGGER.error("Failed to update temperature for sensor %s (%s): %s", 
                                    sensor_id, sensor.get("Room_Name", "Unknown"), err)
            
            _LOGGER.info("Temperature update completed: %d successful, %d failed", 
                        updated_count, failed_count)
            return {"updated": updated_count, "failed": failed_count}
        except Exception as err:
            _LOGGER.error("Error updating all sensors temperature: %s", err)
            raise

    async def async_update_all_sensors_status(self, status_code: str):
        """Update status for ALL sensors in the project."""
        try:
            _LOGGER.info("Updating status to %s for all sensors in project", status_code)
            sensors_to_update = self.data.get("sensors", [])
            updated_count = 0
            failed_count = 0
            
            for sensor in sensors_to_update:
                sensor_id = sensor.get("Room_id")
                if sensor_id is not None:
                    try:
                        await self.async_update_sensor_data(sensor_id, {"status": status_code})
                        updated_count += 1
                        _LOGGER.debug("Updated status for sensor %s (%s) to %s", 
                                    sensor_id, sensor.get("Room_Name", "Unknown"), status_code)
                    except Exception as err:
                        failed_count += 1
                        _LOGGER.error("Failed to update status for sensor %s (%s): %s", 
                                    sensor_id, sensor.get("Room_Name", "Unknown"), err)
            
            _LOGGER.info("Status update completed: %d successful, %d failed", 
                        updated_count, failed_count)
            return {"updated": updated_count, "failed": failed_count}
        except Exception as err:
            _LOGGER.error("Error updating all sensors status: %s", err)
            raise

    async def async_update_all_sensors_fan_speed(self, speed_code: str):
        """Update fan speed for ALL sensors in the project."""
        try:
            _LOGGER.info("Updating fan speed to %s for all sensors in project", speed_code)
            sensors_to_update = self.data.get("sensors", [])
            updated_count = 0
            failed_count = 0
            
            for sensor in sensors_to_update:
                sensor_id = sensor.get("Room_id")
                if sensor_id is not None:
                    try:
                        await self.async_update_sensor_data(sensor_id, {"speed": speed_code})
                        updated_count += 1
                        _LOGGER.debug("Updated fan speed for sensor %s (%s) to %s", 
                                    sensor_id, sensor.get("Room_Name", "Unknown"), speed_code)
                    except Exception as err:
                        failed_count += 1
                        _LOGGER.error("Failed to update fan speed for sensor %s (%s): %s", 
                                    sensor_id, sensor.get("Room_Name", "Unknown"), err)
            
            _LOGGER.info("Fan speed update completed: %d successful, %d failed", 
                        updated_count, failed_count)
            return {"updated": updated_count, "failed": failed_count}
        except Exception as err:
            _LOGGER.error("Error updating all sensors fan speed: %s", err)
            raise

    async def async_options_updated(self):
        """Handle updated options - restart coordinator with new interval."""
        config_data = self.config_entry.data
        options_data = self.config_entry.options
        
        new_interval_seconds = options_data.get(
            CONF_UPDATE_INTERVAL,
            config_data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        )
        
        new_interval = timedelta(seconds=new_interval_seconds)
        
        if new_interval != self.update_interval:
            _LOGGER.info("Updating coordinator interval from %s to %s seconds", 
                        self.update_interval.total_seconds(), new_interval_seconds)
            self.update_interval = new_interval

    # Backward compatibility methods
    async def async_update_sensor(self, sensor_id: int, payload: dict) -> dict:
        return await self.async_update_sensor_data(sensor_id, payload)

    async def async_update_project(self, topic_id: int, payload: dict) -> dict:
        return await self.async_update_project_data(topic_id, payload)
