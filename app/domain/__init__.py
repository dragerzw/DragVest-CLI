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

try:
    from .user import User  # type: ignore
except Exception:
    User = None  # type: ignore

try:
    from .security import Security  # type: ignore
except Exception:
    Security = None  # type: ignore

try:
    from .investment import Investment  # type: ignore
except Exception:
    Investment = None  # type: ignore

try:
    from .portfolio import Portfolio  # type: ignore
except Exception:
    Portfolio = None  # type: ignore

__all__ = [
    "LoginService",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "User",
    "Security",
    "Investment",
    "Portfolio",
]