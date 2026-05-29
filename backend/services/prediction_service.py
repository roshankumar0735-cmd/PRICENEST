"""Service facade over the PriceNest ML/data model."""

from __future__ import annotations

from typing import Any

from backend.model import PriceNestModel


class PredictionService:
    """Expose model operations to routes without coupling endpoints to ML internals."""

    def __init__(self) -> None:
        self.model = PriceNestModel()

    @property
    def dataset_rows(self) -> int:
        return self.model.dataset_rows

    @property
    def score(self) -> float:
        return self.model.score

    @property
    def mae(self) -> float:
        return self.model.mae

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.model.predict(payload)

    def matched_property(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.model.matched_property(payload)

    def search_suggestions(self, query: str, limit: int) -> list[dict[str, str]]:
        return self.model.search_suggestions(query=query, limit=limit)

    def properties(self, limit: int) -> list[dict[str, Any]]:
        return self.model.properties(limit=limit)

    def inventory(self) -> dict[str, int]:
        return self.model.inventory()

    def demand(self) -> list[dict[str, Any]]:
        return self.model.demand()

    def locations(self, city: str | None = None) -> list[str]:
        return self.model.locations(city=city)

    def filter_options(self, **filters: Any) -> dict[str, list[Any]]:
        return self.model.filter_options(**filters)

    def options(self) -> dict[str, list[Any]]:
        return self.model.options()

    def nearby_places(
        self,
        *,
        location_label: str,
        api_key: str,
        radius_m: int,
        limit_per_type: int,
    ) -> dict[str, Any]:
        return self.model.nearby_places(
            location_label=location_label,
            api_key=api_key,
            radius_m=radius_m,
            limit_per_type=limit_per_type,
        )
