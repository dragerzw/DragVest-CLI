import pytest
from decimal import Decimal

from app.service.security_service import SecurityService
from app.service.portfolio_service import PortfolioService
from app.service.user_service import UserService
from app.service.exceptions import NotFoundError
from app.models import Security


def test_buy_and_sell_security_updates_balance_and_transactions(db_session):
    us = UserService()
    ps = PortfolioService()
    ss = SecurityService()

    us.create_user("Buyer", "Two", "buyer2", "pw", 2000.00)
    port = ps.create_portfolio("buyer2", "Main", "Test")

    db_session.add(Security(ticker="MSFT", name="Microsoft Corporation", price=Decimal('476.00')))
    db_session.commit()

    # buy $952 of MSFT (price 476 -> 2 shares)
    ss.buy_security("buyer2", "MSFT", 952.00, port.id)
    p = ps.get_portfolio("buyer2", port.id)
    invs = [i for i in p.investments if i.ticker == "MSFT"]
    assert len(invs) == 1 and invs[0].quantity == 2

    # record balance after buy
    user = us.get_user("buyer2")
    bal_after_buy = Decimal(user.balance)

    # sell $476 (1 share) from the portfolio
    ss.sell_security("buyer2", "MSFT", 476.00, port.id)
    p2 = ps.get_portfolio("buyer2", port.id)
    invs2 = [i for i in p2.investments if i.ticker == "MSFT"]
    assert invs2[0].quantity == 1

    user_after_sell = us.get_user("buyer2")
    assert Decimal(user_after_sell.balance) > bal_after_buy

    # two transactions should exist (buy + sell)
    txs = ss.get_transactions_by_portfolio(port.id, "buyer2")
    assert len(txs) == 2


def test_security_service_buy_sell_errors(db_session):
    us = UserService()
    ps = PortfolioService()
    ss = SecurityService()

    # ensure AAPL exists for these checks
    db_session.add(Security(ticker="AAPL", name="Apple Inc.", price=Decimal('276.00')))
    db_session.commit()

    # user with low balance
    us.create_user("Low", "Bal", "lowbal", "pw", 1.00)
    p = ps.create_portfolio("lowbal", "p", "d")

    # buy with insufficient balance -> since AAPL exists, should raise ValueError for insufficient funds
    with pytest.raises(ValueError):
        ss.buy_security("lowbal", "AAPL", 100.00, p.id)

    # admin cannot buy
    us.create_user("Admin", "One", "ad", "pw", 10000.00, role="admin")
    p2 = ps.create_portfolio("ad", "adminp", "d")
    with pytest.raises(PermissionError):
        ss.buy_security("ad", "AAPL", 100.00, p2.id)

    # amount too low to buy
    us.create_user("Tiny", "Buyer", "tiny", "pw", 1000.00)
    pt = ps.create_portfolio("tiny", "t", "d")
    with pytest.raises(ValueError):
        ss.buy_security("tiny", "AAPL", 10.00, pt.id)

    # sell errors: non-existent user
    with pytest.raises(NotFoundError):
        ss.sell_security("nouser", "AAPL", 10.00, p.id)

    # sell non-existent investment
    us.create_user("Seller", "One", "seller", "pw", 1000.00)
    ps.create_portfolio("seller", "s", "d")
    with pytest.raises(NotFoundError):
        ss.sell_security("seller", "AAPL", 10.00, 9999)


def test_transaction_permission_checks(db_session):
    us = UserService()
    ps = PortfolioService()
    ss = SecurityService()

    us.create_user("Owner", "One", "owner", "pw", 2000.00)
    us.create_user("Other", "Two", "other", "pw", 2000.00)
    us.create_user("Admin", "Root", "admin", "pw", 0.00, role="admin")

    port = ps.create_portfolio("owner", "Sec", "desc")
    db_session.add(Security(ticker="TP", name="TP Co", price=Decimal('20.00')))
    db_session.commit()
    ss.buy_security("owner", "TP", 100.00, port.id)

    # owner can view their transactions
    txs_owner = ss.get_transactions_by_user(us.get_user("owner").id, "owner")
    assert len(txs_owner) >= 1

    # other user may not view owner's transactions
    with pytest.raises(PermissionError):
        ss.get_transactions_by_user(us.get_user("owner").id, "other")

    # admin can view
    txs_admin = ss.get_transactions_by_user(us.get_user("owner").id, "admin")
    assert len(txs_admin) >= 1


