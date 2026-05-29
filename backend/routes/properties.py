"""Property search and listing routes."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from backend.services.prediction_service import PredictionService
from backend.utils.request_helpers import bounded_int


def _search_properties(service: PredictionService, query: str, limit: int) -> list[dict[str, Any]]:
    properties = service.properties(limit=500)
    query = query.strip().lower()
    if query:
        properties = [
            item
            for item in properties
            if query
            in f"{item.get('property_name', '')} {item.get('city', '')} {item.get('location', '')}".lower()
        ]
    return properties[:limit]


def create_property_routes(service: PredictionService) -> Blueprint:
    blueprint = Blueprint("properties", __name__)

    @blueprint.get("/search")
    def search() -> tuple[Any, int]:
        query = request.args.get("q", default="", type=str)
        limit = bounded_int(request, "limit", 8, 1, 20)
        try:
            return jsonify({"results": service.search_suggestions(query=query, limit=limit)}), 200
        except Exception as exc:
            return jsonify({"error": str(exc), "results": []}), 200

    @blueprint.get("/search/properties")
    def search_properties() -> tuple[Any, int]:
        query = request.args.get("q", default="", type=str)
        limit = bounded_int(request, "limit", 20, 1, 100)
        try:
            return jsonify({"properties": _search_properties(service, query, limit)}), 200
        except Exception as exc:
            return jsonify({"error": str(exc), "properties": []}), 200

    @blueprint.get("/properties")
    def properties() -> tuple[Any, int]:
        limit = bounded_int(request, "limit", 24, 1, 100)
        q = request.args.get("q", default="", type=str)
        city = request.args.get("city", default=None, type=str)
        location = request.args.get("location", default=None, type=str)

        try:
            rows = _search_properties(service, q, 500)
            if city:
                rows = [item for item in rows if str(item.get("city", "")).lower() == city.lower()]
            if location:
                rows = [item for item in rows if str(item.get("location", "")).lower() == location.lower()]
            return jsonify({"properties": rows[:limit]}), 200
        except Exception as exc:
            return jsonify({"error": str(exc), "properties": []}), 200

    @blueprint.get("/top-properties")
    def top_properties() -> tuple[Any, int]:
        limit = bounded_int(request, "limit", 8, 1, 24)
        rows = service.properties(limit=limit)
        return jsonify({"top_properties": rows, "properties": rows}), 200

    @blueprint.get("/locations")
    def locations() -> tuple[Any, int]:
        city = request.args.get("city", default=None, type=str)
        return jsonify({"options": service.locations(city=city)}), 200

    return blueprint
