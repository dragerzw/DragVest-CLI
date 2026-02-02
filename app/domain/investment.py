# app/domain/investment.py
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Investment:
    """
    Domain model representing an investment held in a portfolio.
    Attributes:
    - ticker: str
    - quantity: int
    - purchase_price: float
    """
    ticker: str
    quantity: int
    purchase_price: Decimal

    def value(self) -> Decimal:
        return Decimal(self.quantity) * self.purchase_price
