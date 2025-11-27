# app/service/portfolio_service.py
from typing import List, Optional
from decimal import Decimal

from sqlalchemy.orm import selectinload

from app.db import get_session
from app.models import Portfolio as ORMPortfolio, Investment as ORMInvestment, Security as ORMSecurity, User as ORMUser, Transaction
from app.service.exceptions import NotFoundError, ValidationError


class PortfolioService:
    """PortfolioService implemented using SQLAlchemy ORM models and sessions.

    Methods operate with short-lived sessions and commit changes where necessary.
    """

    def __init__(self) -> None:
        pass

    def create_portfolio(self, username: str, name: str, description: str) -> ORMPortfolio:
        session = get_session()
        try:
            user = session.query(ORMUser).filter_by(username=username).one_or_none()
            if not user:
                raise NotFoundError(f"user '{username}' not found")
            portfolio = ORMPortfolio(name=name, description=description, owner_username=username)
            session.add(portfolio)
            session.commit()
            session.refresh(portfolio)
            return portfolio
        finally:
            session.close()

    def list_portfolios(self, username: str) -> List[ORMPortfolio]:
        session = get_session()
        try:
            ports = (
                session.query(ORMPortfolio)
                .options(selectinload(ORMPortfolio.investments))
                .filter_by(owner_username=username)
                .all()
            )
            return ports
        finally:
            session.close()

    def get_portfolio(self, username: str, portfolio_id: int) -> Optional[ORMPortfolio]:
        session = get_session()
        try:
            p = (
                session.query(ORMPortfolio)
                .options(selectinload(ORMPortfolio.investments))
                .filter_by(id=portfolio_id, owner_username=username)
                .one_or_none()
            )
            return p
        finally:
            session.close()

    def delete_portfolio(self, username: str, portfolio_id: int) -> None:
        session = get_session()
        try:
            p = session.query(ORMPortfolio).options(selectinload(ORMPortfolio.investments)).filter_by(id=portfolio_id, owner_username=username).one_or_none()
            if not p:
                raise NotFoundError(f"portfolio id {portfolio_id} not found for user {username}")
            if p.investments:
                raise ValidationError("Portfolio holdings must be empty before deletion.")
            session.delete(p)
            session.commit()
        finally:
            session.close()

    def add_investment(self, username: str, portfolio_id: int, ticker: str, quantity: int, purchase_price: float) -> ORMInvestment:
        if quantity <= 0:
            raise ValidationError("quantity must be positive")
        session = get_session()
        try:
            portfolio = session.query(ORMPortfolio).filter_by(id=portfolio_id, owner_username=username).one_or_none()
            if portfolio is None:
                raise NotFoundError("portfolio not found")
            security = session.query(ORMSecurity).filter_by(ticker=ticker).one_or_none()
            if security is None:
                raise NotFoundError(f"ticker '{ticker}' not found")
            user = session.query(ORMUser).filter_by(username=username).one_or_none()
            if user is None:
                raise NotFoundError("user not found")

            # ensure using Decimal for monetary math
            pp = Decimal(str(purchase_price))
            cost = security.price * Decimal(quantity)
            # normalize user.balance to Decimal if it's a float stored in DB
            if not isinstance(user.balance, Decimal):
                user.balance = Decimal(str(user.balance))
            if user.balance < cost:
                raise ValidationError("insufficient balance")

            # deduct balance using explicit Decimal arithmetic to avoid mixed-type in-place ops
            ubal = Decimal(str(user.balance)) if not isinstance(user.balance, Decimal) else user.balance
            ubal = ubal - cost
            user.balance = ubal

            # check existing holding
            inv = (
                session.query(ORMInvestment)
                .filter_by(portfolio_id=portfolio.id, ticker=ticker)
                .one_or_none()
            )
            if inv:
                inv.quantity += quantity
                inv.purchase_price = pp
            else:
                inv = ORMInvestment(ticker=ticker, quantity=quantity, purchase_price=pp, portfolio_id=portfolio.id)
                session.add(inv)

            session.commit()
            session.refresh(inv)
            return inv
        finally:
            session.close()

    def harvest_investment(self, username: str, portfolio_id: int, ticker: str, quantity: int, sale_price: float) -> Decimal:
        if quantity <= 0:
            raise ValidationError("quantity must be positive")
        session = get_session()
        try:
            portfolio = session.query(ORMPortfolio).filter_by(id=portfolio_id, owner_username=username).one_or_none()
            if portfolio is None:
                raise NotFoundError("portfolio not found")
            inv = (
                session.query(ORMInvestment)
                .filter_by(portfolio_id=portfolio.id, ticker=ticker)
                .one_or_none()
            )
            if not inv:
                raise NotFoundError("investment ticker not found in portfolio")
            if quantity > inv.quantity:
                raise ValidationError("requested quantity exceeds holdings")

            sp = Decimal(str(sale_price))
            proceeds = Decimal(quantity) * sp

            user = session.query(ORMUser).filter_by(username=username).one_or_none()
            if user is None:
                raise NotFoundError("user not found")
            # normalize balance to Decimal if necessary, then add proceeds using assignment
            ubal = Decimal(str(user.balance)) if not isinstance(user.balance, Decimal) else user.balance
            ubal = ubal + proceeds
            user.balance = ubal

            # log transaction
            tx = Transaction(
                user_id=user.id,
                portfolio_id=portfolio.id,
                security_id=ticker,
                action="SELL",
                quantity=quantity,
                price=sp,
            )
            session.add(tx)

            if quantity == inv.quantity:
                session.delete(inv)
            else:
                inv.quantity = inv.quantity - quantity

            session.commit()
            return proceeds
        finally:
            session.close()

    def get_portfolios_by_username(self, username: str) -> List[ORMPortfolio]:
        session = get_session()
        try:
            user = session.query(ORMUser).filter_by(username=username).one_or_none()
            if not user:
                raise NotFoundError(f"User '{username}' not found.")
            ports = session.query(ORMPortfolio).options(selectinload(ORMPortfolio.investments)).filter_by(owner_username=username).all()
            return ports
        finally:
            session.close()
