"""Authentication configuration routes."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify

from backend.config import google_client_id

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.get("/config")
def auth_config() -> tuple[Any, int]:
    return jsonify({"google_client_id": google_client_id()}), 200
