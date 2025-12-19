"""Model package initializer — import models so SQLAlchemy can register mappers.

This module centralizes model imports to avoid circular import problems at runtime.
"""
from app.database import sqldb as db

from .user import User
from .portfolio import Portfolio
from .investment import Investment
from .security import Security
from .transaction import Transaction

__all__ = ["db", "User", "Portfolio", "Investment", "Security", "Transaction"]
