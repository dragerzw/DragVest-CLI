import pytest

from app.service.login_service import LoginService
from app.service.user_service import UserService
from app.service.exceptions import NotFoundError


def test_authenticate_success_and_failure(db_session):
    us = UserService()
    ls = LoginService()

    # create user and verify authenticate succeeds for correct password
    us.create_user("LFirst", "LLast", "login_user", "s3cret", 10.0)
    assert ls.authenticate("login_user", "s3cret") is True

    # wrong password returns False
    assert ls.authenticate("login_user", "wrong") is False

    # non-existent user returns False
    assert ls.authenticate("no_such_user", "x") is False


def test_logout_is_noop():
    ls = LoginService()
    # logout should be a no-op and not raise
    ls.logout()
