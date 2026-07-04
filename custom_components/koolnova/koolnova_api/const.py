# -*- coding: utf-8 -*-
"""Consts for Koolnova python client API."""

KOOLNOVA_API_URL = "https://api.koolnova.com"
KOOLNOVA_AUTH_URL = KOOLNOVA_API_URL + "/auth/v2/login/"

# Full User-Agent string matching browser requests.
# IMPORTANT: since May 2026 the API rejects (404) requests without a modern
# Chrome UA and the sec-ch-ua / sec-fetch-* headers below (see issue #4).
FULL_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"

# Common headers for API requests
COMMON_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en",
    "origin": "https://app.koolnova.com",
    "referer": "https://app.koolnova.com/",
    "cache-control": "no-cache",
    "user-agent": FULL_USER_AGENT,
    "sec-ch-ua": '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
}

# Headers for PATCH requests (includes content-type)
PATCH_HEADERS = COMMON_HEADERS.copy()
PATCH_HEADERS["content-type"] = "application/json"

# Cooldown (seconds) before retrying authentication after a failed login.
# Koolnova bans IPs automatically when it detects repeated failed logins
# (see issue #4), so never re-attempt auth in a tight polling loop.
AUTH_FAILURE_COOLDOWN = 300
