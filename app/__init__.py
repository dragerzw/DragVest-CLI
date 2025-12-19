from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from app.service.exceptions import (
    ValidationError,
    NotFoundError,
    AuthenticationError,
    AuthorizationError,
)

from app.config import Config
from app.database import sqldb


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Accept both with/without trailing slashes for all routes
    app.url_map.strict_slashes = False

    # Register extensions
    sqldb.init_app(app)

    # Ensure tables exist in development environments
    with app.app_context():
        try:
            from app import models as _models  # noqa: F401 - ensure models are registered without shadowing
            sqldb.create_all()
        except Exception:
            # If the database is unreachable or migrations are preferred, ignore here.
            # Routes will still raise meaningful errors via handlers below.
            pass

    # Error handlers return JSON (API-friendly)
    # --- JSON error helpers & handlers ---
    def json_error(code: str, message: str, details: dict | list | str | None = None, status: int = 400):
        payload = {"error": {"code": code, "message": message}}
        if details is not None:
            payload["error"]["details"] = details
        return payload, status

    @app.errorhandler(ValidationError)
    def handle_validation_error(err: ValidationError):
        return json_error("validation_error", str(err), getattr(err, "details", None), 400)

    @app.errorhandler(NotFoundError)
    def handle_not_found_error(err: NotFoundError):
        return json_error("not_found", str(err), getattr(err, "details", None), 404)

    @app.errorhandler(AuthenticationError)
    def handle_auth_error(err: AuthenticationError):
        return json_error("authentication_error", str(err), getattr(err, "details", None), 401)

    @app.errorhandler(AuthorizationError)
    def handle_authorization_error(err: AuthorizationError):
        return json_error("authorization_error", str(err), getattr(err, "details", None), 403)

    @app.errorhandler(HTTPException)
    def handle_http_exception(err: HTTPException):
        code = (err.name or "http_error").replace(" ", "_").lower()
        message = err.description or err.name or "HTTP error"
        return json_error(code, message, None, err.code or 500)

    @app.errorhandler(Exception)
    def handle_unexpected_exception(err: Exception):
        # In debug mode, Flask will still show its debugger. This provides a JSON fallback otherwise.
        return json_error("internal_error", "An unexpected error occurred", None, 500)

    # Register blueprints
    from app.routes.user_bp import user_bp
    from app.routes.portfolio_bp import portfolio_bp
    from app.routes.security_bp import security_bp

    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(portfolio_bp, url_prefix="/api/portfolios")
    app.register_blueprint(security_bp, url_prefix="/api/securities")

    @app.get("/")
    def index():
        return {
            "service": "DragVest-CLI API",
            "status": "running",
            "health": "/api/health",
            "endpoints": {
                "users": ["GET /api/users", "GET /api/users/{id}", "POST /api/users", "DELETE /api/users/{username}"],
                "portfolios": [
                    "GET /api/portfolios?owner={username}",
                    "GET /api/portfolios/{id}",
                    "POST /api/portfolios",
                    "DELETE /api/portfolios/{id}?owner={username}",
                    "POST /api/portfolios/{id}/buy",
                    "POST /api/portfolios/{id}/harvest"
                ],
                "securities": ["GET /api/securities", "GET /api/securities/{ticker}"]
            }
        }, 200

    @app.get("/api/health")
    def health():
        return {"status": "ok"}, 200

    return app
# app package init
