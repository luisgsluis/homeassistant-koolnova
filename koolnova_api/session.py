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

        # Improved retry logic with exponential backoff for rate limiting
        response = None
        max_attempts = 5
        base_delay = 2.0  # Start with 2 seconds
        max_delay = 60.0  # Cap at 60 seconds

        for attempt in range(max_attempts):
            try:
                response = super().request("POST", KOOLNOVA_AUTH_URL, json=payload, headers=headers_token, timeout=30)
            except Exception as e:
                _LOGGER.exception("Exception when calling auth endpoint (attempt %d/%d): %s", attempt + 1, max_attempts, e)
                response = None

            if response is None:
                # Network error - use exponential backoff
                if attempt < max_attempts - 1:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    _LOGGER.debug("Network error, retrying in %.1f seconds (attempt %d/%d)", delay, attempt + 1, max_attempts)
                    time.sleep(delay)
                continue

            _LOGGER.debug("Auth response status: %s", response.status_code)

            if response.status_code == 429:
                # Rate limiting - extract retry-after if available
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    try:
                        delay = min(float(retry_after), max_delay)
                    except ValueError:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                else:
                    # API says "Expected available in 32 seconds" - use that as base
                    delay = min(32.0 + (attempt * 5), max_delay)

                if attempt < max_attempts - 1:
                    _LOGGER.warning("Rate limited (429), retrying in %.1f seconds (attempt %d/%d)", delay, attempt + 1, max_attempts)
                    time.sleep(delay)
                    continue
                else:
                    _LOGGER.error("Rate limit persisted after %d attempts", max_attempts)
                    break
            elif response.status_code >= 500:
                # Server errors - use shorter backoff
                if attempt < max_attempts - 1:
                    delay = min(base_delay * (2 ** attempt), 30.0)
                    _LOGGER.debug("Server error (%d), retrying in %.1f seconds (attempt %d/%d)",
                                response.status_code, delay, attempt + 1, max_attempts)
                    time.sleep(delay)
                    continue
            else:
                # Success or client error - break
                break

        if response is None:
            raise RuntimeError(f"Authentication request failed after {max_attempts} attempts (no response)")

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
        self.token_created = time.time()  # Track when token was created
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
