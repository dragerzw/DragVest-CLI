# app/service/login_service.py
from typing import Optional
from app.database import sqldb as db
from app.models.user import User

class LoginService:
    """
    Login service using SQLAlchemy ORM and MySQL.
    """
    def __init__(self) -> None:
        pass

    def authenticate(self, username: str, password: str) -> bool:
        session = db.session
        user = session.query(User).filter_by(username=username).one_or_none()
        if user is None:
            return False
        # Compare password (plain text for now)
        return str(user.password) == str(password)

    def logout(self) -> None:
        # No in-memory state to clear
        pass
