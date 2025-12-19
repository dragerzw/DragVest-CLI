# app/service/user_service.py
from typing import List, Optional
from decimal import Decimal
from app.database import sqldb as db
from app.models.user import User
from app.service.exceptions import ValidationError, NotFoundError, AuthorizationError

class UserService:
    def get_user(self, username: str) -> Optional[User]:
        session = db.session
        user = session.query(User).filter_by(username=username).one_or_none()
        if not user:
            raise NotFoundError(f"User '{username}' does not exist.")
        return user

    def list_users(self) -> List[User]:
        session = db.session
        users = session.query(User).all()
        return users

    def create_user(self, first_name: str, last_name: str, username: str, password: str, balance: float, role: str = "customer") -> User:
        session = db.session
        if session.query(User).filter_by(username=username).first():
            raise ValidationError(f"Username '{username}' already exists.")
        # convert balance to Decimal
        bal = Decimal(str(balance))
        user = User(first_name=first_name, last_name=last_name, username=username, password=password, balance=bal, role=role)
        session.add(user)
        session.commit()
        return user

    def delete_user(self, username: str) -> None:
        session = db.session
        user = session.query(User).filter_by(username=username).one_or_none()
        if not user:
            raise NotFoundError("User does not exist.")
        # Check portfolios (assuming relationship exists)
        if hasattr(user, 'portfolios') and user.portfolios:
            raise ValidationError("User has portfolios. Remove them before deleting the user.")
        session.delete(user)
        session.commit()

    def deposit(self, username: str, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit amount must be greater than zero.")
        session = db.session
        user = session.query(User).filter_by(username=username).one_or_none()
        if not user:
            raise NotFoundError(f"User '{username}' does not exist.")
        amt = Decimal(str(amount))
        ubal = Decimal(str(user.balance)) if not isinstance(user.balance, Decimal) else user.balance
        ubal = ubal + amt
        user.balance = ubal
        session.commit()
