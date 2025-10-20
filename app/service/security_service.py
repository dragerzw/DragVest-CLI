# app/service/security_service.py
from typing import List
import db

from app.domain.security import Security
from app.domain.portfolio import Portfolio
from app.service.exceptions import NotFoundError

class SecurityService:
    """
    Simple service to expose securities stored in the top-level `db` module.
    Assumes `db.securities` is a dict mapping ticker -> Security.
    """
    def __init__(self) -> None:
        self.db = db

    def list_securities(self) -> List[Security]:
        """Return all securities available in the marketplace."""
        sec_map = getattr(self.db, "securities", {})
        # ensure we return a list of Security objects (or empty list)
        return list(sec_map.values()) if isinstance(sec_map, dict) else []

    def get_security(self, ticker: str) -> Security:
        """Return a Security by ticker or raise NotFoundError."""
        sec_map = getattr(self.db, "securities", {})
        if not isinstance(sec_map, dict):
            raise NotFoundError(f"ticker '{ticker}' not found")
        sec = sec_map.get(ticker)
        if sec is None:
            raise NotFoundError(f"ticker '{ticker}' not found")
        return sec

    def buy_security(self, username: str, ticker: str, amount: float, portfolio_id: int) -> None:
        """
        Allow a user to buy a security in a specific portfolio.
        Supports fractional investing.
        """
        if username not in self.db.users:
            raise NotFoundError(f"User '{username}' not found.")

        user = self.db.users[username]
        if user.role != "customer":
            raise PermissionError("Only customers can buy securities.")

        portfolios = self.db.portfolios.get(username, [])
        portfolio = next((p for p in portfolios if p.id == portfolio_id), None)
        if portfolio is None:
            raise NotFoundError(f"Portfolio with ID '{portfolio_id}' not found for user '{username}'.")

        security = self.db.securities.get(ticker)
        if security is None:
            raise NotFoundError(f"Security '{ticker}' not found in the marketplace.")

        if amount > user.balance:
            raise ValueError("Insufficient balance to buy security.")

        # Calculate fractional shares
        quantity = amount / security.price
        if quantity <= 0:
            raise ValueError("Investment amount is too low to buy any shares.")

        user.adjust_balance(-amount)
        portfolio.add_or_update_investment(ticker, quantity, security.price)

    def sell_security(self, username: str, ticker: str, amount: float, portfolio_id: int) -> None:
        """
        Allow a user to sell a security from a specific portfolio.
        Only users with the 'customer' role can perform this action.
        """
        if username not in self.db.users:
            raise NotFoundError(f"User '{username}' not found.")

        user = self.db.users[username]
        if user.role != "customer":
            raise PermissionError("Only customers can sell securities.")

        portfolios = self.db.portfolios.get(username, [])
        portfolio = next((p for p in portfolios if p.id == portfolio_id), None)
        if portfolio is None:
            raise NotFoundError(f"Portfolio with ID '{portfolio_id}' not found for user '{username}'.")

        investment = next((inv for inv in portfolio.holdings if inv.ticker == ticker), None)
        if investment is None:
            raise NotFoundError(f"Security '{ticker}' not found in portfolio '{portfolio.name}'.")

        security = self.db.securities.get(ticker)
        if security is None:
            raise NotFoundError(f"Security '{ticker}' not found in the marketplace.")

        total_value = investment.quantity * security.price
        if amount > total_value:
            raise ValueError("Amount exceeds the total value of the investment.")

        quantity_to_sell = amount // security.price
        if quantity_to_sell == 0:
            raise ValueError("Amount is too low to sell any shares.")

        investment.quantity -= quantity_to_sell
        if investment.quantity == 0:
            portfolio.holdings.remove(investment)

        user.adjust_balance(amount)
