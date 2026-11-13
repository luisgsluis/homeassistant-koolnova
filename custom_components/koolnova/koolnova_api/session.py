# -*- coding: utf-8 -*-
"""Session manager for the Koolnova REST API in order to maintain authentication token between calls."""

import logging
import time
from typing import Optional

from requests import Response
from requests import Session
from requests.exceptions import ConnectionError
from requests.exceptions import Timeout

from .const import COMMON_HEADERS
from .const import FULL_USER_AGENT
from .const import KOOLNOVA_API_URL
from .const import KOOLNOVA_AUTH_URL

_LOGGER = logging.getLogger(__name__)

# Retry policy for authenticated API calls (rest_request).
DEFAULT_MAX_RETRIES = 3      # retries after the initial attempt
DEFAULT_RETRY_BACKOFF = 1.0  # base delay in seconds, doubles each attempt
DEFAULT_RETRY_MAX_DELAY = 30.0

# Per-request timeout. Without one, a hung request blocks a polling cycle forever.
# 45s is the value recommended by Koolnova support.
REQUEST_TIMEOUT = 45

class KoolnovaClientSession(Session):
    """HTTP session manager for Koolnova api.

    This session object allows to manage the authentication
    in the API using a token.
    """

    host: str = KOOLNOVA_API_URL

    def __init__(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff: float = DEFAULT_RETRY_BACKOFF,
        request_timeout: float = REQUEST_TIMEOUT,
    ) -> None:
        """Initialize and authenticate.

        Args:
            username: the flipr registered user
            password: the flipr user's password
            email: optional email for the account; this is the field the API
                authenticates on (see _authenticate)
            max_retries: retry count for rest_request
            retry_backoff: base delay (seconds) for the exponential backoff
            request_timeout: per-request timeout in seconds for auth and API calls
        """
        Session.__init__(self)
        self.username = username
        self.password = password
        self.email = email
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.request_timeout = request_timeout
        self.bearerToken: Optional[str] = None
        self.token_created: float = 0.0
        self._authenticate()

    def _authenticate(self) -> None:
        """POST /auth/v2/login/ and store the bearer token.

        Raises:
            RuntimeError: if the login fails after all attempts.
        """
        _LOGGER.debug("Starting authentication for username '%s' (email: %s)", self.username, self.email)

        # Build payload. The API authenticates under the 'email' field
        # (verified against api.koolnova.com/auth/v2/login/: 'email' -> 200,
        # 'username' -> 400 "Unable to log in with provided credentials").
        # The 404 in issue #4 was caused by the missing browser headers below,
        # not by the field name; sending 'username' regressed login (see v1.3.0).
        login = self.email or self.username or ""
        payload = {"email": login, "password": self.password}

        _LOGGER.debug("Auth payload user: %s", login)

        # Browser-like headers: since May 2026 the API returns 404 without the
        # sec-ch-ua / sec-fetch-* headers and a modern Chrome UA (issue #4).
        headers_token = COMMON_HEADERS.copy()
        headers_token["content-type"] = "application/json"

        # Improved retry logic with exponential backoff for rate limiting
        response = None
        max_attempts = 5
        base_delay = 2.0  # Start with 2 seconds
        max_delay = 60.0  # Cap at 60 seconds

        for attempt in range(max_attempts):
            try:
                response = super().request("POST", KOOLNOVA_AUTH_URL, json=payload, headers=headers_token, timeout=self.request_timeout)
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

        # Read body for easier debugging when failing (do not log it on
        # success: it contains the auth token)
        try:
            body = response.text
        except Exception:
            body = "<unable to read response body>"

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
        _LOGGER.debug("Authentication successful, token obtained")

    def refresh_token(self) -> None:
        """Re-authenticate and replace the bearer token.

        Used when the API answers 401 (expired/invalid token) mid-session.
        Only renews the token; the requests.Session itself is left untouched.
        """
        self._authenticate()

    def rest_request(
        self,
        method: str,
        path: str,
        max_retries: Optional[int] = None,
        retry_backoff: Optional[float] = None,
        **kwargs,
    ) -> Response:
        """
        Make a request using token authentication, retrying transient failures.

        Retries network errors (ConnectionError/Timeout), rate limiting (429)
        and server errors (5xx) with exponential backoff. A 401 refreshes the
        token once and retries. Everything else is propagated via
        raise_for_status().

        Args:
            method: HTTP method (e.g., "GET", "POST", "PATCH").
            path: Path of the REST API endpoint.
            max_retries: override the retry count (default: self.max_retries).
            retry_backoff: override the base backoff delay.
            **kwargs: Additional arguments for the request (e.g., headers, json, data).

        Returns:
            The Response object corresponding to the result of the API request.
        """
        retries = self.max_retries if max_retries is None else max_retries
        backoff = self.retry_backoff if retry_backoff is None else retry_backoff

        # Without an explicit timeout a hung request blocks the polling cycle.
        kwargs.setdefault("timeout", self.request_timeout)

        headers_auth = {
            "Authorization": "Bearer " + (self.bearerToken or ""),
            "Cache-Control": "no-cache",
            "User-Agent": FULL_USER_AGENT,
        }
        # Merge in the headers passed as an argument
        headers = kwargs.pop("headers", {})
        headers_auth.update(headers)

        url = f"{self.host}/{path}"
        refreshed = False  # un solo re-login por petición: si el token nuevo también da 401, no es el token

        for attempt in range(retries + 1):
            try:
                response = super().request(method, url, headers=headers_auth, **kwargs)
            except (ConnectionError, Timeout) as exc:
                if attempt < retries:
                    delay = min(backoff * (2 ** attempt), DEFAULT_RETRY_MAX_DELAY)
                    _LOGGER.warning(
                        "Network error on %s %s (attempt %d/%d): %s; retrying in %.1fs",
                        method, url, attempt + 1, retries + 1, exc, delay,
                    )
                    time.sleep(delay)
                    continue
                _LOGGER.error("Network error on %s %s persisted after %d attempts", method, url, retries + 1)
                raise

            # 401: token expired/invalid -> refresh once and retry
            if response.status_code == 401 and attempt < retries and not refreshed:
                refreshed = True
                _LOGGER.warning(
                    "Received 401 on %s %s (attempt %d/%d); refreshing token",
                    method, url, attempt + 1, retries + 1,
                )
                try:
                    self.refresh_token()
                except Exception:
                    # Invalidate the token so the client recreates the session
                    # (applying its anti-ban cooldown) on the next poll.
                    self.token_created = 0.0
                    raise
                headers_auth["Authorization"] = "Bearer " + (self.bearerToken or "")
                continue

            # 429: rate limited -> honour Retry-After when present
            if response.status_code == 429 and attempt < retries:
                try:
                    retry_after = response.headers.get("Retry-After")
                    delay = min(float(retry_after), DEFAULT_RETRY_MAX_DELAY) if retry_after else min(backoff * (2 ** attempt), DEFAULT_RETRY_MAX_DELAY)
                except ValueError:
                    delay = min(backoff * (2 ** attempt), DEFAULT_RETRY_MAX_DELAY)
                _LOGGER.warning(
                    "Rate limited (429) on %s %s, retrying in %.1fs (attempt %d/%d)",
                    method, url, delay, attempt + 1, retries + 1,
                )
                time.sleep(delay)
                continue

            # 5xx: server error -> retry with backoff
            if response.status_code >= 500 and attempt < retries:
                delay = min(backoff * (2 ** attempt), DEFAULT_RETRY_MAX_DELAY)
                _LOGGER.warning(
                    "Server error %d on %s %s, retrying in %.1fs (attempt %d/%d)",
                    response.status_code, method, url, delay, attempt + 1, retries + 1,
                )
                time.sleep(delay)
                continue

            response.raise_for_status()
            return response

        raise RuntimeError(f"All retry attempts exhausted for {method} {url}")
