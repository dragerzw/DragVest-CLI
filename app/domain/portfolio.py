# app/domain/portfolio.py
from dataclasses import dataclass
from typing import List, Optional
from app.domain.investment import Investment

@dataclass
class Portfolio:
    """
    Domain model representing a user portfolio.
    Attributes:
    - id: int
    - name: str
    - description: str
    - holdings: list[Investment]
    """
    id: int
    name: str
    description: str
    holdings: List[Investment]

    def find_investment(self, ticker: str) -> Optional[Investment]:
        for inv in self.holdings:
            if inv.ticker.upper() == ticker.upper():
                return inv
        return None

    def add_or_update_investment(self, ticker: str, quantity: int, purchase_price: 'Decimal') -> None:
        existing = self.find_investment(ticker)
        if existing:
            existing.quantity += quantity
            # We keep the purchase_price as-is; another strategy could be weighted average.
        else:
            # ensure purchase_price stored as Decimal in domain model
            from decimal import Decimal
            pp = Decimal(str(purchase_price)) if not isinstance(purchase_price, Decimal) else purchase_price
            self.holdings.append(Investment(ticker=ticker.upper(), quantity=quantity, purchase_price=pp))

    def remove_investment(self, ticker: str, quantity: int) -> bool:
        inv = self.find_investment(ticker)
        if not inv:
            return False
        if quantity > inv.quantity:
            raise ValueError("Quantity to remove exceeds holding.")
        if quantity == inv.quantity:
            self.holdings.remove(inv)
        else:
            inv.quantity -= quantity
        return True
