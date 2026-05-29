"""Market insight routes."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify

from backend.services.prediction_service import PredictionService


def create_insight_routes(service: PredictionService) -> Blueprint:
    blueprint = Blueprint("insights", __name__)

    @blueprint.get("/inventory")
    def inventory() -> tuple[Any, int]:
        inventory_data = service.inventory()
        return jsonify({"inventory": inventory_data, **inventory_data}), 200

    @blueprint.get("/demand")
    def demand() -> tuple[Any, int]:
        return jsonify({"demand": service.demand()}), 200

    return blueprint
