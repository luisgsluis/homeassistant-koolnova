"""DataUpdateCoordinator for Koolnova."""

import logging
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed

from .koolnova_api.client import KoolnovaAPIRestClient
from .koolnova_api.exceptions import KoolnovaError

from .const import (
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    CONF_PROJECT_UPDATE_FREQUENCY,
    DEFAULT_PROJECT_UPDATE_FREQUENCY,
    CONF_REQUEST_TIMEOUT,
    DEFAULT_REQUEST_TIMEOUT,
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

        # Koolnova bans IPs polled more often than every 30s (issue #4):
        # clamp intervals from configs created before this limit existed.
        if update_interval_seconds < MIN_UPDATE_INTERVAL:
            _LOGGER.warning(
                "Configured update interval (%ss) is below Koolnova's rate limit; "
                "clamping to %ss to avoid an IP ban",
                update_interval_seconds, MIN_UPDATE_INTERVAL,
            )
            update_interval_seconds = MIN_UPDATE_INTERVAL

        super().__init__(
            hass,
            _LOGGER,
            name="koolnova",
            update_interval=timedelta(seconds=update_interval_seconds),
        )

        self.client = KoolnovaAPIRestClient(
            username="",
            email=config_data["email"],
            password=config_data["password"],
            request_timeout=options_data.get(
                CONF_REQUEST_TIMEOUT,
                config_data.get(CONF_REQUEST_TIMEOUT, DEFAULT_REQUEST_TIMEOUT)
            ),
        )
        self.config_entry = config_entry
        self.data = {"projects": [], "sensors": [], "hubs": []}

        # Counter driving the periodic project refresh
        self._project_update_counter = 0
        self._project_update_frequency = options_data.get(
            CONF_PROJECT_UPDATE_FREQUENCY,
            config_data.get(CONF_PROJECT_UPDATE_FREQUENCY, DEFAULT_PROJECT_UPDATE_FREQUENCY)
        )

    def _fetch_hubs(self) -> list:
        """Discover hubs and read their state.

        Never raises: hubs are optional and only exist on legacy accounts.
        Returns a list of hub dicts, or [] when the account has no hub
        (/modules/ answers nothing usable, which is the norm for newer
        zone-based systems).
        """
        hubs = []
        try:
            module_ids = self.client.search_all_ids()
        except Exception as err:
            _LOGGER.debug("Hub discovery unavailable (%s); continuing without hubs", err)
            return hubs
        for hub_id in module_ids.get("hub", []):
            try:
                hub_state = self.client.get_hub_state(hub_id)
                hubs.append({
                    "Hub_id": hub_id,
                    "State": hub_state.get("state"),
                    "Mode": hub_state.get("mode"),
                })
            except Exception as err:
                _LOGGER.warning("Could not fetch state for hub %s: %s", hub_id, err)
        return hubs

    def _fetch_data_fallback(self) -> dict:
        """Fetch data via the /devices/ endpoint when the topics endpoints fail.

        Returns None when the fallback yields nothing usable.
        """
        try:
            _LOGGER.debug("Attempting fallback data fetch via /devices/")
            devices = self.client.get_devices()
            if not devices:
                _LOGGER.warning("Fallback: no devices found in /devices/")
                return None

            sensors = []
            projects_dict = {}
            for device in devices:
                sensor_data = device.get("sensor")
                if not sensor_data:
                    continue

                topic_info = sensor_data.get("topic_info", {})
                topic_id = topic_info.get("id", "Unknown")

                sensors.append({
                    "Room_Name": sensor_data.get("name"),
                    "Room_id": sensor_data.get("id"),
                    "Room_status": sensor_data.get("status"),
                    "Room_update_at": sensor_data.get("updated_at"),
                    "Room_actual_temp": sensor_data.get("temperature"),
                    "Room_setpoint_temp": sensor_data.get("setpoint_temperature"),
                    "Room_humidity": sensor_data.get("humidity"),
                    "Room_speed": sensor_data.get("speed"),
                    "Topic_id": topic_id,
                    "topic_info": topic_info,
                })

                if topic_id not in projects_dict:
                    projects_dict[topic_id] = {
                        "Project_Name": device.get("project_name", "Home"),
                        "Topic_Name": topic_info.get("name", "Main"),
                        "Topic_id": topic_id,
                        "Mode": topic_info.get("mode"),
                        "is_stop": topic_info.get("is_stop"),
                        "is_online": topic_info.get("is_online"),
                        "eco": topic_info.get("eco"),
                        "last_sync": topic_info.get("last_sync"),
                    }

            return {
                "projects": list(projects_dict.values()),
                "sensors": sensors,
                "hubs": self._fetch_hubs(),
            }
        except Exception as err:
            _LOGGER.error("Fallback data fetch failed: %s", err)
            return None

    def _fetch_data(self) -> dict:
        """Fetch all data from Koolnova API. Called during initial setup."""
        try:
            _LOGGER.debug("Fetching all data from Koolnova API (initial setup)")
            try:
                projects = self.client.get_project()
                sensors = self.client.get_sensors()
                hubs = self._fetch_hubs()
                _LOGGER.debug("Successfully fetched %d projects, %d sensors and %d hubs",
                             len(projects), len(sensors), len(hubs))
                return {"projects": projects, "sensors": sensors, "hubs": hubs}
            except Exception as err:
                _LOGGER.warning("Primary fetch failed, trying /devices/ fallback: %s", err)
                fallback_data = self._fetch_data_fallback()
                if fallback_data:
                    _LOGGER.info("Fallback fetch via /devices/ successful")
                    return fallback_data
                raise
        except KoolnovaError as err:
            _LOGGER.error("Koolnova API error: %s", err)
            raise UpdateFailed(f"Error communicating with Koolnova API: {err}")
        except Exception as err:
            _LOGGER.error("Unexpected error fetching data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}")

    def _fetch_sensors_only(self) -> dict:
        """Fetch only sensors data from Koolnova API. Called during periodic updates."""
        try:
            _LOGGER.debug("Fetching sensors data from Koolnova API (periodic update)")
            try:
                sensors = self.client.get_sensors()
            except Exception as err:
                _LOGGER.warning("Sensors fetch failed, trying /devices/ fallback: %s", err)
                fallback_data = self._fetch_data_fallback()
                if not fallback_data:
                    raise
                sensors = fallback_data.get("sensors", [])
                if fallback_data.get("projects"):
                    self.data["projects"] = fallback_data["projects"]
                if fallback_data.get("hubs"):
                    self.data["hubs"] = fallback_data["hubs"]
            _LOGGER.debug("Successfully fetched %d sensors", len(sensors))
            # Keep existing projects and hubs data, only update sensors
            return {
                "projects": self.data.get("projects", []),
                "sensors": sensors,
                "hubs": self.data.get("hubs", []),
            }
        except KoolnovaError as err:
            _LOGGER.error("Koolnova API error fetching sensors: %s", err)
            raise UpdateFailed(f"Error communicating with Koolnova API: {err}")
        except Exception as err:
            _LOGGER.error("Unexpected error fetching sensors: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}")

    async def _async_update_data(self) -> dict:
        """
        Update data asynchronously with intelligent polling strategy.

        This method implements a smart polling approach to optimize API usage:
        - FIRST RUN: Fetches complete data (projects + sensors) for initial setup
        - PERIODIC UPDATES: Uses counter-based strategy for project updates
          * Every Nth update: fetches projects + sensors (N = project_update_frequency)
          * Other updates: fetches only sensors for efficiency

        This optimization reduces API load since project data rarely changes,
        while sensor data (temperatures, status) updates frequently.
        However, project mode is updated periodically to keep Global Control entity current.

        Additionally, this method fires a "koolnova_update_completed" event after each update
        with detailed information about the update type, success status, and data counts.
        The event data includes:
        - update_type: "initial", "full", "sensors_only", "cached", or "failed"
        - success: boolean indicating if the update was successful
        - timestamp: timestamp of when the update occurred
        - entry_id: unique identifier for this integration instance
        - lastsync: the project's own "last_sync" timestamp, i.e. when the Koolnova system
          last synchronised (not when we polled it). Absent from "failed" events, and None
          when there is no project data to read it from.
        - projects_count: number of projects (for full/initial updates)
        - sensors_count: number of sensors (for full/sensors_only updates)
        - hubs_count: number of hubs (for full/sensors_only/initial updates)
        - error: error message (for failed/cached updates)

        Returns:
            dict: Data structure with 'projects' and 'sensors' keys
        """
        try:
            if self.data and self.data.get("projects"):
                # PERIODIC UPDATE STRATEGY with project update counter
                self._project_update_counter += 1

                if self._project_update_counter >= self._project_update_frequency:
                    # TIME TO UPDATE PROJECTS: fetch complete dataset
                    _LOGGER.debug("Project update cycle reached (%d/%d): fetching projects + sensors",
                                self._project_update_counter, self._project_update_frequency)
                    self._project_update_counter = 0  # Reset counter
                    result = await self.hass.async_add_executor_job(self._fetch_data)
                    
                    # Fire an event after a full update
                    self.hass.bus.async_fire("koolnova_update_completed", {
                        "update_type": "full",
                        "success": True,
                        "timestamp": datetime.now().isoformat(),
                        "entry_id": self.config_entry.entry_id,
                        "lastsync": result.get("projects", [{}])[0].get("last_sync") if result.get("projects") else None,
                        "projects_count": len(result.get("projects", [])),
                        "sensors_count": len(result.get("sensors", [])),
                        "hubs_count": len(result.get("hubs", []))
                    })

                    return result
                else:
                    # NORMAL UPDATE: Only fetch sensors for efficiency
                    _LOGGER.debug("Using optimized polling: sensors only (projects cached) - counter: %d/%d",
                                self._project_update_counter, self._project_update_frequency)
                    result = await self.hass.async_add_executor_job(self._fetch_sensors_only)
                    
                    # Fire an event after a partial update (sensors only)
                    self.hass.bus.async_fire("koolnova_update_completed", {
                        "update_type": "sensors_only",
                        "success": True,
                        "timestamp": datetime.now().isoformat(),
                        "entry_id": self.config_entry.entry_id,
                        "lastsync": self.data.get("projects", [{}])[0].get("last_sync") if self.data.get("projects") else None,
                        "sensors_count": len(result.get("sensors", [])),
                        "hubs_count": len(result.get("hubs", []))
                    })

                    return result
            else:
                # INITIAL SETUP: Fetch complete dataset and reset counter
                _LOGGER.debug("Initial setup: fetching complete dataset (projects + sensors)")
                self._project_update_counter = 0
                result = await self.hass.async_add_executor_job(self._fetch_data)
                
                # Fire an event after the initial setup
                self.hass.bus.async_fire("koolnova_update_completed", {
                    "update_type": "initial",
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "entry_id": self.config_entry.entry_id,
                    "lastsync": result.get("projects", [{}])[0].get("last_sync") if result.get("projects") else None,
                    "projects_count": len(result.get("projects", [])),
                    "sensors_count": len(result.get("sensors", [])),
                    "hubs_count": len(result.get("hubs", []))
                })

                return result
        except Exception as err:
            # Enhanced error handling for authentication failures
            error_msg = str(err)
            if "Authentication failed" in error_msg or "429" in error_msg:
                _LOGGER.warning("Authentication/rate limiting error during data update: %s", err)
                # For auth failures, return existing data if available to avoid disabling the integration
                if self.data and (self.data.get("projects") or self.data.get("sensors")):
                    _LOGGER.info("Returning cached data due to authentication error")
                    
                    # Disparar evento de error con datos cacheados
                    self.hass.bus.async_fire("koolnova_update_completed", {
                        "update_type": "cached",
                        "success": False,
                        "error": "authentication_failed",
                        "timestamp": datetime.now().isoformat(),
                        "entry_id": self.config_entry.entry_id,
                        "lastsync": self.data.get("projects", [{}])[0].get("last_sync") if self.data.get("projects") else None
                    })
                    
                    return self.data
                else:
                    # No cached data available, re-raise to trigger proper error handling
                    
                    # Fire a critical error event
                    self.hass.bus.async_fire("koolnova_update_completed", {
                        "update_type": "failed",
                        "success": False,
                        "error": str(err),
                        "timestamp": datetime.now().isoformat(),
                        "entry_id": self.config_entry.entry_id
                    })
                    
                    raise UpdateFailed(f"Authentication failed and no cached data available: {err}")
            else:
                # Re-raise other errors
                
                # Fire a generic error event
                self.hass.bus.async_fire("koolnova_update_completed", {
                    "update_type": "failed",
                    "success": False,
                    "error": str(err),
                    "timestamp": datetime.now().isoformat(),
                    "entry_id": self.config_entry.entry_id
                })
                
                raise

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
                    # Only overwrite humidity when the PUT response carries it,
                    # so the sensor doesn't blank out between polls
                    if "humidity" in updated_sensor_data:
                        self.data["sensors"][i]["Room_humidity"] = updated_sensor_data["humidity"]
                    _LOGGER.debug("Updated sensor %s in local cache using API response", sensor_id)
                    return True
        return False

    def _update_project_in_cache(self, topic_id: int, updated_project_data: dict):
        """Update specific project in local cache using complete API response."""
        if "projects" in self.data:
            for i, project in enumerate(self.data["projects"]):
                if project.get("Topic_id") == topic_id:
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
        """Handle updated options - update coordinator settings without full restart."""
        config_data = self.config_entry.data
        options_data = self.config_entry.options

        # Update interval
        new_interval_seconds = options_data.get(
            CONF_UPDATE_INTERVAL,
            config_data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        )

        # Same clamp as in __init__: never poll faster than Koolnova allows
        if new_interval_seconds < MIN_UPDATE_INTERVAL:
            _LOGGER.warning(
                "Configured update interval (%ss) is below Koolnova's rate limit; "
                "clamping to %ss to avoid an IP ban",
                new_interval_seconds, MIN_UPDATE_INTERVAL,
            )
            new_interval_seconds = MIN_UPDATE_INTERVAL

        new_interval = timedelta(seconds=new_interval_seconds)

        if new_interval != self.update_interval:
            _LOGGER.info("Updating coordinator interval from %s to %s seconds",
                        self.update_interval.total_seconds(), new_interval_seconds)
            self.update_interval = new_interval

        # Update project update frequency
        new_frequency = options_data.get(
            CONF_PROJECT_UPDATE_FREQUENCY,
            config_data.get(CONF_PROJECT_UPDATE_FREQUENCY, DEFAULT_PROJECT_UPDATE_FREQUENCY)
        )

        if new_frequency != self._project_update_frequency:
            _LOGGER.info("Updating project update frequency from %s to %s",
                        self._project_update_frequency, new_frequency)
            self._project_update_frequency = new_frequency
            self._project_update_counter = 0  # Reset counter with new frequency

        # Request timeout
        new_timeout = options_data.get(
            CONF_REQUEST_TIMEOUT,
            config_data.get(CONF_REQUEST_TIMEOUT, DEFAULT_REQUEST_TIMEOUT)
        )

        if new_timeout != self.client.request_timeout:
            _LOGGER.info("Updating API request timeout from %s to %s seconds",
                        self.client.request_timeout, new_timeout)
            self.client.set_request_timeout(new_timeout)

    # Backward compatibility methods
    async def async_update_sensor(self, sensor_id: int, payload: dict) -> dict:
        return await self.async_update_sensor_data(sensor_id, payload)

    async def async_update_project(self, topic_id: int, payload: dict) -> dict:
        return await self.async_update_project_data(topic_id, payload)
