# app/domain/security.py
from dataclasses import dataclass
from typing import Any
from decimal import Decimal


@dataclass
class Security:
    """
    Domain model representing a security available in the marketplace.
    Attributes:
    - ticker: str
    - issuer: str
    - price: float
    """
    ticker: str
    issuer: str
    price: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {"ticker": self.ticker, "issuer": self.issuer, "price": str(self.price)}
