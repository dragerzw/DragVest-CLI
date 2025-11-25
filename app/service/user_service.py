# app/service/user_service.py
from typing import List
from db import list_users, get_user, add_user, remove_user, portfolios
from app.domain.user import User
from app.service.exceptions import ValidationError, NotFoundError, AuthorizationError

class UserService:
    def get_user(self, username: str) -> User:
        """Retrieve a user by username."""
        user = get_user(username)
        if not user:
            raise NotFoundError(f"User '{username}' does not exist.")
        return user
    def list_users(self) -> List[User]:
        return list_users()

    def create_user(self, first_name: str, last_name: str, username: str, password: str, balance: float, role: str = "customer") -> User:
        """
        Create and add a new user to the database.
        Ensures at least one admin user exists.
        Raises ValidationError if username is not unique or if trying to remove the last admin.
        """
        if role == "admin" and not any(user.is_admin() for user in list_users()):
            raise ValidationError("At least one admin must exist.")

        user = User(first_name, last_name, username, password, balance, role)
        add_user(user)
        return user

    def delete_user(self, username: str) -> None:
        user = get_user(username)
        if not user:
            raise NotFoundError("User does not exist.")
        # Check portfolios
        user_portfolios = portfolios.get(username, [])
        if user_portfolios:
            raise ValidationError("User has portfolios. Remove them before deleting the user.")
        remove_user(username)

    def deposit(self, username: str, amount: float) -> None:
        """
        Deposit money into the user's account.
        Raises ValueError if the amount is negative or the user does not exist.
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be greater than zero.")

        user = get_user(username)
        if not user:
            raise NotFoundError(f"User '{username}' does not exist.")

        user.adjust_balance(amount)
