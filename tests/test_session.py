"""Tests for the login request.

The login payload field is the single most fragile detail in this integration: v1.3.0
switched it from `email` to `username` and broke authentication for everyone, and
v1.3.1 had to revert it. These tests pin that behaviour down.
"""

import unittest
from unittest.mock import patch

from requests.exceptions import ConnectionError
from requests.exceptions import HTTPError
from requests.exceptions import Timeout

from koolnova_api.session import KoolnovaClientSession


def _ok_response(payload=None, status=200):
    """Build a stand-in for requests.Response with just what the code touches."""

    class _Response:
        status_code = status
        headers = {}
        text = "{}"

        def json(self):
            return payload if payload is not None else {"access_token": "tok"}

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(f"HTTP {self.status_code}")

    return _Response()


def _status_response(status, payload=None, headers=None):
    """Response with an explicit status code and headers (for retry tests)."""

    class _Response:
        status_code = status
        text = "{}"

        def json(self):
            return payload if payload is not None else {"access_token": "tok"}

        def raise_for_status(self):
            if self.status_code >= 400:
                raise HTTPError(f"HTTP {self.status_code}", response=self)

    response = _Response()
    response.headers = headers or {}
    return response


class LoginPayloadTest(unittest.TestCase):
    """What we send to /auth/v2/login/."""

    def _login(self, *args, **kwargs):
        with patch("requests.Session.request", return_value=_ok_response()) as request:
            KoolnovaClientSession(*args, **kwargs)
        return request.call_args

    def test_credentials_are_sent_under_email_not_username(self):
        """Regression guard for v1.3.0: 'username' makes the API answer 400."""
        _, kwargs = self._login("user@example.com", "secret")

        self.assertEqual(kwargs["json"], {"email": "user@example.com", "password": "secret"})
        self.assertNotIn("username", kwargs["json"])

    def test_explicit_email_argument_wins_over_username(self):
        _, kwargs = self._login("someone", "secret", email="real@example.com")

        self.assertEqual(kwargs["json"]["email"], "real@example.com")

    def test_posts_to_the_v2_login_endpoint(self):
        args, _ = self._login("user@example.com", "secret")

        self.assertEqual(args[0], "POST")
        self.assertEqual(args[1], "https://api.koolnova.com/auth/v2/login/")

    def test_sends_browser_headers(self):
        """Regression guard for issue #4: without these the API answers 404."""
        _, kwargs = self._login("user@example.com", "secret")
        headers = kwargs["headers"]

        self.assertIn("Chrome/", headers["user-agent"])
        self.assertIn("sec-ch-ua", headers)
        self.assertIn("sec-fetch-mode", headers)
        self.assertEqual(headers["origin"], "https://app.koolnova.com")
        self.assertEqual(headers["content-type"], "application/json")


class TokenHandlingTest(unittest.TestCase):
    """What we do with the response."""

    def test_accepts_the_documented_token_field_names(self):
        for field in ("access_token", "token", "accessToken"):
            with self.subTest(field=field):
                with patch("requests.Session.request", return_value=_ok_response({field: "abc123"})):
                    session = KoolnovaClientSession("user@example.com", "secret")

                self.assertEqual(session.bearerToken, "abc123")

    def test_raises_when_the_response_carries_no_token(self):
        with patch("requests.Session.request", return_value=_ok_response({"detail": "nope"})):
            with self.assertRaises(RuntimeError):
                KoolnovaClientSession("user@example.com", "secret")

    def test_raises_on_a_rejected_login(self):
        with patch("requests.Session.request", return_value=_ok_response(status=400)):
            with self.assertRaises(RuntimeError):
                KoolnovaClientSession("user@example.com", "secret")

    def test_authenticated_requests_carry_the_bearer_token(self):
        with patch("requests.Session.request", return_value=_ok_response()):
            session = KoolnovaClientSession("user@example.com", "secret")

        with patch("requests.Session.request", return_value=_ok_response()) as request:
            session.rest_request("GET", "projects/")

        headers = request.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "Bearer tok")
        self.assertIn("Chrome/", headers["User-Agent"])

    def test_rest_request_builds_the_url_from_the_api_host(self):
        with patch("requests.Session.request", return_value=_ok_response()):
            session = KoolnovaClientSession("user@example.com", "secret")

        with patch("requests.Session.request", return_value=_ok_response()) as request:
            session.rest_request("GET", "topics/sensors/")

        self.assertEqual(request.call_args.args[1], "https://api.koolnova.com/topics/sensors/")


