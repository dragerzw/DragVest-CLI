# app/service/portfolio_service.py
from typing import Dict, List, Optional, Any
import db

from app.service.exceptions import NotFoundError, ValidationError
from app.domain.portfolio import Portfolio
from app.domain.investment import Investment

class PortfolioService:
    """
    Service to manage portfolios stored in the top-level `db` module.
    Portfolios are Portfolio objects with holdings as list[Investment].
    """

    def __init__(self) -> None:
        self.db = db

    def create_portfolio(self, username: str, name: str, description: str) -> Portfolio:
        if username not in getattr(self.db, "users", {}):
            raise NotFoundError(f"user '{username}' not found")
        pid = getattr(self.db, "next_portfolio_id_get", lambda: 1)()
        portfolio = Portfolio(id=pid, name=name, description=description, holdings=[])
        self.db.portfolios.setdefault(username, []).append(portfolio)
        return portfolio

    def list_portfolios(self, username: str) -> List[Portfolio]:
        return list(self.db.portfolios.get(username, []))

    def get_portfolio(self, username: str, portfolio_id: int) -> Optional[Portfolio]:
        for p in self.db.portfolios.get(username, []):
            if p.id == portfolio_id:
                return p
        return None

    def delete_portfolio(self, username: str, portfolio_id: int) -> None:
        user_ports = self.db.portfolios.get(username, [])
        for idx, p in enumerate(user_ports):
            if p.id == portfolio_id:
                if p.holdings:
                    raise ValidationError("Portfolio holdings must be empty before deletion.")
                user_ports.pop(idx)
                return
        raise NotFoundError(f"portfolio id {portfolio_id} not found for user {username}")

    def add_investment(self, username: str, portfolio_id: int, ticker: str, quantity: int, purchase_price: float) -> Investment:
        if quantity <= 0:
            raise ValidationError("quantity must be positive")
        portfolio = self.get_portfolio(username, portfolio_id)
        if portfolio is None:
            raise NotFoundError("portfolio not found")
        # check if security exists
        if ticker not in self.db.securities:
            raise NotFoundError(f"ticker '{ticker}' not found")
        security = self.db.securities[ticker]
        cost = security.price * quantity
        user = self.db.users.get(username)
        if user is None or user.balance < cost:
            raise ValidationError("insufficient balance")
        # deduct balance
        user.balance -= cost
        # find existing holding
        for h in portfolio.holdings:
            if h.ticker == ticker:
                h.quantity += quantity
                # update purchase_price to average or keep as is; for simplicity, keep provided
                h.purchase_price = purchase_price
                return h
        holding = Investment(ticker=ticker, quantity=quantity, purchase_price=purchase_price)
        portfolio.holdings.append(holding)
        return holding

    def harvest_investment(self, username: str, portfolio_id: int, ticker: str, quantity: int, sale_price: float) -> float:
        if quantity <= 0:
            raise ValidationError("quantity must be positive")
        portfolio = self.get_portfolio(username, portfolio_id)
        if portfolio is None:
            raise NotFoundError("portfolio not found")
        for idx, h in enumerate(portfolio.holdings):
            if h.ticker == ticker:
                held_qty = h.quantity
                if quantity > held_qty:
                    raise ValidationError("requested quantity exceeds holdings")
                proceeds = quantity * sale_price
                # update user balance
                user = self.db.users.get(username)
                if user is None:
                    raise NotFoundError("user not found")
                user.balance += proceeds
                # update holdings
                if quantity == held_qty:
                    portfolio.holdings.pop(idx)
                else:
                    h.quantity = held_qty - quantity
                return proceeds
        raise NotFoundError("investment ticker not found in portfolio")

    def get_portfolios_by_username(self, username: str) -> List[Portfolio]:
        """
        Retrieve all portfolios for a given username.
        Raises NotFoundError if the user does not exist.
        """
        if username not in self.db.users:
            raise NotFoundError(f"User '{username}' not found.")
        return self.db.portfolios.get(username, [])
