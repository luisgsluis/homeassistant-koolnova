# -*- coding: utf-8 -*-
"""Session manager for the Koolnova REST API in order to maintain authentication token between calls."""

import logging
import json
import time
from typing import Optional
from urllib.parse import quote_plus

from requests import Response
from requests import Session

#logging.basicConfig(level=logging.DEBUG)

from .const import KOOLNOVA_API_URL
from .const import KOOLNOVA_AUTH_URL

_LOGGER = logging.getLogger(__name__)

# ============= CONSTANTE CENTRALIZADA USER-AGENT =============
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
# =============================================================

class KoolnovaClientSession(Session):
    """HTTP session manager for Koolnova api.

    This session object allows to manage the authentication
    in the API using a token.
    """

    host: str = KOOLNOVA_API_URL

    def __init__(self, username: str, password: str, email: Optional[str] = None) -> None:
        """Initialize and authenticate.

        Args:
            username: the flipr registered user
            password: the flipr user's password
        """
        Session.__init__(self)
        _LOGGER.debug("Starting authentication for username '%s' (email: %s)", username, email)

        # Build payload: prefer explicit email param; if not provided but username
        # looks like an email address, send it as 'email' as well (matches web app)
        if email:
            payload = {"email": email, "password": password}
        elif username and "@" in username:
            payload = {"email": username, "password": password}
        else:
            payload = {"username": username or "", "password": password}

        _LOGGER.debug("Auth payload: %s", payload)

        # Add headers similar to browser request (helps servers routing based on Origin/UA)
        headers_token = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "accept-language": "fr",
            "origin": "https://app.koolnova.com",
            "referer": "https://app.koolnova.com/",
            "cache-control": "no-cache",
            "user-agent": DEFAULT_USER_AGENT,  # ← USAR CONSTANTE
        }

        # Simple retry on 429 Too Many Requests
        response = None
        for attempt in range(3):
            try:
                response = super().request("POST", KOOLNOVA_AUTH_URL, json=payload, headers=headers_token, timeout=10)
            except Exception:
                _LOGGER.exception("Exception when calling auth endpoint (attempt %s)", attempt + 1)
                response = None

            if response is None:
                # small sleep and retry
                time.sleep(0.5 * (attempt + 1))
                continue

            _LOGGER.debug("Auth response status: %s", response.status_code)
            if response.status_code == 429:
                # backoff and retry
                time.sleep(0.5 * (attempt + 1))
                continue
            break

        if response is None:
            raise RuntimeError("Authentication request failed (no response)")

        # Log body for easier debugging when failing
        try:
            body = response.text
        except Exception:
            body = "<unable to read response body>"

        _LOGGER.debug("Auth response body: %s", body)

        try:
            response.raise_for_status()
        except Exception as exc:
            raise RuntimeError(f"Authentication failed: {exc} - {body}") from exc

        data = response.json()
        # Support common token field names
        token = data.get("access_token") or data.get("token") or data.get("accessToken")
        if not token:
            raise RuntimeError(f"Authentication response did not contain a token: {data}")

        self.bearerToken = str(token)
        _LOGGER.debug("BearerToken of authentication : %s", self.bearerToken)

    def rest_request(self, method: str, path: str, **kwargs) -> Response:
        """
        Make a request using token authentication.

        Args:
            method: HTTP method (e.g., "GET", "POST", "PATCH").
            path: Path of the REST API endpoint.
            **kwargs: Additional arguments for the request (e.g., headers, json, data).

        Returns:
            The Response object corresponding to the result of the API request.
        """
        headers_auth = {
            "Authorization": "Bearer " + self.bearerToken,
            "Cache-Control": "no-cache",
            "User-Agent": DEFAULT_USER_AGENT,  # ← AÑADIDO USER-AGENT AQUÍ
        }
        # Fusionner les headers passés en argument
        headers = kwargs.pop("headers", {})
        headers_auth.update(headers)

        response = super().request(method, f"{self.host}/{path}", headers=headers_auth, **kwargs)
        response.raise_for_status()
        return response
