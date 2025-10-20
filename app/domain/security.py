# app/domain/security.py
from dataclasses import dataclass
from typing import Any

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
    price: float

    def to_dict(self) -> dict[str, Any]:
        return {"ticker": self.ticker, "issuer": self.issuer, "price": self.price}