class RetryBehaviourTest(unittest.TestCase):
    """rest_request retries transient failures instead of surfacing them."""

    def setUp(self):
        with patch("requests.Session.request", return_value=_ok_response()):
            self.session = KoolnovaClientSession("user@example.com", "secret")
        # Avoid real sleeps between retries.
        sleep = patch("koolnova_api.session.time.sleep")
        sleep.start()
        self.addCleanup(sleep.stop)

    def test_succeeds_without_retry_on_a_normal_response(self):
        with patch("requests.Session.request", return_value=_ok_response()) as request:
            response = self.session.rest_request("GET", "projects/")

        self.assertEqual(request.call_count, 1)
        self.assertEqual(response.status_code, 200)

    def test_retries_after_a_connection_error(self):
        with patch("requests.Session.request", side_effect=[ConnectionError("boom"), _ok_response()]) as request:
            response = self.session.rest_request("GET", "projects/")

        self.assertEqual(request.call_count, 2)
        self.assertEqual(response.status_code, 200)

    def test_retries_after_a_timeout(self):
        with patch("requests.Session.request", side_effect=[Timeout("slow"), _ok_response()]) as request:
            response = self.session.rest_request("GET", "projects/")

        self.assertEqual(request.call_count, 2)
        self.assertEqual(response.status_code, 200)

    def test_retries_on_rate_limit(self):
        with patch(
            "requests.Session.request",
            side_effect=[_status_response(429, headers={"Retry-After": "0"}), _ok_response()],
        ) as request:
            response = self.session.rest_request("GET", "projects/")

        self.assertEqual(request.call_count, 2)
        self.assertEqual(response.status_code, 200)

    def test_retries_on_rate_limit_without_retry_after(self):
        with patch(
            "requests.Session.request",
            side_effect=[_status_response(429), _ok_response()],
        ):
            response = self.session.rest_request("GET", "projects/")

        self.assertEqual(response.status_code, 200)

    def test_retries_on_server_error(self):
        with patch("requests.Session.request", side_effect=[_status_response(500), _ok_response()]) as request:
            response = self.session.rest_request("GET", "projects/")

        self.assertEqual(request.call_count, 2)
        self.assertEqual(response.status_code, 200)

    def test_connection_error_is_reraised_once_retries_run_out(self):
        # 4 attempts with default max_retries=3, all failing.
        with patch("requests.Session.request", side_effect=[ConnectionError("boom")] * 4) as request:
            with self.assertRaises(ConnectionError):
                self.session.rest_request("GET", "projects/")

        self.assertEqual(request.call_count, 4)

    def test_max_retries_zero_does_not_retry(self):
        with patch("requests.Session.request", side_effect=[ConnectionError("boom")]) as request:
            with self.assertRaises(ConnectionError):
                self.session.rest_request("GET", "projects/", max_retries=0)

        self.assertEqual(request.call_count, 1)

    def test_400_is_not_retried(self):
        with patch("requests.Session.request", side_effect=[_status_response(400)]) as request:
            with self.assertRaises(HTTPError):
                self.session.rest_request("GET", "projects/")

        self.assertEqual(request.call_count, 1)


