from __future__ import annotations

import json
import math
import random
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "properties.csv"

NUMERIC_FEATURES = [
    "rate_per_sqft",
    "carpet_area_sqft",
    "total_area",
    "bathroom",
    "balcony",
    "bedrooms",
]

CATEGORICAL_FEATURES = [
    "property_type",
    "status",
    "floor",
    "transaction_type",
    "facing",
    "overlooking",
    "ownership",
    "parking",
    "city",
    "location",
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

DATASET_AMENITY_FIELDS = {
    "garden_park": "Garden/Park",
    "main_road": "Main Road",
    "pool": "Pool",
}

PROPERTY_TYPE_UI_LABELS = {
    "Apartment": "Apartment/Flat",
    "Flat": "Apartment/Flat",
    "House": "House",
    "Villa": "Villa",
    "Studio Apartment": "Studio Apartment",
}

PROPERTY_TYPE_UI_ORDER = ["Apartment/Flat", "House", "Villa", "Studio Apartment"]

ARTIFICIAL_AMENITY_FIELDS = {
    "gym": "Gym",
    "lift": "Lift",
    "security": "Security",
    "power_backup": "Power Backup",
}

LUXURY_LOCALITIES = {
    "dlf phase 1",
    "dlf city phase 1",
    "dlf city plot phase 1",
    "dlf phase 2",
    "dlf city phase 2",
    "golf course road",
    "golf course extension road",
    "vasant vihar",
    "greater kailash",
    "sushant lok",
    "sushant lok-i",
    "defence colony",
    "hauz khas",
    "south city 1",
    "sector 54",
}

PREMIUM_SOUTH_DELHI_TERMS = {
    "vasant vihar",
    "greater kailash",
    "defence colony",
    "hauz khas",
    "panchsheel",
    "anand niketan",
    "green park",
    "south extension",
    "saket",
}

FACING_ORDER = [
    "East",
    "West",
    "South",
    "North",
    "North-East",
    "North-West",
    "South-East",
    "South-West",
]

CANONICAL_COLUMNS = [
    "property_name",
    "price",
    "rate_per_sqft",
    "property_type",
    "carpet_area",
    "total_area",
    "status",
    "floor",
    "transaction_type",
    "facing",
    "overlooking",
    "ownership",
    "parking",
    "bathroom",
    "balcony",
    "city",
    "location",
    "bedrooms",
]

ALIAS_PATTERNS: dict[str, set[str]] = {
    "property_name": {"propertyname", "name", "title", "listingname"},
    "price": {"price", "targetprice", "amount", "cost"},
    "rate_per_sqft": {"ratepersqft", "ratepersquarefeet", "pricepersqft", "rate", "ppsf"},
    "property_type": {"propertytype", "type"},
    "carpet_area": {"carpetarea", "carpetareasqft", "carpetareasquarefeet", "carpet"},
    "total_area": {"totalarea", "superarea", "builtuparea", "area", "saleablearea"},
    "status": {"status", "constructionstatus"},
    "floor": {"floor", "floorno", "floordetails"},
    "transaction_type": {"transactiontype", "transaction", "dealingtype"},
    "facing": {"facing", "direction"},
    "overlooking": {"overlooking", "view"},
    "ownership": {"ownership", "ownershiptype"},
    "parking": {"parking", "parkingdetails"},
    "bathroom": {"bathroom", "bathrooms", "toilets"},
    "balcony": {"balcony", "balconies"},
    "city": {"city", "town"},
    "location": {"location", "locality", "address", "area_name"},
    "bedrooms": {"bedroom", "bedrooms", "bhk", "beds"},
}


def clean_text(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\ufeff", "")).strip()


def to_number(value: Any) -> float:
    if value is None:
        return np.nan
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"-?\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(match.group(0)) if match else np.nan


def area_unit(value: Any) -> str:
    text = clean_text(value).lower()
    if re.search(r"\bsq\.?\s*yd\b|\bsqyrd\b|\bsquare\s*yard", text):
        return "sqyrd"
    if re.search(r"\bsq\.?\s*m\b|\bsqm\b|\bsquare\s*meter|\bsquare\s*metre", text):
        return "sqm"
    if re.search(r"\bsq\.?\s*ft\b|\bsqft\b|\bsquare\s*feet|\bsquare\s*foot", text):
        return "sqft"
    return ""


AREA_SQFT_FACTORS = {
    "sqft": 1.0,
    "sqm": 10.7639,
    "sqyrd": 9.0,
}


def convert_rate_unit(rate: float, source_unit: str, target_unit: str) -> float:
    source = clean_text(source_unit).lower() or "sqft"
    target = clean_text(target_unit).lower() or source
    if np.isnan(rate) or rate <= 0:
        return np.nan
    source_factor = AREA_SQFT_FACTORS.get(source, 1.0)
    target_factor = AREA_SQFT_FACTORS.get(target, source_factor)
    rate_per_sqft = float(rate) / source_factor
    return rate_per_sqft * target_factor


def normalize_to_sqft(area: float, unit: str) -> float:
    source = clean_text(unit).lower() or "sqft"
    if np.isnan(area) or area <= 0:
        return np.nan
    source_factor = AREA_SQFT_FACTORS.get(source, 1.0)
    return float(area) * source_factor


def convert_area(area: float, source_unit: str, target_unit: str) -> float:
    source = clean_text(source_unit).lower() or "sqft"
    target = clean_text(target_unit).lower() or source
    if np.isnan(area) or area <= 0:
        return np.nan
    source_factor = AREA_SQFT_FACTORS.get(source, 1.0)
    target_factor = AREA_SQFT_FACTORS.get(target, source_factor)
    return (float(area) * source_factor) / target_factor


def infer_property_type(*texts: Any) -> str:
    merged = " ".join(clean_text(t).lower() for t in texts)
    if "studio apartment" in merged or "studio" in merged:
        return "Studio Apartment"
    if "villa" in merged:
        return "Villa"
    if "plot" in merged or "land" in merged:
        return "Plot"
    if "independent floor" in merged or "builder floor" in merged:
        return "Independent Floor"
    if "house" in merged:
        return "House"
    if "flat" in merged:
        return "Apartment"
    return "Apartment"


def property_type_ui_label(value: Any) -> str:
    text = clean_text(value)
    lower = text.lower()
    if "studio apartment" in lower or lower == "studio":
        return "Studio Apartment"
    if "villa" in lower:
        return "Villa"
    if "house" in lower:
        return "House"
    if "flat" in lower or "apartment" in lower:
        return "Apartment/Flat"
    return PROPERTY_TYPE_UI_LABELS.get(text, "")


def property_type_model_value(value: Any) -> str:
    label = property_type_ui_label(value)
    return {
        "Apartment/Flat": "Apartment",
        "House": "House",
        "Villa": "Villa",
        "Studio Apartment": "Studio Apartment",
    }.get(label, clean_text(value))


def dataset_property_type_label(row: Any) -> str:
    if hasattr(row, "get"):
        property_name = row.get("property_name", "")
        property_type = row.get("property_type", "")
    else:
        property_name = getattr(row, "property_name", "")
        property_type = getattr(row, "property_type", "")
    return property_type_ui_label(
        infer_property_type(property_name, property_type)
    )


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def is_yes(value: Any) -> bool:
    return clean_text(value).lower() == "yes"


def normalize_facing(value: Any) -> str:
    text = clean_text(value).replace(" -", "-").replace("- ", "-")
    return {
        "Northeast": "North-East",
        "NorthEast": "North-East",
        "North - East": "North-East",
        "Northwest": "North-West",
        "NorthWest": "North-West",
        "North - West": "North-West",
        "Southeast": "South-East",
        "SouthEast": "South-East",
        "South - East": "South-East",
        "Southwest": "South-West",
        "SouthWest": "South-West",
        "South -West": "South-West",
        "South - West": "South-West",
    }.get(text, text)


def parking_sort_key(value: str) -> tuple[int, int, str]:
    text = clean_text(value).rstrip(",")
    number = int(to_number(text)) if not np.isnan(to_number(text)) else 999
    kind_rank = 0 if "covered" in text.lower() else 1 if "open" in text.lower() else 2
    return (number, kind_rank, text)


def _find_column(raw: pd.DataFrame, canonical_name: str) -> str | None:
    aliases = ALIAS_PATTERNS.get(canonical_name, set())
    normalized_map = {normalize_key(str(col)): str(col) for col in raw.columns}

    for alias in aliases:
        if alias in normalized_map:
            return normalized_map[alias]

    for alias in aliases:
        for norm_col, original_col in normalized_map.items():
            if alias in norm_col:
                return original_col

    return None


def _series_from(df: pd.DataFrame, column: str, default: Any = "") -> pd.Series:
    if column in df.columns:
        return df[column]
    return pd.Series([default] * len(df), index=df.index)


def load_dataset(path: Path = DATA_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at '{path}'. Create backend/data.csv before starting the API."
        )

    raw = pd.read_csv(path)
    mapped_cols: dict[str, str] = {}
    for canonical in CANONICAL_COLUMNS:
        found = _find_column(raw, canonical)
        if found:
            mapped_cols[canonical] = found

    df = pd.DataFrame(index=raw.index)
    df["property_name"] = _series_from(raw, mapped_cols.get("property_name", ""), "").map(clean_text)
    df["price"] = _series_from(raw, mapped_cols.get("price", ""), np.nan).map(to_number)
    df["rate_per_sqft"] = _series_from(raw, mapped_cols.get("rate_per_sqft", ""), np.nan).map(to_number)
    carpet_area_col = mapped_cols.get("carpet_area", "")
    for candidate in raw.columns:
        normalized_candidate = normalize_key(str(candidate))
        if normalized_candidate in {"carpetarea", "carpet"}:
            candidate_series = raw[candidate].map(clean_text)
            if candidate_series.str.contains(r"\bsq|square", case=False, regex=True, na=False).any():
                carpet_area_col = str(candidate)
                break

    raw_carpet_area = _series_from(raw, carpet_area_col, np.nan)
    df["carpet_area"] = raw_carpet_area.map(to_number)
    df["carpet_area_unit"] = raw_carpet_area.map(area_unit)
    df["carpet_area_sqft"] = df["carpet_area"]
    df["total_area"] = _series_from(raw, mapped_cols.get("total_area", ""), np.nan).map(to_number)
    df["bathroom"] = _series_from(raw, mapped_cols.get("bathroom", ""), np.nan).map(to_number)
    df["balcony"] = _series_from(raw, mapped_cols.get("balcony", ""), np.nan).map(to_number)
    df["bedrooms"] = _series_from(raw, mapped_cols.get("bedrooms", ""), np.nan).map(to_number)

    df["property_type"] = _series_from(raw, mapped_cols.get("property_type", ""), "").map(clean_text)
    for col in ["status", "floor", "transaction_type", "facing", "overlooking", "ownership", "parking", "city", "location"]:
        df[col] = _series_from(raw, mapped_cols.get(col, ""), "").map(clean_text)

    if df["rate_per_sqft"].isna().all() and not df["price"].isna().all() and not df["total_area"].isna().all():
        df["rate_per_sqft"] = df["price"] / df["total_area"]

    if df["total_area"].isna().all() and not df["carpet_area"].isna().all():
        df["total_area"] = df["carpet_area"]

    inferred = [infer_property_type(df.at[i, "property_name"], df.at[i, "property_type"]) for i in df.index]
    inferred_series = pd.Series(inferred, index=df.index)
    usable_type = df["property_type"].map(property_type_ui_label).astype(bool)
    df.loc[~usable_type, "property_type"] = inferred_series.loc[~usable_type]
    df["property_type"] = df["property_type"].replace("", np.nan).fillna(inferred_series)

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=["price"])
    df = df[df["price"] > 0].copy()
    df.reset_index(drop=True, inplace=True)
    return df


class PriceNestModel:
    def __init__(self) -> None:
        self.df = load_dataset()
        self.pipeline: Pipeline | None = None
        self.score = 0.0
        self.mae = 0.0
        self.dataset_rows = len(self.df)
        self.train()

    def train(self) -> None:
        x = self.df[FEATURES]
        y = self.df["price"]

        x_train, x_test, y_train, y_test = train_test_split(
            x,
            y,
            test_size=0.2,
            random_state=42,
        )

        preprocessor = ColumnTransformer(
            transformers=[
                ("num", Pipeline([("imputer", SimpleImputer(strategy="median"))]), NUMERIC_FEATURES),
                (
                    "cat",
                    Pipeline(
                        [
                            ("imputer", SimpleImputer(strategy="most_frequent")),
                            ("encoder", OneHotEncoder(handle_unknown="ignore")),
                        ]
                    ),
                    CATEGORICAL_FEATURES,
                ),
            ]
        )

        self.pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=300,
                        random_state=42,
                        min_samples_leaf=2,
                        n_jobs=-1,
                    ),
                ),
            ]
        )

        self.pipeline.fit(x_train, y_train)
        predictions = self.pipeline.predict(x_test)
        self.score = float(max(0.0, min(1.0, r2_score(y_test, predictions))))
        self.mae = float(mean_absolute_error(y_test, predictions))

    def _payload_to_row(self, payload: dict[str, Any]) -> dict[str, Any]:
        property_name = clean_text(payload.get("property_name"))
        property_type = property_type_model_value(payload.get("property_type")) or infer_property_type(property_name)
        carpet_area = to_number(payload.get("carpet_area_sqft", payload.get("carpet_area")))
        total_area = to_number(payload.get("total_area"))
        if np.isnan(total_area):
            total_area = self._dataset_total_area_for_selection(payload, carpet_area)
        if np.isnan(total_area):
            total_area = carpet_area
        selected_dataset_amenities = [
            label for key, label in DATASET_AMENITY_FIELDS.items() if is_yes(payload.get(key))
        ]
        overlooking = ", ".join(selected_dataset_amenities) or clean_text(payload.get("overlooking"))

        return {
            "rate_per_sqft": to_number(payload.get("rate_per_sqft")),
            "carpet_area_sqft": carpet_area,
            "total_area": total_area,
            "bathroom": to_number(payload.get("bathroom")),
            "balcony": to_number(payload.get("balcony")),
            "bedrooms": to_number(payload.get("bedrooms", payload.get("bhk"))),
            "property_type": property_type,
            "status": clean_text(payload.get("status")),
            "floor": clean_text(payload.get("floor")),
            "transaction_type": clean_text(payload.get("transaction_type")),
            "facing": clean_text(payload.get("facing")),
            "overlooking": overlooking,
            "ownership": clean_text(payload.get("ownership")),
            "parking": clean_text(payload.get("parking")),
            "city": clean_text(payload.get("city")),
            "location": clean_text(payload.get("location")),
        }

    def _dataset_total_area_for_selection(self, payload: dict[str, Any], carpet_area: float) -> float:
        if np.isnan(carpet_area):
            return np.nan

        city = clean_text(payload.get("city")).lower()
        location = clean_text(payload.get("location")).lower()
        unit = clean_text(payload.get("carpet_area_unit") or "sqft").lower()
        df = self.df

        if city:
            df = df[df["city"].astype(str).str.lower() == city]
        if location:
            df = df[df["location"].astype(str).str.lower() == location]
        if unit:
            unit_mask = df["carpet_area_unit"].astype(str).str.lower() == unit
            if unit == "sqft":
                unit_mask = unit_mask | (df["carpet_area_unit"].astype(str).str.strip() == "")
            df = df[unit_mask]

        matches = df[np.isclose(df["carpet_area"].astype(float), float(carpet_area), rtol=0, atol=0.01)]
        values = matches["total_area"].dropna()
        if values.empty:
            return np.nan
        return float(values.iloc[0])

    def _dataset_row_for_selection(self, payload: dict[str, Any], include_area: bool = True) -> pd.Series | None:
        df = self._filter_matching_dataset_rows(payload, include_area=include_area)
        if df.empty:
            return None

        exact_fields = [
            ("bedrooms", lambda series, value: series.dropna().astype(float).eq(float(value))),
            ("balcony", lambda series, value: series.dropna().astype(float).eq(float(value))),
            ("floor", lambda series, value: series.astype(str).map(clean_text).str.lower().eq(clean_text(value).lower())),
            ("facing", lambda series, value: series.map(normalize_facing).str.lower().eq(normalize_facing(value).lower())),
            ("parking", lambda series, value: series.astype(str).map(clean_text).str.rstrip(",").str.lower().eq(clean_text(value).rstrip(",").lower())),
        ]

        scored = df.copy()
        scored["_match_score"] = 0
        for field, matcher in exact_fields:
            value = payload.get(field)
            if clean_text(value):
                try:
                    mask = matcher(scored[field], value).reindex(scored.index, fill_value=False)
                    scored.loc[mask, "_match_score"] += 2
                except (TypeError, ValueError):
                    pass

        property_type = property_type_ui_label(payload.get("property_type"))
        if property_type:
            type_mask = scored.apply(lambda item: dataset_property_type_label(item) == property_type, axis=1)
            scored.loc[type_mask, "_match_score"] += 3

        carpet_area = to_number(payload.get("original_carpet_area", payload.get("carpet_area_sqft", payload.get("carpet_area"))))
        carpet_unit = clean_text(payload.get("original_carpet_area_unit", payload.get("carpet_area_unit"))).lower()
        if include_area and not np.isnan(carpet_area):
            area_mask = np.isclose(scored["carpet_area"].astype(float), float(carpet_area), rtol=0, atol=0.01)
            if carpet_unit:
                unit_mask = scored["carpet_area_unit"].astype(str).str.lower().eq(carpet_unit)
                if carpet_unit == "sqft":
                    unit_mask = unit_mask | scored["carpet_area_unit"].astype(str).str.strip().eq("")
                area_mask = area_mask & unit_mask
            scored.loc[area_mask, "_match_score"] += 4

        exact = scored
        for field, matcher in exact_fields:
            value = payload.get(field)
            if clean_text(value):
                try:
                    exact_mask = matcher(exact[field], value).reindex(exact.index, fill_value=False)
                    narrowed = exact.loc[exact_mask]
                    if not narrowed.empty:
                        exact = narrowed
                except (TypeError, ValueError):
                    pass
        if property_type:
            narrowed = exact.loc[exact.apply(lambda item: dataset_property_type_label(item) == property_type, axis=1)]
            if not narrowed.empty:
                exact = narrowed
        if include_area and not np.isnan(carpet_area):
            exact_area_mask = np.isclose(exact["carpet_area"].astype(float), float(carpet_area), rtol=0, atol=0.01)
            if carpet_unit:
                exact_unit_mask = exact["carpet_area_unit"].astype(str).str.lower().eq(carpet_unit)
                if carpet_unit == "sqft":
                    exact_unit_mask = exact_unit_mask | exact["carpet_area_unit"].astype(str).str.strip().eq("")
                exact_area_mask = exact_area_mask & exact_unit_mask
            narrowed = exact.loc[exact_area_mask]
            if not narrowed.empty:
                exact = narrowed

        source = exact if not exact.empty else scored
        source = source.sort_values(["_match_score", "price"], ascending=[False, False])
        return source.iloc[0].drop(labels=["_match_score"], errors="ignore")

    def _filter_matching_dataset_rows(
        self,
        payload: dict[str, Any],
        *,
        include_area: bool = False,
        stop_before: str | None = None,
    ) -> pd.DataFrame:
        order = ["city", "location", "property_type", "bedrooms", "floor", "facing", "balcony", "parking", "carpet_area"]
        df = self.df.copy()

        for field in order:
            if stop_before == field:
                break

            if field == "city":
                city = clean_text(payload.get("city")).lower()
                if city:
                    df = df[df["city"].astype(str).str.lower() == city]
            elif field == "location":
                location = clean_text(payload.get("location")).lower()
                if location:
                    df = df[df["location"].astype(str).str.lower() == location]
            elif field == "property_type":
                property_type = property_type_ui_label(payload.get("property_type"))
                if property_type:
                    df = df[df.apply(lambda item: dataset_property_type_label(item) == property_type, axis=1)]
            elif field == "bedrooms":
                bedrooms = to_number(payload.get("bedrooms"))
                if not np.isnan(bedrooms):
                    df = df[df["bedrooms"].astype(float).eq(float(bedrooms))]
            elif field == "floor":
                floor = clean_text(payload.get("floor")).lower()
                if floor:
                    df = df[df["floor"].astype(str).map(clean_text).str.lower() == floor]
            elif field == "facing":
                facing = normalize_facing(payload.get("facing")).lower()
                if facing:
                    df = df[df["facing"].map(normalize_facing).str.lower() == facing]
            elif field == "balcony":
                balcony = to_number(payload.get("balcony"))
                if not np.isnan(balcony):
                    df = df[df["balcony"].astype(float).eq(float(balcony))]
            elif field == "parking":
                parking = clean_text(payload.get("parking")).rstrip(",").lower()
                if parking:
                    df = df[df["parking"].astype(str).map(clean_text).str.rstrip(",").str.lower() == parking]
            elif field == "carpet_area" and include_area:
                carpet_area = to_number(payload.get("original_carpet_area", payload.get("carpet_area_sqft", payload.get("carpet_area"))))
                carpet_unit = clean_text(payload.get("original_carpet_area_unit", payload.get("carpet_area_unit"))).lower()
                if not np.isnan(carpet_area):
                    area_mask = np.isclose(df["carpet_area"].astype(float), float(carpet_area), rtol=0, atol=0.01)
                    if carpet_unit:
                        unit_mask = df["carpet_area_unit"].astype(str).str.lower() == carpet_unit
                        if carpet_unit == "sqft":
                            unit_mask = unit_mask | (df["carpet_area_unit"].astype(str).str.strip() == "")
                        area_mask = area_mask & unit_mask
                    df = df[area_mask]

            if df.empty:
                return df

        return df

    def _validate_payload(self, payload: dict[str, Any], row: dict[str, Any]) -> None:
        required_fields = ["city", "location", "bedrooms"]
        missing = [field for field in required_fields if not clean_text(payload.get(field))]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        if np.isnan(row["bedrooms"]) or row["bedrooms"] <= 0:
            raise ValueError("bedrooms must be a valid positive number.")

    def _confidence(self, row: dict[str, Any], predicted_price: float) -> float:
        completeness_fields = [
            "city",
            "location",
            "property_type",
            "total_area",
            "rate_per_sqft",
            "bedrooms",
            "bathroom",
        ]
        completeness = sum(
            (not pd.isna(row.get(key))) and bool(clean_text(row.get(key)) if key in CATEGORICAL_FEATURES else row.get(key))
            for key in completeness_fields
        ) / len(completeness_fields)

        city = clean_text(row.get("city")).lower()
        location = clean_text(row.get("location")).lower()
        local_matches = ((self.df["city"].str.lower() == city) & (self.df["location"].str.lower() == location)).sum()
        support = min(1.0, float(local_matches) / 20.0)

        rel_error_component = min(1.0, self.mae / max(predicted_price, 1.0))
        confidence = 0.45 * self.score + 0.30 * completeness + 0.25 * support - 0.10 * rel_error_component
        return float(max(0.3, min(0.99, confidence)))

    def _amenity_increment_range(self, row: dict[str, Any]) -> tuple[int, int]:
        city = clean_text(row.get("city")).lower()
        location = clean_text(row.get("location")).lower()
        bedrooms = to_number(row.get("bedrooms"))
        total_area = to_number(row.get("total_area"))

        is_luxury_locality = any(term in location for term in LUXURY_LOCALITIES)
        is_premium_south_delhi = city == "delhi" and any(term in location for term in PREMIUM_SOUTH_DELHI_TERMS)
        is_large_luxury_home = (
            not np.isnan(bedrooms)
            and not np.isnan(total_area)
            and bedrooms >= 4
            and total_area >= 2500
        )

        if is_luxury_locality or (city == "gurgaon" and is_large_luxury_home):
            return (80000, 100000)
        if is_premium_south_delhi:
            return (60000, 100000)
        if city == "ghaziabad":
            return (30000, 45000)
        if city == "faridabad":
            return (30000, 50000)
        if city in {"noida", "greater noida"}:
            return (30000, 70000)
        if is_large_luxury_home:
            return (50000, 90000)
        return (30000, 60000)

    def _amenity_price_boost(self, payload: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
        selected = [
            label for key, label in ARTIFICIAL_AMENITY_FIELDS.items() if is_yes(payload.get(key))
        ]
        if not selected:
            return {"total": 0, "items": []}

        low, high = self._amenity_increment_range(row)
        items = [
            {"amenity": amenity, "increment": random.randint(low, high)}
            for amenity in selected
        ]
        return {"total": sum(item["increment"] for item in items), "items": items}

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.pipeline is None:
            raise RuntimeError("Model is not trained yet.")

        row = self._payload_to_row(payload)
        self._validate_payload(payload, row)
        dataset_row = self._dataset_row_for_selection(payload)

        model_price = float(self.pipeline.predict(pd.DataFrame([row]))[0])
        base_price = model_price
        base_rate = np.nan
        dataset_carpet_area = np.nan
        dataset_carpet_unit = clean_text(payload.get("carpet_area_unit") or "")
        selected_rate_unit = clean_text(payload.get("carpet_area_unit") or "")
        dataset_total_area = to_number(row.get("total_area"))
        property_name = clean_text(payload.get("property_name", "Predicted Property"))

        if dataset_row is not None:
            base_price = float(dataset_row.get("price"))
            base_rate = to_number(dataset_row.get("rate_per_sqft"))
            dataset_carpet_area = to_number(dataset_row.get("carpet_area"))
            dataset_carpet_unit = clean_text(dataset_row.get("carpet_area_unit")) or dataset_carpet_unit or "sqft"
            selected_rate_unit = selected_rate_unit or dataset_carpet_unit
            dataset_total_area = to_number(dataset_row.get("total_area"))
            property_name = clean_text(dataset_row.get("property_name")) or property_name
            row["total_area"] = dataset_total_area
            row["carpet_area_sqft"] = dataset_carpet_area
            row["rate_per_sqft"] = base_rate

        total_area = float(dataset_total_area) if not np.isnan(dataset_total_area) else np.nan
        if np.isnan(base_rate) or base_rate <= 0:
            if not np.isnan(total_area) and total_area > 0:
                base_rate = base_price / total_area
            else:
                base_rate = np.nan
        if np.isnan(dataset_carpet_area):
            dataset_carpet_area = to_number(payload.get("carpet_area_sqft", payload.get("carpet_area")))
        if not dataset_carpet_unit:
            dataset_carpet_unit = clean_text(payload.get("carpet_area_unit") or "sqft")
        selected_rate_unit = selected_rate_unit or dataset_carpet_unit or "sqft"
        display_rate = convert_rate_unit(base_rate, dataset_carpet_unit or "sqft", selected_rate_unit)
        selected_carpet_area = to_number(payload.get("carpet_area_sqft", payload.get("carpet_area")))
        if np.isnan(selected_carpet_area):
            selected_carpet_area = dataset_carpet_area

        original_unit = clean_text(dataset_carpet_unit or "sqft").lower()
        target_unit = clean_text(selected_rate_unit or original_unit).lower()
        normalized_carpet_area_sqft = normalize_to_sqft(dataset_carpet_area, original_unit)
        normalized_total_area_sqft = float(total_area) if not np.isnan(total_area) and total_area > 0 else np.nan
        loading_factor = 1.0
        if (
            not np.isnan(normalized_carpet_area_sqft)
            and normalized_carpet_area_sqft > 0
            and not np.isnan(normalized_total_area_sqft)
            and normalized_total_area_sqft > 0
        ):
            loading_factor = float(normalized_total_area_sqft) / float(normalized_carpet_area_sqft)
        original_total_area = (
            float(dataset_carpet_area) * loading_factor
            if not np.isnan(dataset_carpet_area) and dataset_carpet_area > 0
            else np.nan
        )
        display_total_area = (
            float(selected_carpet_area) * loading_factor
            if not np.isnan(selected_carpet_area) and selected_carpet_area > 0
            else np.nan
        )
        is_original_dataset_area = (
            target_unit == original_unit
            and not np.isnan(selected_carpet_area)
            and not np.isnan(dataset_carpet_area)
            and math.isclose(float(selected_carpet_area), float(dataset_carpet_area), rel_tol=0, abs_tol=0.01)
        )
        dynamic_base_price = base_price
        if not is_original_dataset_area and not np.isnan(selected_carpet_area) and selected_carpet_area > 0 and not np.isnan(display_rate):
            dynamic_base_price = float(selected_carpet_area) * float(display_rate)

        amenity_boost = self._amenity_price_boost(payload, row)
        predicted_price = dynamic_base_price + amenity_boost["total"]

        if not math.isfinite(predicted_price) or predicted_price <= 0:
            raise ValueError("Predicted price could not be calculated.")

        confidence_score = self._confidence(row=row, predicted_price=predicted_price)

        return {
            "property_name": property_name,
            "predicted_price": round(predicted_price, 2),
            "base_dataset_price": round(base_price, 2),
            "converted_base_price": round(dynamic_base_price, 2),
            "base_model_price": round(model_price, 2),
            "amenity_price_boost": amenity_boost,
            "price_per_sqft": None if np.isnan(display_rate) else round(float(display_rate), 2),
            "rate_unit": selected_rate_unit,
            "carpet_area": None if np.isnan(selected_carpet_area) else float(selected_carpet_area),
            "carpet_area_unit": target_unit or dataset_carpet_unit or "sqft",
            "total_area": None if np.isnan(display_total_area) else round(float(display_total_area), 2),
            "original_carpet_area": None if np.isnan(dataset_carpet_area) else float(dataset_carpet_area),
            "original_carpet_area_unit": dataset_carpet_unit or "sqft",
            "original_total_area": None if np.isnan(original_total_area) else round(float(original_total_area), 2),
            "normalized_carpet_area_sqft": None if np.isnan(normalized_carpet_area_sqft) else round(float(normalized_carpet_area_sqft), 2),
            "normalized_total_area_sqft": None if np.isnan(normalized_total_area_sqft) else round(float(normalized_total_area_sqft), 2),
            "loading_factor": round(float(loading_factor), 6),
            "original_rate": None if np.isnan(base_rate) else round(float(base_rate), 2),
            "original_rate_unit": dataset_carpet_unit or "sqft",
            "confidence_score": round(confidence_score, 3),
            "city": clean_text(row.get("city", "")),
            "location": clean_text(row.get("location", "")),
        }

    def matched_property(self, payload: dict[str, Any]) -> dict[str, Any]:
        dataset_row = self._dataset_row_for_selection(payload, include_area=False)
        if dataset_row is None:
            return {}

        carpet_area = to_number(dataset_row.get("carpet_area"))
        total_area = to_number(dataset_row.get("total_area"))
        rate = to_number(dataset_row.get("rate_per_sqft"))
        price = to_number(dataset_row.get("price"))
        unit = clean_text(dataset_row.get("carpet_area_unit")) or "sqft"

        return {
            "property_name": clean_text(dataset_row.get("property_name")),
            "price": None if np.isnan(price) else round(float(price), 2),
            "rate": None if np.isnan(rate) else round(float(rate), 2),
            "carpet_area": "" if np.isnan(carpet_area) else (
                str(int(carpet_area)) if float(carpet_area).is_integer() else str(round(float(carpet_area), 2))
            ),
            "carpet_area_unit": unit,
            "total_area": None if np.isnan(total_area) else round(float(total_area), 2),
            "city": clean_text(dataset_row.get("city")),
            "location": clean_text(dataset_row.get("location")),
        }

    def search(self, query: str, limit: int = 10) -> list[dict[str, str]]:
        q = clean_text(query).lower()
        pairs = self.df[["city", "location"]].dropna().drop_duplicates()
        if q:
            mask = pairs["city"].str.lower().str.contains(q, na=False) | pairs["location"].str.lower().str.contains(q, na=False)
            pairs = pairs.loc[mask]
        pairs = pairs.head(limit)

        return [
            {
                "city": clean_text(row.city),
                "location": clean_text(row.location),
                "label": f"{clean_text(row.location)}, {clean_text(row.city)}",
            }
            for row in pairs.itertuples()
        ]

    def properties(
        self,
        q: str = "",
        city: str | None = None,
        location: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Fetch properties with optional filtering."""
        df = self.df.copy()

        if q:
            q = clean_text(q).lower()
            mask = (
                df["property_name"].astype(str).str.lower().str.contains(q, na=False)
                | df["city"].astype(str).str.lower().str.contains(q, na=False)
                | df["location"].astype(str).str.lower().str.contains(q, na=False)
            )
            df = df[mask]

        if city:
            df = df[df["city"].astype(str).str.lower() == city.lower()]

        if location:
            df = df[df["location"].astype(str).str.lower() == location.lower()]

        cols = [
            "property_name",
            "price",
            "rate_per_sqft",
            "property_type",
            "carpet_area",
            "total_area",
            "status",
            "city",
            "location",
            "bedrooms",
        ]

        records = df[cols].head(limit).to_dict(orient="records")
        normalized = []

        for item in records:
            normalized.append({
                "property_name": clean_text(item.get("property_name")),
                "price": round(float(item.get("price", 0.0)), 2),
                "rate_per_sqft": None if pd.isna(item.get("rate_per_sqft")) else round(float(item["rate_per_sqft"]), 2),
                "property_type": clean_text(item.get("property_type")),
                "carpet_area": None if pd.isna(item.get("carpet_area")) else round(float(item["carpet_area"]), 2),
                "total_area": None if pd.isna(item.get("total_area")) else round(float(item["total_area"]), 2),
                "status": clean_text(item.get("status")),
                "city": clean_text(item.get("city")),
                "location": clean_text(item.get("location")),
                "bedrooms": None if pd.isna(item.get("bedrooms")) else int(float(item["bedrooms"])),
            })

        return normalized
    def supply(self) -> dict[str, int]:
        counts = self.df["property_type"].fillna("").map(clean_text).value_counts().to_dict()
        return {
            "Apartment": int(counts.get("Apartment", 0)),
            "Villa": int(counts.get("Villa", 0)),
            "Independent Floor": int(counts.get("Independent Floor", 0)),
            "Plot": int(counts.get("Plot", 0)),
        }

    def options(self) -> dict[str, list[str]]:
        options: dict[str, list[str]] = {}

        for col in CATEGORICAL_FEATURES:
            values = self.df[col].dropna().map(clean_text)
            options[col] = sorted(v for v in values.unique() if v)

        options["facing"] = [value for value in FACING_ORDER if value in {normalize_facing(v) for v in options.get("facing", [])}]
        options["parking"] = sorted(
            {clean_text(value).rstrip(",") for value in options.get("parking", []) if clean_text(value)},
            key=parking_sort_key,
        )

        options["bedrooms"] = sorted(
            (
                str(int(v))
                for v in self.df["bedrooms"].dropna().map(float).map(int).unique()
                if v > 0
            ),
            key=lambda value: int(value),
        )
        options["bathroom"] = sorted(
            str(int(v))
            for v in self.df["bathroom"].dropna().map(float).map(int).unique()
            if v > 0
        )
        options["balcony"] = sorted(
            (
                str(int(v))
                for v in self.df["balcony"].dropna().map(float).map(int).unique()
                if v > 0
            ),
            key=lambda value: int(value),
        )
        area_values_by_unit: dict[str, list[str]] = {}
        for unit in ["sqft", "sqm", "sqyrd"]:
            unit_mask = self.df["carpet_area_unit"] == unit
            if unit == "sqft":
                unit_mask = unit_mask | (self.df["carpet_area_unit"] == "")
            values = (
                self.df.loc[unit_mask, "carpet_area"]
                .dropna()
                .map(float)
                .unique()
            )
            area_values_by_unit[unit] = [
                str(int(value)) if float(value).is_integer() else str(round(float(value), 2))
                for value in sorted(values)
            ]

        options["carpet_area_units"] = ["sqft", "sqm", "sqyrd"]
        options["carpet_area_values_by_unit"] = area_values_by_unit
        property_type_labels = {
            property_type_ui_label(value)
            for value in self.df["property_type"].dropna().map(clean_text)
        }
        options["property_type"] = [label for label in PROPERTY_TYPE_UI_ORDER if label in property_type_labels]
        options["gym"] = ["Yes", "No"]
        options["lift"] = ["Yes", "No"]
        options["security"] = ["Yes", "No"]
        options["power_backup"] = ["Yes", "No"]
        options["garden_park"] = ["Yes", "No"]
        options["main_road"] = ["Yes", "No"]
        options["pool"] = ["Yes", "No"]
        return options

    def locations(self, city: str | None = None) -> list[str]:
        df = self.df
        if city:
            df = df[df["city"].astype(str).str.lower() == city.lower()]

        values = df["location"].dropna().map(clean_text)
        return sorted(v for v in values.unique() if v)

    def filter_options(self, **filters: Any) -> dict[str, list[Any]]:
        payload = {key: clean_text(value) for key, value in filters.items() if clean_text(value)}
        df = self._filter_matching_dataset_rows(payload, include_area=False)

        def df_for(field: str) -> pd.DataFrame:
            return self._filter_matching_dataset_rows(payload, include_area=False, stop_before=field)

        property_type_df = df_for("property_type")
        bedrooms_df = df_for("bedrooms")
        floor_df = df_for("floor")
        facing_df = df_for("facing")
        balcony_df = df_for("balcony")
        parking_df = df_for("parking")
        carpet_df = df_for("carpet_area")

        property_type_values = {
            property_type_ui_label(value)
            for value in property_type_df["property_type"].dropna().map(clean_text)
            if property_type_ui_label(value)
        }
        facing_values = {normalize_facing(value) for value in facing_df["facing"].dropna().map(clean_text) if clean_text(value)}
        parking_values = {
            clean_text(value).rstrip(",")
            for value in parking_df["parking"].dropna().map(clean_text)
            if clean_text(value)
        }
        overlooking_values = [clean_text(value) for value in df["overlooking"].dropna().map(clean_text) if clean_text(value)]
        amenity_options: dict[str, list[str]] = {}
        for key, label in DATASET_AMENITY_FIELDS.items():
            if not overlooking_values:
                amenity_options[key] = []
                continue
            has_yes = any(label.lower() in value.lower() for value in overlooking_values)
            has_no = any(label.lower() not in value.lower() for value in overlooking_values)
            amenity_options[key] = [value for value in ["Yes", "No"] if (value == "Yes" and has_yes) or (value == "No" and has_no)]
        area_values_by_unit: dict[str, list[str]] = {}
        total_area_by_carpet_area_unit: dict[str, dict[str, float]] = {}
        carpet_area_options: list[dict[str, Any]] = []
        for unit in ["sqft", "sqm", "sqyrd"]:
            unit_mask = carpet_df["carpet_area_unit"] == unit
            if unit == "sqft":
                unit_mask = unit_mask | (carpet_df["carpet_area_unit"] == "")
            unit_df = carpet_df.loc[unit_mask].dropna(subset=["carpet_area"])
            values = unit_df["carpet_area"].map(float).unique()
            area_values_by_unit[unit] = [
                str(int(value)) if float(value).is_integer() else str(round(float(value), 2))
                for value in sorted(values)
            ]
            total_area_by_carpet_area_unit[unit] = {}
            for row in unit_df.dropna(subset=["total_area"]).itertuples():
                carpet_value = float(row.carpet_area)
                key = str(int(carpet_value)) if carpet_value.is_integer() else str(round(carpet_value, 2))
                if key not in total_area_by_carpet_area_unit[unit]:
                    total_area_by_carpet_area_unit[unit][key] = round(float(row.total_area), 2)
        seen_area_options: set[tuple[str, str]] = set()
        for row in carpet_df.dropna(subset=["carpet_area"]).itertuples():
            carpet_value = float(row.carpet_area)
            value = str(int(carpet_value)) if carpet_value.is_integer() else str(round(carpet_value, 2))
            unit = clean_text(row.carpet_area_unit) or "sqft"
            key = (value, unit)
            if key in seen_area_options:
                continue
            seen_area_options.add(key)
            carpet_area_options.append(
                {
                    "value": value,
                    "unit": unit,
                    "label": f"{value} {unit}",
                    "total_area": None if pd.isna(row.total_area) else round(float(row.total_area), 2),
                }
            )

        return {
            "bedrooms": sorted(
                {int(float(value)) for value in bedrooms_df["bedrooms"].dropna() if float(value) > 0}
            ),
            "floor": sorted(
                {clean_text(value) for value in floor_df["floor"].dropna().map(clean_text) if clean_text(value)}
            ),
            "balcony": sorted(
                {int(float(value)) for value in balcony_df["balcony"].dropna() if float(value) > 0}
            ),
            "facing": [value for value in FACING_ORDER if value in facing_values],
            "parking": sorted(parking_values, key=parking_sort_key),
            "property_type": [label for label in PROPERTY_TYPE_UI_ORDER if label in property_type_values],
            "garden_park": amenity_options["garden_park"],
            "main_road": amenity_options["main_road"],
            "pool": amenity_options["pool"],
            "carpet_area_options": sorted(carpet_area_options, key=lambda item: (to_number(item["value"]), item["unit"])),
            "carpet_area_values_by_unit": area_values_by_unit,
            "total_area_by_carpet_area_unit": total_area_by_carpet_area_unit,
        }

    def inventory(self) -> dict[str, int]:
        total_properties = len(self.df)
        bhk_counts = self.df['bedrooms'].value_counts()
        total_1bhk = int(bhk_counts.get(1, 0))
        total_2bhk = int(bhk_counts.get(2, 0))
        total_3bhk = int(bhk_counts.get(3, 0))
        total_4bhk_plus = int(bhk_counts[bhk_counts.index >= 4].sum())
        total_cities = self.df['city'].nunique()
        return {
            "total_properties": total_properties,
            "total_1bhk": total_1bhk,
            "total_2bhk": total_2bhk,
            "total_3bhk": total_3bhk,
            "total_4bhk_plus": total_4bhk_plus,
            "total_cities": total_cities,
        }

    def nearby_places(
        self,
        location_label: str,
        api_key: str,
        radius_m: int = 2500,
        limit_per_type: int = 5,
    ) -> dict[str, Any]:
        location_label = clean_text(location_label)
        api_key = clean_text(api_key)
        if not location_label:
            raise ValueError("locationLabel is required.")
        if not api_key:
            return {"nearby": [], "message": "Google Maps API key not provided."}

        try:
            geocode_params = urllib.parse.urlencode({"address": location_label, "key": api_key})
            geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?{geocode_params}"
            with urllib.request.urlopen(geocode_url, timeout=10) as response:
                geocode_data = json.loads(response.read().decode("utf-8"))

            if geocode_data.get("status") != "OK" or not geocode_data.get("results"):
                return {
                    "nearby": [],
                    "message": "Nearby facilities unavailable. Enable Google Maps, Places, and Geocoding APIs.",
                }

            geometry = geocode_data["results"][0]["geometry"]["location"]
            lat_lng = f"{geometry['lat']},{geometry['lng']}"
            place_types = {
                "hospital": "Hospital",
                "school": "School",
                "subway_station": "Metro Station",
                "shopping_mall": "Mall",
            }

            nearby: list[dict[str, Any]] = []
            for google_type, label in place_types.items():
                params = urllib.parse.urlencode(
                    {
                        "location": lat_lng,
                        "radius": max(100, min(int(radius_m), 50000)),
                        "type": google_type,
                        "key": api_key,
                    }
                )
                places_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?{params}"
                with urllib.request.urlopen(places_url, timeout=10) as response:
                    places_data = json.loads(response.read().decode("utf-8"))

                status = places_data.get("status")
                if status not in {"OK", "ZERO_RESULTS"}:
                    return {
                        "nearby": [],
                        "message": "Nearby facilities unavailable. Enable Google Maps, Places, and Geocoding APIs.",
                    }

                for place in places_data.get("results", [])[: max(1, int(limit_per_type))]:
                    place_location = place.get("geometry", {}).get("location", {})
                    distance = self._distance_m(
                        float(geometry["lat"]),
                        float(geometry["lng"]),
                        float(place_location.get("lat", geometry["lat"])),
                        float(place_location.get("lng", geometry["lng"])),
                    )
                    nearby.append(
                        {
                            "name": clean_text(place.get("name")),
                            "type": label,
                            "distance": int(round(distance)),
                            "address": clean_text(place.get("vicinity")),
                        }
                    )

            nearby.sort(key=lambda item: item["distance"])
            return {"nearby": nearby}
        except Exception as exc:
            return {"nearby": [], "message": f"Nearby lookup unavailable: {exc}"}

    @staticmethod
    def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        radius = 6371000.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = (
            math.sin(delta_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        )
        return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def demand(self) -> list[dict[str, Any]]:
        location_counts = self.df.groupby('location').size().sort_values(ascending=False).head(5)
        total = len(self.df)
        return [
            {
                "location": loc,
                "percentage": round((count / total) * 100, 1)
            }
            for loc, count in location_counts.items()
        ]

    def search_properties(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        q = clean_text(query).lower()
        mask = (
            self.df['property_name'].str.lower().str.contains(q, na=False) |
            self.df['location'].str.lower().str.contains(q, na=False) |
            self.df['city'].str.lower().str.contains(q, na=False)
        )
        filtered = self.df[mask].head(limit)
        return [
            {
                "property_name": clean_text(row.property_name),
                "price": round(float(row.price), 2),
                "rate_per_sqft": None if pd.isna(row.rate_per_sqft) else round(float(row.rate_per_sqft), 2),
                "bedrooms": None if pd.isna(row.bedrooms) else int(float(row.bedrooms)),
                "total_area": None if pd.isna(row.total_area) else round(float(row.total_area), 2),
                "city": clean_text(row.city),
                "location": clean_text(row.location),
            }
            for row in filtered.itertuples()
        ]

    def search_suggestions(self, query: str = "", limit: int = 8) -> list[dict[str, Any]]:
        """Return autocomplete suggestions from property names, locations, and cities."""
        q = clean_text(query).lower()
        if not q:
            return []

        results = []
        seen = set()

        # Search in property names
        prop_mask = self.df['property_name'].str.lower().str.contains(q, na=False)
        for row in self.df[prop_mask].head(limit).itertuples():
            key = (clean_text(row.property_name), clean_text(row.city))
            if key not in seen:
                seen.add(key)
                results.append({
                    "name": clean_text(row.property_name),
                    "type": "property",
                    "city": clean_text(row.city),
                    "location": clean_text(row.location),
                })

        # Search in locations
        loc_mask = self.df['location'].str.lower().str.contains(q, na=False)
        for row in self.df[loc_mask].drop_duplicates('location').head(limit).itertuples():
            key = (clean_text(row.location), clean_text(row.city))
            if key not in seen:
                seen.add(key)
                results.append({
                    "name": clean_text(row.location),
                    "type": "location",
                    "city": clean_text(row.city),
                    "location": clean_text(row.location),
                })

        # Search in cities
        city_mask = self.df['city'].str.lower().str.contains(q, na=False)
        for row in self.df[city_mask].drop_duplicates('city').head(limit).itertuples():
            key = (clean_text(row.city), clean_text(row.city))
            if key not in seen:
                seen.add(key)
                results.append({
                    "name": clean_text(row.city),
                    "type": "city",
                    "city": clean_text(row.city),
                    "location": "",
                })

        return results[:limit]
