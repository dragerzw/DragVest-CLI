# app/domain/investment.py
from dataclasses import dataclass

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
    purchase_price: float

    def value(self) -> float:
        return self.quantity * self.purchase_price
