# app/service/exceptions.py
class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass

class AuthorizationError(Exception):
    """Raised when a user is not authorized to perform an action."""
    pass

class NotFoundError(Exception):
    """Raised when a requested resource cannot be found."""
    pass

class ValidationError(Exception):
    """Raised when input validation fails."""
    pass

__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
]
