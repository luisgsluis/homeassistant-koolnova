# -*- coding: utf-8 -*-
"""Client for the Koolnova REST API."""

import logging
import time
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from dateutil.parser import parse

from .exceptions import KoolnovaError
from .session import KoolnovaClientSession
from .const import COMMON_HEADERS, PATCH_HEADERS

_LOGGER = logging.getLogger(__name__)


class KoolnovaAPIRestClient:
    """Proxy to the Koolnova REST API."""

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

    def _get_session(self) -> KoolnovaClientSession:
        if self.session is None:
            self.session = KoolnovaClientSession(self.username, self.password, self.email)
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

            rooms.append({
                "Room_Name": room["name"],
                "Room_id": room["id"],
                "Room_status": room["status"],
                "Room_update_at": room["updated_at"],
                "Room_actual_temp": room["temperature"],
                "Room_setpoint_temp": room["setpoint_temperature"],
                "Room_speed": room["speed"],
                "Topic_id": topic_id 
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

        # Send the PATCH request
        response = self._get_session().rest_request("PATCH", url, json=payload, headers=headers)
        response.raise_for_status()

        _LOGGER.debug("Sensor %s updated successfully with payload %s: %s", sensor_id, payload, response.json())
        return response.json()
    
    def search_all_ids(self) -> Dict[str, List[str]]:
        """Return all device ids grouped by type (koolnova / hub).

        This is a minimal implementation used by the test-suite: it GETs
        `/modules` and classifies entries by `ModuleType_Id` (1 => koolnova,
        2 => hub) using the `Serial` field as identifier.
        """
        resp = self._get_session().rest_request("GET", "modules")
        json_resp = resp.json()
        koolnova = []
        hub = []
        for item in json_resp:
            serial = item.get("Serial")
            if not serial:
                continue
            module_type = item.get("ModuleType_Id")
            if module_type == 1:
                koolnova.append(serial)
            elif module_type == 2:
                hub.append(serial)

        return {"koolnova": koolnova, "hub": hub}

    def search_koolnova_ids(self) -> List[str]:
        """Return list of koolnova ids."""
        return self.search_all_ids().get("koolnova", [])

    def search_hub_ids(self) -> List[str]:
        """Return list of hub ids."""
        return self.search_all_ids().get("hub", [])

    def get_pool_measure_latest(self, koolnova_id: str) -> Dict[str, Any]:
        """Return latest measures for a koolnova device.

        Expected to call `/modules/{id}/NewResume` and convert the mocked
        response into the structure used by the tests.
        """
        resp = self._get_session().rest_request("GET", f"modules/{koolnova_id}/NewResume")
        json_resp = resp.json()

        # If the API returned no data at all
        if not json_resp:
            raise KoolnovaError(
                f"Error : No data received for koolnova {koolnova_id} by the API. "
                + "You should test on koolnova official app and contact gokoolnova if it is not working."
                + " Or perhaps API has changed :(.")

        # If Current key is missing -> same as no data
        if "Current" not in json_resp:
            raise KoolnovaError(
                f"Error : No data received for koolnova {koolnova_id} by the API. "
                + "You should test on koolnova official app and contact gokoolnova if it is not working."
                + " Or perhaps API has changed :(.")

        current = json_resp.get("Current")
        # If Current exists but contains no value (hibernation) -> specific message
        if current == "" or current is None:
            raise KoolnovaError(
                f"Error : No measure found for koolnova {koolnova_id} by the API."
                + " Your koolnova is probably not calibrated or in Winter mode."
                + " You should deactive the integration until you resolve the problem via the koolnova official app. "
            )

        date_time = parse(current.get("DateTime"))
        temperature = current.get("Temperature")
        red_ox = current.get("OxydoReductionPotentiel", {}).get("Value")
        chlorine = current.get("Desinfectant", {}).get("Value")
        ph = current.get("PH", {}).get("Value")
        battery = current.get("Battery", {}).get("Deviation")
        # tests expect battery as percentage (e.g. 0.75 -> 75)
        if battery is not None:
            battery = int(round(battery * 100))

        return {
            "date_time": date_time,
            "temperature": temperature,
            "red_ox": red_ox,
            "chlorine": chlorine,
            "ph": ph,
            "battery": battery,
        }

    def get_hub_state(self, hub_id: str) -> Dict[str, Any]:
        resp = self._get_session().rest_request("GET", f"hub/{hub_id}/state")
        json_resp = resp.json()
        state_equipment = json_resp.get("stateEquipment")
        behavior = json_resp.get("behavior")
        return {"state": bool(state_equipment), "mode": behavior}

    def set_hub_mode(self, hub_id: str, target_mode: str) -> Dict[str, Any]:
        if target_mode not in ("manual", "auto", "planning"):
            raise ValueError("Invalid mode")
        resp = self._get_session().rest_request("PUT", f"hub/{hub_id}/mode/{target_mode}")
        json_resp = resp.json()
        # Normalize response to {'state': bool, 'mode': behavior}
        state_equipment = json_resp.get("stateEquipment")
        behavior = json_resp.get("behavior")
        return {"state": bool(state_equipment), "mode": behavior}

    def set_hub_state(self, hub_id: str, state: bool) -> Dict[str, Any]:
        # The tests expect a call to /hub/{id}/Manual/True for True
        path = f"hub/{hub_id}/Manual/{str(state)}"
        # Use POST/PUT depending on API: tests mock POST for this endpoint
        response = self._get_session().rest_request("POST", path)
        # After changing state, return current state (tests will mock the GET)
        return self.get_hub_state(hub_id)
   
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
