# -*- coding: utf-8 -*-
"""Consts for Koolnova python client API."""

KOOLNOVA_API_URL = "https://api.koolnova.com"
KOOLNOVA_AUTH_URL = KOOLNOVA_API_URL + "/auth/v2/login/"

# Common headers for API requests
COMMON_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "fr",
    "origin": "https://app.koolnova.com",
    "referer": "https://app.koolnova.com/",
    "cache-control": "no-cache",
    "user-agent": "Mozilla/5.0",
}

# Headers for PATCH requests (includes content-type)
PATCH_HEADERS = COMMON_HEADERS.copy()
PATCH_HEADERS["content-type"] = "application/json"
