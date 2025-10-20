# app/domain/user.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class User:
    """
    Domain model representing an application user.
    Attributes required by the assignment:
    - first_name (str)
    - last_name  (str)
    - username   (str)
    - password   (str)
    - balance    (float)
    """
    first_name: str
    last_name: str
    username: str
    password: str
    balance: float = 0.0
    role: str = "customer"  # Default role is 'customer'

    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def adjust_balance(self, amount: float) -> None:
        """Adjust balance by amount (positive or negative)."""
        self.balance += amount

    def is_admin(self) -> bool:
        return self.role == "admin"

    def to_dict(self) -> dict[str, Any]:
        """Return a simple serializable representation."""
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
            "password": self.password,
            "balance": self.balance,
            "role": self.role,
        }
