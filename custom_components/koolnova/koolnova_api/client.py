# -*- coding: utf-8 -*-
"""Client for the Koolnova REST API."""

import logging
import time
from typing import Any
from typing import Dict
from typing import Optional

from .exceptions import KoolnovaError
from .session import KoolnovaClientSession
from .const import AUTH_FAILURE_COOLDOWN, COMMON_HEADERS, PATCH_HEADERS

_LOGGER = logging.getLogger(__name__)


class KoolnovaAPIRestClient:
    """Proxy to the Koolnova REST API."""

    # Token expires after 1 hour (3600 seconds) - use 50 minutes to be safe
    TOKEN_LIFETIME = 3000  # 50 minutes in seconds

    def __init__(self, username: str, password: str, email: Optional[str] = None) -> None:
        """Initialize the API and authenticate so we can make requests.

        Args:
            username: string containing your Koolnova's app username
            password: string containing your Koolnova's app password
            email: optional email associated to the account (API accepte username, email, password)
        """
        self.username = username
        self.password = password
        self.email = email
        self.session: Optional[KoolnovaClientSession] = None
        self._last_auth_failure: float = 0.0

    def _is_session_valid(self) -> bool:
        """Check if current session is valid and not expired."""
        if self.session is None:
            return False

        # Check if token has expired
        if hasattr(self.session, 'token_created'):
            elapsed = time.time() - self.session.token_created
            if elapsed > self.TOKEN_LIFETIME:
                _LOGGER.debug("Session token expired (%.0f seconds old)", elapsed)
                return False

        return True

    def _get_session(self) -> KoolnovaClientSession:
        """Get a valid session, creating or refreshing if necessary."""
        if not self._is_session_valid():
            # Cooldown after a failed login: Koolnova auto-bans IPs that spam
            # failed auth attempts (issue #4), so back off instead of retrying
            # on every polling cycle.
            since_failure = time.time() - self._last_auth_failure
            if self._last_auth_failure and since_failure < AUTH_FAILURE_COOLDOWN:
                raise KoolnovaError(
                    f"Authentication recently failed; waiting "
                    f"{AUTH_FAILURE_COOLDOWN - since_failure:.0f}s before retrying "
                    "to avoid an IP ban from Koolnova"
                )

            _LOGGER.debug("Creating new session (previous was invalid/expired)")
            try:
                self.session = KoolnovaClientSession(self.username, self.password, self.email)
                self._last_auth_failure = 0.0
            except Exception as e:
                _LOGGER.error("Failed to create new session: %s", e)
                self.session = None
                self._last_auth_failure = time.time()
                raise

        return self.session

    

   

    def get_project(self) -> Dict[str, Any]:

        # Use the same endpoint shape as the webapp: trailing slash + common
        # query params. Add browser-like headers to match the web request.
        params = {
            "page": 1,
            "page_size": 25,
            "ordering": "-start_date",
            "search": "",
            "is_oem": "false",
        }
        headers = COMMON_HEADERS.copy()

        response = self._get_session().rest_request("GET", "projects/", params=params, headers=headers)
        response.raise_for_status()
        json_resp = response.json()
        if not json_resp:
            raise KoolnovaError(
                f"Error : No data received for Koolnova by the API. "
                + "You should test on Koolnova official app. "
                + "Or perhaps API has changed :(."
            )

        #_LOGGER.debug("Réponse brute  : %s", json_resp)

        if not json_resp["data"]:
            raise KoolnovaError(
                f"Error :  No data"
                )
        projects = []
        for project in json_resp["data"]:
            _LOGGER.debug("Project Name : %s", project["name"])
            _LOGGER.debug("Topic Name : %s", project["topic"]["name"])
            projects.append({
                "Project_Name": project["name"],
                "Topic_Name": project["topic"]["name"],
                "Topic_id": project["topic"]["id"],
                "Mode": project["topic"]["mode"],
                "is_stop": project["topic"]["is_stop"],
                "is_online": project["topic"]["is_online"],
                "eco": project["topic"]["eco"],
                "last_sync": project["topic"]["last_sync"],


            })

        return projects

    def get_sensors(self) -> Dict[str, Any]:

        # Request the sensors endpoint using trailing slash and browser-like headers
        headers = COMMON_HEADERS.copy()

        resp = self._get_session().rest_request("GET", "topics/sensors/", headers=headers)
        json_resp = resp.json()
        if not json_resp:
            raise KoolnovaError(
                f"Error : No data received for Koolnova by the API. "
                + "You should test on Koolnova official app. "
                + "Or perhaps API has changed :(."
            )

        #_LOGGER.debug("Réponse brute  : %s", json_resp)

        if not json_resp["data"]:
            raise KoolnovaError(
                f"Error :  No data"
                )

        rooms = []
        for room in json_resp["data"]:
            _LOGGER.debug("Room Name : %s", room["name"])
            _LOGGER.debug("Room Room_actual_temp : %s", room["temperature"])
            _LOGGER.debug("Topic Info : %s", room.get("topic_info", {}))
            # Récupérer l'id de topic_info
            topic_id = room.get("topic_info", {}).get("id", "Unknown")
            # Incluir toda la información de topic_info para acceder a RSSI, online, sync
            topic_info = room.get("topic_info", {})

            rooms.append({
                "Room_Name": room["name"],
                "Room_id": room["id"],
                "Room_status": room["status"],
                "Room_update_at": room["updated_at"],
                "Room_actual_temp": room["temperature"],
                "Room_setpoint_temp": room["setpoint_temperature"],
                "Room_speed": room["speed"],
                "Topic_id": topic_id,
                "topic_info": topic_info  # AÑADIDO: Toda la información de conectividad
            })

        return rooms
       

    def update_sensor(self, sensor_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update specific attributes for a sensor.

        Args:
            sensor_id: The ID of the sensor to update.
            payload: A dictionary containing the attributes to update and their new values.

        Returns:
            The JSON response from the API.
        """
        url = f"topics/sensors/{sensor_id}/"
        headers = PATCH_HEADERS.copy()

        # Send the PUT request
        response = self._get_session().rest_request("PUT", url, json=payload, headers=headers)
        response.raise_for_status()

        _LOGGER.debug("Sensor %s updated successfully with payload %s: %s", sensor_id, payload, response.json())
        return response.json()

    def update_project(self, topic_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update specific attributes for a project (topic).

        Args:
            topic_id: The ID of the topic/project to update.
            payload: A dictionary containing the attributes to update and their new values.

        Returns:
            The JSON response from the API.
        """
        url = f"topics/{topic_id}/"
        headers = PATCH_HEADERS.copy()

        response = self._get_session().rest_request("PATCH", url, json=payload, headers=headers)
        response.raise_for_status()

        _LOGGER.debug("Project %s updated successfully with payload %s: %s", topic_id, payload, response.json())
        return response.json()
