"""Authentication configuration routes."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from backend.config import google_client_id
from backend.services.mongodb_service import mongo_service

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.get("/config")
def auth_config() -> tuple[Any, int]:
    return jsonify({"google_client_id": google_client_id()}), 200


@auth_bp.post("/google-login")
def google_login() -> tuple[Any, int]:
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        payload = {}

    mongo_service.upsert_google_user(
        name=str(payload.get("name") or "").strip(),
        email=str(payload.get("email") or "").strip(),
    )
    return jsonify({"status": "ok"}), 200
