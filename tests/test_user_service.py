import pytest
from decimal import Decimal
from uuid import uuid4

from app.service.user_service import UserService
from app.service.exceptions import NotFoundError, ValidationError


def test_user_service_errors(db_session):
    us = UserService()
    # use a unique username to avoid cross-test collisions
    uname = f"dupuser_{uuid4().hex[:8]}"
    us.create_user("First", "User", uname, "pw", 100.00)

    # duplicate username should raise
    with pytest.raises(ValidationError):
        us.create_user("First", "User", uname, "pw", 100.00)

    # deposit negative
    with pytest.raises(ValueError):
        us.deposit("dupuser", -50.0)

    # deposit to non-existent user
    with pytest.raises(NotFoundError):
        us.deposit("noone", 10.0)

    # delete non-existent
    with pytest.raises(NotFoundError):
        us.delete_user("noone")


def test_get_user_not_found_raises(db_session):
    us = UserService()
    with pytest.raises(NotFoundError):
        us.get_user("this_user_does_not_exist")


def test_list_users_and_delete_user_success(db_session):
    us = UserService()
    # create a user then delete (no portfolios)
    user = us.create_user("Del", "Me", "delme", "pw", 20.00)
    users = us.list_users()
    assert any(u.username == "delme" for u in users)

    # delete should succeed because no portfolios
    us.delete_user("delme")
    with pytest.raises(NotFoundError):
        us.get_user("delme")


def test_deposit_normalization(db_session):
    us = UserService()
    # create user then manually set balance to float to simulate mixed types
    user = us.create_user("Norm", "User", "norm", "pw", 10.00)
    # set stored balance to a float (simulate a legacy float) and commit
    s = db_session
    u = s.query(type(user)).filter_by(username="norm").one()
    u.balance = float(10.0)
    s.commit()

    # deposit should normalize and update correctly
    us.deposit("norm", 5.00)
    updated = us.get_user("norm")
    assert Decimal(str(updated.balance)) == Decimal("15.00")