def test_list_and_get_security_errors(db_session):
    ss = SecurityService()

    # ensure marketplace empty for this test
    secs = ss.list_securities()
    # list should return a list (may be empty)
    assert isinstance(secs, list)

    # get non-existent security should raise NotFoundError
    with pytest.raises(NotFoundError):
        ss.get_security("NOPE")


def test_buy_user_portfolio_security_not_found(db_session):
    us = UserService()
    ps = PortfolioService()
    ss = SecurityService()

    # user not found
    with pytest.raises(NotFoundError):
        ss.buy_security("ghost", "AAPL", 100.00, 1)

    # create user but no portfolio -> portfolio not found
    us.create_user("B1", "Buyer", "b1", "pw", 1000.00)
    with pytest.raises(NotFoundError):
        ss.buy_security("b1", "AAPL", 100.00, 9999)

    # create portfolio but security missing -> NotFoundError
    p = ps.create_portfolio("b1", "p", "d")
    with pytest.raises(NotFoundError):
        ss.buy_security("b1", "NOSYM", 100.00, p.id)


def test_sell_amount_edge_cases(db_session):
    us = UserService()
    ps = PortfolioService()
    ss = SecurityService()

    us.create_user("S1", "Sell", "s1", "pw", 1000.00)
    p = ps.create_portfolio("s1", "sp", "d")
    # add security and buy 1 share at price 100
    from decimal import Decimal
    db_session.add(Security(ticker="P100", name="P100 Co", price=Decimal('100.00')))
    db_session.commit()
    ss.buy_security("s1", "P100", 100.00, p.id)  # buys 1 share

    # attempt to sell amount greater than total value -> raises ValueError
    with pytest.raises(ValueError):
        ss.sell_security("s1", "P100", 1000.00, p.id)

    # amount too low to sell any share (price 100, amount 10)
    with pytest.raises(ValueError):
        ss.sell_security("s1", "P100", 10.00, p.id)

    # attempt to sell more shares than owned -> compute amount that results in >1 share when only 1 exists
    with pytest.raises(ValueError):
        ss.sell_security("s1", "P100", 300.00, p.id)


def test_get_transactions_by_portfolio_and_security_permissions(db_session):
    us = UserService()
    ps = PortfolioService()
    ss = SecurityService()

    # requester not found for portfolio queries
    with pytest.raises(NotFoundError):
        ss.get_transactions_by_portfolio(1, "noone")

    # create users and portfolio
    us.create_user("Owner2", "Two", "owner2", "pw", 2000.00)
    us.create_user("Other2", "Two", "other2", "pw", 2000.00)
    us.create_user("Admin2", "Root", "admin2", "pw", 0.00, role="admin")

    port = ps.create_portfolio("owner2", "Sec2", "desc")
    from decimal import Decimal
    db_session.add(Security(ticker="SSEC", name="SSEC Co", price=Decimal('10.00')))
    db_session.commit()
    ss.buy_security("owner2", "SSEC", 50.00, port.id)

    # portfolio not found
    with pytest.raises(NotFoundError):
        ss.get_transactions_by_portfolio(9999, "owner2")

    # other user cannot view
    with pytest.raises(PermissionError):
        ss.get_transactions_by_portfolio(port.id, "other2")

    # owner can view
    txs = ss.get_transactions_by_portfolio(port.id, "owner2")
    assert isinstance(txs, list) and len(txs) >= 1

    # admin can view
    txs_admin = ss.get_transactions_by_portfolio(port.id, "admin2")
    assert isinstance(txs_admin, list) and len(txs_admin) >= 1

    # security-level permissions: requester not found
    with pytest.raises(NotFoundError):
        ss.get_transactions_by_security("SSEC", "ghost")

    # other2 doesn't own any investment in SSEC -> permission error
    with pytest.raises(PermissionError):
        ss.get_transactions_by_security("SSEC", "other2")

    # owner2 can view by security
    txs_sec = ss.get_transactions_by_security("SSEC", "owner2")
    assert isinstance(txs_sec, list) and len(txs_sec) >= 1

    # admin can view security transactions
    txs_sec_admin = ss.get_transactions_by_security("SSEC", "admin2")
    assert isinstance(txs_sec_admin, list) and len(txs_sec_admin) >= 1
