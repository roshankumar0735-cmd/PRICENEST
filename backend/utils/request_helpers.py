"""Request parsing helpers shared by route modules."""

from __future__ import annotations

from flask import Request


def bounded_int(request: Request, name: str, default: int, minimum: int, maximum: int) -> int:
    value = request.args.get(name, default=default, type=int)
    return max(minimum, min(value, maximum))


def prediction_filters(request: Request) -> dict[str, str]:
    keys = [
        "city",
        "location",
        "property_type",
        "bedrooms",
        "floor",
        "facing",
        "balcony",
        "parking",
        "carpet_area",
        "carpet_area_unit",
        "original_carpet_area",
        "original_carpet_area_unit",
    ]
    return {key: request.args.get(key, default="", type=str) for key in keys}
