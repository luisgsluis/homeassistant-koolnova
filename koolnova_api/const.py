# -*- coding: utf-8 -*-
"""Consts for Koolnova python client API."""

KOOLNOVA_API_URL = "https://api.koolnova.com"
KOOLNOVA_AUTH_URL = KOOLNOVA_API_URL + "/auth/v2/login/"

# Full User-Agent string matching browser requests
FULL_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Common headers for API requests
COMMON_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en",
    "origin": "https://app.koolnova.com",
    "referer": "https://app.koolnova.com/",
    "cache-control": "no-cache",
    "user-agent": FULL_USER_AGENT,
}

# Headers for PATCH requests (includes content-type)
PATCH_HEADERS = COMMON_HEADERS.copy()
PATCH_HEADERS["content-type"] = "application/json"
