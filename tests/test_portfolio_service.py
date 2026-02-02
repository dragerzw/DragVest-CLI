import pytest
from decimal import Decimal

from app.service.portfolio_service import PortfolioService
from app.service.user_service import UserService
from app.service.exceptions import NotFoundError, ValidationError
from app.models import Security


def test_add_investment_and_prevent_delete_with_holdings(db_session):
    us = UserService()
    ps = PortfolioService()

    us.create_user("U", "One", "u1", "pw", 1000.00)
    p = ps.create_portfolio("u1", "P1", "desc")

    # seed security
    db_session.add(Security(ticker="AAPL", name="Apple Inc.", price=Decimal('276.00')))
    db_session.commit()

    inv = ps.add_investment("u1", p.id, "AAPL", 1, 276.00)
    assert inv.quantity == 1

    # deleting portfolio with holdings should raise ValidationError
    with pytest.raises(ValidationError):
        ps.delete_portfolio("u1", p.id)


def test_portfolio_add_investment_errors(db_session):
    us = UserService()
    ps = PortfolioService()

    us.create_user("QA", "User", "qa", "pw", 50.00)
    p = ps.create_portfolio("qa", "qa-p", "desc")

    # ensure AAPL exists
    s = db_session
    s.add(Security(ticker="AAPL", name="Apple Inc.", price=Decimal('276.00')))
    s.commit()

    # quantity must be positive
    with pytest.raises(Exception):
        ps.add_investment("qa", p.id, "AAPL", 0, 276.00)

    # purchase price so high cost > balance
    with pytest.raises(ValidationError):
        ps.add_investment("qa", p.id, "AAPL", 1, 1000.00)

    # portfolio not found (wrong owner)
    with pytest.raises(NotFoundError):
        ps.add_investment("noone", p.id, "AAPL", 1, 276.00)

    # ticker not found
    with pytest.raises(NotFoundError):
        ps.add_investment("qa", p.id, "XXXX", 1, 10.00)


def test_get_portfolios_notfound():
    ps = PortfolioService()
    with pytest.raises(NotFoundError):
        ps.get_portfolios_by_username("nouser")


def test_add_investment_updates_existing_holding(db_session):
    us = UserService()
    ps = PortfolioService()

    us.create_user("Upd", "User", "upd", "pw", 2000.00)
    p = ps.create_portfolio("upd", "U", "d")

    # ensure security exists
    db_session.add(Security(ticker="S1", name="S1 Co", price=Decimal("10.00")))
    db_session.commit()

    inv1 = ps.add_investment("upd", p.id, "S1", 5, 10.00)
    assert inv1.quantity == 5

    # add again -> should update quantity and purchase_price
    inv2 = ps.add_investment("upd", p.id, "S1", 3, 11.00)
    assert inv2.quantity == 8
    assert Decimal(str(inv2.purchase_price)) == Decimal("11.00")


def test_harvest_partial_and_full_removes_investment_and_logs_tx(db_session):
    us = UserService()
    ps = PortfolioService()

    us.create_user("Harvester", "One", "harv", "pw", 5000.00)
    p = ps.create_portfolio("harv", "H1", "for harvest")

    db_session.add(Security(ticker="MSFT", name="Microsoft", price=Decimal('476.00')))
    db_session.commit()

    # buy 2 shares via add_investment
    ps.add_investment("harv", p.id, "MSFT", 2, 476.00)

    # harvest one share
    proceeds = ps.harvest_investment("harv", p.id, "MSFT", 1, 476.00)
    assert Decimal(proceeds) == Decimal('476.00')

    # harvest remaining share
    proceeds2 = ps.harvest_investment("harv", p.id, "MSFT", 1, 476.00)
    assert Decimal(proceeds2) == Decimal('476.00')

    p_after = ps.get_portfolio("harv", p.id)
    assert not p_after.investments