class TokenRefreshTest(unittest.TestCase):
    """A 401 mid-session refreshes the token and retries the call."""

    def setUp(self):
        with patch("requests.Session.request", return_value=_ok_response()):
            self.session = KoolnovaClientSession("user@example.com", "secret")
        sleep = patch("koolnova_api.session.time.sleep")
        sleep.start()
        self.addCleanup(sleep.stop)

    def test_401_refreshes_the_token_and_retries(self):
        # GET -> 401, login (refresh) -> 200 token, GET retry -> 200
        with patch(
            "requests.Session.request",
            side_effect=[_status_response(401), _ok_response(), _ok_response()],
        ) as request:
            response = self.session.rest_request("GET", "projects/")

        self.assertEqual(request.call_count, 3)
        self.assertEqual(response.status_code, 200)

        # The refreshed token is the one used on the retried call.
        _, kwargs = request.call_args_list[2]
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer tok")

    def test_persistent_401_logs_in_only_once(self):
        # GET -> 401, login -> 200, GET -> 401 again: the token is not the problem, so no second
        # login (each one counts against the API's login rate limit that leads to a ban).
        with patch(
            "requests.Session.request",
            side_effect=[_status_response(401), _ok_response(), _status_response(401)],
        ) as request:
            with self.assertRaises(HTTPError):
                self.session.rest_request("GET", "projects/")

        logins = [c for c in request.call_args_list if c.args[0] == "POST"]
        self.assertEqual(len(logins), 1)
        self.assertEqual(request.call_count, 3)

    def test_logins_per_request_capped_at_five(self):
        # GET -> 401, then the login keeps answering 429: 5 login attempts in total, never 15.
        with patch(
            "requests.Session.request",
            side_effect=[_status_response(401)] + [_status_response(429)] * 20,
        ) as request:
            with self.assertRaises(Exception):
                self.session.rest_request("GET", "projects/")

        logins = [c for c in request.call_args_list if c.args[0] == "POST"]
        self.assertEqual(len(logins), 5)

    def test_refresh_token_replaces_the_bearer_token(self):
        with patch("requests.Session.request", return_value=_ok_response({"access_token": "newtok"})):
            self.session.refresh_token()

        self.assertEqual(self.session.bearerToken, "newtok")

    def test_401_without_retries_raises_instead_of_refreshing(self):
        with patch("requests.Session.request", side_effect=[_status_response(401)]):
            with self.assertRaises(HTTPError):
                self.session.rest_request("GET", "projects/", max_retries=0)

    def test_a_failed_refresh_invalidates_the_token_for_the_next_poll(self):
        # GET -> 401, refresh login -> 400.
        with patch(
            "requests.Session.request",
            side_effect=[_status_response(401), _status_response(400)],
        ):
            with self.assertRaises(RuntimeError):
                self.session.rest_request("GET", "projects/")

        # token_created reset so the client recreates the session (with its
        # anti-ban cooldown) instead of reusing a dead token.
        self.assertEqual(self.session.token_created, 0.0)


class RequestTimeoutTest(unittest.TestCase):
    def setUp(self):
        with patch("requests.Session.request", return_value=_ok_response()):
            self.session = KoolnovaClientSession("user@example.com", "secret")

    def test_defaults_to_a_45s_timeout(self):
        with patch("requests.Session.request", return_value=_ok_response()) as request:
            self.session.rest_request("GET", "projects/")

        self.assertEqual(request.call_args.kwargs["timeout"], 45)

    def test_an_explicit_timeout_is_preserved(self):
        with patch("requests.Session.request", return_value=_ok_response()) as request:
            self.session.rest_request("GET", "projects/", timeout=10)

        self.assertEqual(request.call_args.kwargs["timeout"], 10)

    def test_a_configured_timeout_applies_to_auth_and_api_calls(self):
        with patch("requests.Session.request", return_value=_ok_response()) as request:
            session = KoolnovaClientSession("user@example.com", "secret", request_timeout=10)
            session.rest_request("GET", "projects/")

        auth_timeout = request.call_args_list[0].kwargs["timeout"]
        api_timeout = request.call_args_list[1].kwargs["timeout"]
        self.assertEqual(auth_timeout, 10)
        self.assertEqual(api_timeout, 10)


if __name__ == "__main__":
    unittest.main()
