"""Optional MongoDB Atlas persistence helpers.

MongoDB is intentionally additive: every public method catches failures so
authentication, prediction, and the existing ML workflow continue normally if
Atlas is not configured or temporarily unavailable.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

try:
    from pymongo import MongoClient
    from pymongo.collection import Collection
except Exception:  # pragma: no cover - keeps app bootable without pymongo
    MongoClient = None  # type: ignore[assignment]
    Collection = Any  # type: ignore[misc, assignment]


LOGGER = logging.getLogger(__name__)


def load_local_env() -> None:
    """Load simple KEY=VALUE pairs from the project .env file if present."""
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    if not os.path.exists(env_path):
        return

    try:
        with open(env_path, "r", encoding="utf-8") as env_file:
            for line in env_file:
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                key, value = stripped.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    except Exception as exc:
        LOGGER.warning("Could not load local .env file: %s", exc)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MongoDBService:
    """Small resilient wrapper around the PriceNest MongoDB collections."""

    def __init__(self) -> None:
        self._client: Any | None = None
        self._users: Collection[Any] | None = None
        self._prediction_history: Collection[Any] | None = None
        self._enabled = False
        self._connect()

    def _connect(self) -> None:
        load_local_env()
        uri = os.environ.get("MONGODB_URI", "").strip()
        if not uri:
            LOGGER.info("MONGODB_URI is not set; MongoDB persistence is disabled.")
            return
        if MongoClient is None:
            LOGGER.warning("pymongo is not available; MongoDB persistence is disabled.")
            return

        try:
            self._client = MongoClient(uri, serverSelectionTimeoutMS=2500)
            self._client.admin.command("ping")
            database = self._client["pricenest"]
            self._users = database["users"]
            self._prediction_history = database["prediction_history"]
            self._users.create_index("email", unique=True)
            self._prediction_history.create_index("created_at")
            self._enabled = True
        except Exception as exc:
            LOGGER.warning("MongoDB connection failed; continuing without persistence: %s", exc)
            self._client = None
            self._users = None
            self._prediction_history = None
            self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    def upsert_google_user(self, *, name: str | None, email: str | None) -> None:
        if not email or self._users is None:
            return

        now = utc_now()
        try:
            self._users.update_one(
                {"email": email},
                {
                    "$set": {
                        "name": name or "",
                        "email": email,
                        "last_login": now,
                    },
                    "$setOnInsert": {"created_at": now},
                },
                upsert=True,
            )
        except Exception as exc:
            LOGGER.warning("MongoDB user upsert failed for %s: %s", email, exc)

    def save_prediction_history(self, *, payload: dict[str, Any], prediction: dict[str, Any]) -> None:
        if self._prediction_history is None:
            return

        user_email = str(payload.get("user_email") or "").strip() or "guest"
        document = {
            "user_email": user_email,
            "city": str(payload.get("city") or prediction.get("city") or "").strip(),
            "location": str(payload.get("location") or prediction.get("location") or "").strip(),
            "property_type": str(payload.get("property_type") or "").strip(),
            "predicted_price": prediction.get("predicted_price"),
            "created_at": utc_now(),
        }

        try:
            self._prediction_history.insert_one(document)
        except Exception as exc:
            LOGGER.warning("MongoDB prediction history insert failed: %s", exc)


mongo_service = MongoDBService()
