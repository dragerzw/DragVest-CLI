# db.py
from typing import Optional, Dict, List, Any
from app.domain.user import User
from app.domain.security import Security
from app.domain.portfolio import Portfolio
from app.domain.investment import Investment

# In-memory "database" state
logged_in_user: Optional[User] = None
users: Dict[str, User] = {}
securities: Dict[str, Security] = {}
portfolios: Dict[str, List[Portfolio]] = {}
next_portfolio_id: int = 1

# Seed a default admin user so the app has at least one account.
# Username: admin, Password: admin123
_admin = User(first_name="Admin", last_name="User", username="admin", password="admin123", balance=0.0)
users[_admin.username] = _admin

# Seed example securities (3 minimum)
securities["AAPL"] = Security(ticker="AAPL", issuer="Apple Inc.", price=150.0)
securities["MSFT"] = Security(ticker="MSFT", issuer="Microsoft Corp.", price=300.0)
securities["GOOG"] = Security(ticker="GOOG", issuer="Alphabet Inc.", price=2800.0)

# Helper functions used by services/CLI
def list_users() -> List[User]:
    """Return all users as a list."""
    return list(users.values())

def get_user(username: str) -> Optional[User]:
    """Return a user by username or None if not found."""
    return users.get(username)

def add_user(user: User) -> None:
    """
    Add a new user to the in-memory store.
    Raises ValueError if username already exists.
    """
    if user.username in users:
        raise ValueError(f"username '{user.username}' already exists")
    if user.role == "admin" and not any(u.is_admin() for u in users.values() if u.username != user.username):
        raise ValueError("Cannot remove the last admin user.")

    users[user.username] = user

def remove_user(username: str) -> None:
    """
    Remove a user if they exist and have no portfolios.
    Raises ValueError if user not found or if portfolios exist.
    """
    if username not in users:
        raise ValueError(f"user '{username}' does not exist")
    user_ports = portfolios.get(username, [])
    if user_ports:
        raise ValueError("user has portfolios; remove them before deleting the user")
    # safe to remove
    del users[username]

def next_portfolio_id_get() -> int:
    """Return the next portfolio id and increment the counter."""
    global next_portfolio_id
    pid = next_portfolio_id
    next_portfolio_id += 1
    return pid

def seed_initial_data() -> None:
    """
    Idempotently ensure required initial data exists (admin user and sample securities).
    Safe to call multiple times.
    """
    global users, securities, portfolios, next_portfolio_id

    # Ensure admin user exists
    if "admin" not in users:
        try:
            admin = User(first_name="Admin", last_name="User", username="admin", password="admin123", balance=0.0)
            users[admin.username] = admin
        except Exception:
            # don't crash during seeding
            pass

    # Ensure example securities exist (do not overwrite existing entries)
    default_securities = {
        "AAPL": Security(ticker="AAPL", issuer="Apple Inc.", price=150.0),
        "MSFT": Security(ticker="MSFT", issuer="Microsoft Corp.", price=300.0),
        "GOOG": Security(ticker="GOOG", issuer="Alphabet Inc.", price=2800.0),
    }
    for ticker, sec in default_securities.items():
        securities.setdefault(ticker, sec)

# Exported symbols
__all__ = [
    "logged_in_user",
    "users",
    "securities",
    "portfolios",
    "next_portfolio_id",
    "list_users",
    "get_user",
    "add_user",
    "remove_user",
    "next_portfolio_id_get",
    "seed_initial_data",
]
