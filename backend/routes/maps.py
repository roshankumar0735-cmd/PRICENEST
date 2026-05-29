"""Map and nearby-facility routes."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from backend.config import google_maps_api_key
from backend.services.prediction_service import PredictionService


def create_map_routes(service: PredictionService) -> Blueprint:
    blueprint = Blueprint("maps", __name__)

    @blueprint.get("/maps/config")
    def maps_config() -> tuple[Any, int]:
        api_key = google_maps_api_key()
        return jsonify({"maps_enabled": bool(api_key)}), 200

    @blueprint.post("/nearby")
    def nearby() -> tuple[Any, int]:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"error": "Request body must be a JSON object."}), 400

        location_label = payload.get("locationLabel") or payload.get("location") or ""
        radius_m = payload.get("radiusM") or payload.get("radius_m") or 2500
        limit_per_type = payload.get("limitPerType") or payload.get("limit_per_type") or 5

        try:
            result = service.nearby_places(
                location_label=location_label,
                api_key=google_maps_api_key(),
                radius_m=int(radius_m),
                limit_per_type=int(limit_per_type),
            )
            return jsonify(result), 200
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception:
            return jsonify({"error": "Failed to fetch nearby places."}), 500

    return blueprint
