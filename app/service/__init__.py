# Package initializer for app.service

# Defensive re-exports so `from app.service import LoginService` works without failing import-time
try:
    from .login_service import LoginService  # type: ignore
except Exception:
    LoginService = None  # type: ignore

try:
    from .exceptions import (
        AuthenticationError,
        AuthorizationError,
        NotFoundError,
        ValidationError,
    )  # type: ignore
except Exception:
    AuthenticationError = AuthorizationError = NotFoundError = ValidationError = Exception  # type: ignore

__all__ = [
    "LoginService",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
]