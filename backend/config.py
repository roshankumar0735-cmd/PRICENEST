"""Application configuration constants."""

import os

DEFAULT_GOOGLE_CLIENT_ID = "680749009825-ao8hh9f5r6fr0cd8d7ciq3e1ikjsf74j.apps.googleusercontent.com"
DEFAULT_GOOGLE_MAPS_API_KEY = "AIzaSyAPkMff4klSo28J-UIwjl6dXwpYzAc6nKM"


def google_client_id() -> str:
    return os.environ.get("GOOGLE_CLIENT_ID", "").strip() or DEFAULT_GOOGLE_CLIENT_ID


def google_maps_api_key() -> str:
    return os.environ.get("GOOGLE_MAPS_API_KEY", "").strip() or DEFAULT_GOOGLE_MAPS_API_KEY
