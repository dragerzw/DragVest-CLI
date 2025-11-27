# app/service/user_service.py
from typing import List, Optional
from decimal import Decimal
from app.db import get_session
from app.models.user import User
from app.service.exceptions import ValidationError, NotFoundError, AuthorizationError

class UserService:
    def get_user(self, username: str) -> Optional[User]:
        session = get_session()
        user = session.query(User).filter_by(username=username).one_or_none()
        session.close()
        if not user:
            raise NotFoundError(f"User '{username}' does not exist.")
        return user

    def list_users(self) -> List[User]:
        session = get_session()
        users = session.query(User).all()
        session.close()
        return users

    def create_user(self, first_name: str, last_name: str, username: str, password: str, balance: float, role: str = "customer") -> User:
        session = get_session()
        if session.query(User).filter_by(username=username).first():
            session.close()
            raise ValidationError(f"Username '{username}' already exists.")
        # convert balance to Decimal
        bal = Decimal(str(balance))
        user = User(first_name=first_name, last_name=last_name, username=username, password=password, balance=bal, role=role)
        session.add(user)
        session.commit()
        session.close()
        return user

    def delete_user(self, username: str) -> None:
        session = get_session()
        user = session.query(User).filter_by(username=username).one_or_none()
        if not user:
            session.close()
            raise NotFoundError("User does not exist.")
        # Check portfolios (assuming relationship exists)
        if hasattr(user, 'portfolios') and user.portfolios:
            session.close()
            raise ValidationError("User has portfolios. Remove them before deleting the user.")
        session.delete(user)
        session.commit()
        session.close()

    def deposit(self, username: str, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit amount must be greater than zero.")
        session = get_session()
        user = session.query(User).filter_by(username=username).one_or_none()
        if not user:
            session.close()
            raise NotFoundError(f"User '{username}' does not exist.")
        amt = Decimal(str(amount))
        ubal = Decimal(str(user.balance)) if not isinstance(user.balance, Decimal) else user.balance
        ubal = ubal + amt
        user.balance = ubal
        session.commit()
        session.close()
