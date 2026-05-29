"""Prediction and dataset filtering API routes."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from backend.services.prediction_service import PredictionService
from backend.utils.request_helpers import prediction_filters


def create_prediction_routes(service: PredictionService) -> Blueprint:
    blueprint = Blueprint("prediction", __name__)

    @blueprint.get("/health")
    def health() -> tuple[Any, int]:
        return (
            jsonify(
                {
                    "status": "ok",
                    "rows": service.dataset_rows,
                    "model_r2_score": round(service.score, 4),
                    "mae": round(service.mae, 2),
                }
            ),
            200,
        )

    @blueprint.post("/predict")
    def predict() -> tuple[Any, int]:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"error": "Request body must be a JSON object."}), 400

        try:
            return jsonify(service.predict(payload)), 200
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception:
            return jsonify({"error": "Prediction failed due to an internal error."}), 500

    @blueprint.get("/filter-options")
    def filter_options() -> tuple[Any, int]:
        return jsonify(service.filter_options(**prediction_filters(request))), 200

    @blueprint.post("/match-row")
    def match_row() -> tuple[Any, int]:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"error": "Request body must be a JSON object."}), 400
        return jsonify({"match": service.matched_property(payload)}), 200

    @blueprint.get("/options")
    def options() -> tuple[Any, int]:
        return jsonify({"options": service.options()}), 200

    return blueprint
