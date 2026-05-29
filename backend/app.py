from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from flask import Flask, jsonify
from flask_cors import CORS

from backend.routes.auth import auth_bp
from backend.routes.frontend import create_frontend_routes
from backend.routes.insights import create_insight_routes
from backend.routes.maps import create_map_routes
from backend.routes.prediction import create_prediction_routes
from backend.routes.properties import create_property_routes
from backend.services.prediction_service import PredictionService


def create_app() -> Flask:
    project_root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(project_root / "templates"),
        static_folder=str(project_root / "static"),
        static_url_path="/static",
    )
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    CORS(app)

    service = PredictionService()

    app.register_blueprint(create_frontend_routes(project_root))
    app.register_blueprint(auth_bp)
    app.register_blueprint(create_prediction_routes(service))
    app.register_blueprint(create_property_routes(service))
    app.register_blueprint(create_insight_routes(service))
    app.register_blueprint(create_map_routes(service))

    @app.after_request
    def disable_cache(response: Any) -> Any:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    @app.errorhandler(404)
    def not_found(_: Exception) -> tuple[Any, int]:
        return jsonify({"error": "Route not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(_: Exception) -> tuple[Any, int]:
        return jsonify({"error": "Method not allowed."}), 405

    return app


app = create_app()


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host=host, port=port, debug=debug)
