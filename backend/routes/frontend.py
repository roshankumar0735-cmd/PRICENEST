"""Frontend document and static compatibility routes."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from flask import Blueprint, redirect, render_template, url_for


def create_frontend_routes(project_root: Path) -> Blueprint:
    blueprint = Blueprint("frontend", __name__)

    def asset_version() -> str:
        static_files = list((project_root / "static").glob("**/*"))
        mtimes = [path.stat().st_mtime for path in static_files if path.is_file()]
        return str(int(max(mtimes) if mtimes else time.time()))

    @blueprint.get("/")
    def index() -> Any:
        return render_template("index.html", asset_version=asset_version())

    @blueprint.get("/app.js")
    @blueprint.get("/app_v2.js")
    def frontend_app_js() -> Any:
        return redirect(url_for("static", filename="js/app.js"))

    @blueprint.get("/styles.css")
    @blueprint.get("/styles_v2.css")
    def frontend_styles_css() -> Any:
        return redirect(url_for("static", filename="css/styles.css"))

    @blueprint.get("/firebase.js")
    def frontend_firebase_js() -> Any:
        return redirect(url_for("static", filename="js/firebase.js"))

    return blueprint
