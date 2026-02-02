from typing import List
from decimal import Decimal
from app.db import get_session
from app.models import Security, Portfolio, Investment, User, Transaction
from sqlalchemy.orm import selectinload
from app.service.exceptions import NotFoundError


class SecurityService:
	"""Service for securities and transaction logging using SQLAlchemy/MySQL."""
	def list_securities(self) -> List[Security]:
		session = get_session()
		try:
			secs = session.query(Security).all()
			return secs
		finally:
			session.close()

	def get_security(self, ticker: str) -> Security:
		session = get_session()
		try:
			sec = session.query(Security).filter_by(ticker=ticker).one_or_none()
			if not sec:
				raise NotFoundError(f"ticker '{ticker}' not found")
			return sec
		finally:
			session.close()

	def buy_security(self, username: str, ticker: str, amount: float, portfolio_id: int) -> None:
		session = get_session()
		try:
			user = session.query(User).filter_by(username=username).one_or_none()
			if not user:
				raise NotFoundError(f"User '{username}' not found.")
			if user.role != "customer":
				raise PermissionError("Only customers can buy securities.")

			portfolio = session.query(Portfolio).filter_by(owner_username=username, id=portfolio_id).one_or_none()
			if not portfolio:
				raise NotFoundError(f"Portfolio with ID '{portfolio_id}' not found for user '{username}'.")

			security = session.query(Security).filter_by(ticker=ticker).one_or_none()
			if not security:
				raise NotFoundError(f"Security '{ticker}' not found in the marketplace.")

			# Ensure security.price is a Decimal for safe arithmetic
			price = Decimal(str(security.price))
			amt = Decimal(str(amount))
			# normalize user balance to Decimal for comparisons and arithmetic
			ubal = Decimal(str(user.balance)) if not isinstance(user.balance, Decimal) else user.balance
			if amt > ubal:
				raise ValueError("Insufficient balance to buy security.")

			quantity = int(amt // price)
			if quantity <= 0:
				raise ValueError("Investment amount is too low to buy any shares.")

			total_cost = Decimal(quantity) * price
			# perform assignment to avoid float/Decimal in-place ops
			ubal = Decimal(str(user.balance)) if not isinstance(user.balance, Decimal) else user.balance
			ubal = ubal - total_cost
			user.balance = ubal

			investment = session.query(Investment).filter_by(portfolio_id=portfolio_id, ticker=ticker).one_or_none()
			if investment:
				investment.quantity += quantity
				investment.purchase_price = price
			else:
				investment = Investment(ticker=ticker, quantity=quantity, purchase_price=price, portfolio_id=portfolio_id)
				session.add(investment)

			# Log transaction
			transaction = Transaction(
				user_id=user.id,
				portfolio_id=portfolio_id,
				security_id=ticker,
				action="BUY",
				quantity=quantity,
				price=price,
			)
			session.add(transaction)

			session.commit()
		finally:
			session.close()

	def sell_security(self, username: str, ticker: str, amount: float, portfolio_id: int) -> None:
		session = get_session()
		try:
			user = session.query(User).filter_by(username=username).one_or_none()
			if not user:
				raise NotFoundError(f"User '{username}' not found.")
			if user.role != "customer":
				raise PermissionError("Only customers can sell securities.")

			portfolio = session.query(Portfolio).filter_by(owner_username=username, id=portfolio_id).one_or_none()
			if not portfolio:
				raise NotFoundError(f"Portfolio with ID '{portfolio_id}' not found for user '{username}'.")

			investment = session.query(Investment).filter_by(portfolio_id=portfolio_id, ticker=ticker).one_or_none()
			if not investment:
				raise NotFoundError(f"Security '{ticker}' not found in portfolio '{portfolio.name if portfolio else ''}'.")

			security = session.query(Security).filter_by(ticker=ticker).one_or_none()
			if not security:
				raise NotFoundError(f"Security '{ticker}' not found in the marketplace.")

			# Ensure security.price is Decimal for arithmetic
			price = Decimal(str(security.price))
			amt = Decimal(str(amount))
			total_value = Decimal(investment.quantity) * price
			if amt > total_value:
				raise ValueError("Amount exceeds the total value of the investment.")

			quantity_to_sell = int(amt // price)
			if quantity_to_sell <= 0:
				raise ValueError("Amount is too low to sell any shares.")
			if quantity_to_sell > investment.quantity:
				raise ValueError("Not enough shares to sell.")
			investment.quantity -= quantity_to_sell
			if investment.quantity == 0:
				session.delete(investment)

			proceeds = Decimal(quantity_to_sell) * price
			ubal = Decimal(str(user.balance)) if not isinstance(user.balance, Decimal) else user.balance
			ubal = ubal + proceeds
			user.balance = ubal

			transaction = Transaction(
				user_id=user.id,
				portfolio_id=portfolio_id,
				security_id=ticker,
				action="SELL",
				quantity=quantity_to_sell,
				price=price,
			)
			session.add(transaction)

			session.commit()
		finally:
			session.close()

	# Query transaction history
	def get_transactions_by_user(self, user_id: int, requesting_username: str) -> List[Transaction]:
		"""Return transactions for a given user id if requesting user is the owner or an admin."""
		session = get_session()
		try:
			requester = session.query(User).filter_by(username=requesting_username).one_or_none()
			if not requester:
				raise NotFoundError(f"Requesting user '{requesting_username}' not found")
			if requester.role != "admin" and requester.id != user_id:
				raise PermissionError("Not authorized to view these transactions.")

			txs = (
				session.query(Transaction)
				.options(selectinload(Transaction.user), selectinload(Transaction.portfolio), selectinload(Transaction.security))
				.filter_by(user_id=user_id)
				.order_by(Transaction.timestamp.desc())
				.all()
			)
			return txs
		finally:
			session.close()

	def get_transactions_by_portfolio(self, portfolio_id: int, requesting_username: str) -> List[Transaction]:
		"""Return transactions for a portfolio if requesting user is the portfolio owner or an admin."""
		session = get_session()
		try:
			requester = session.query(User).filter_by(username=requesting_username).one_or_none()
			if not requester:
				raise NotFoundError(f"Requesting user '{requesting_username}' not found")

			portfolio = session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
			if not portfolio:
				raise NotFoundError(f"Portfolio id '{portfolio_id}' not found")

			if requester.role != "admin" and portfolio.owner_username != requesting_username:
				raise PermissionError("Not authorized to view these transactions.")

			txs = (
				session.query(Transaction)
				.options(selectinload(Transaction.user), selectinload(Transaction.portfolio), selectinload(Transaction.security))
				.filter_by(portfolio_id=portfolio_id)
				.order_by(Transaction.timestamp.desc())
				.all()
			)
			return txs
		finally:
			session.close()

	def get_transactions_by_security(self, security_id: str, requesting_username: str) -> List[Transaction]:
		"""Return transactions for a security if requester is admin or owns portfolios holding that security."""
		session = get_session()
		try:
			requester = session.query(User).filter_by(username=requesting_username).one_or_none()
			if not requester:
				raise NotFoundError(f"Requesting user '{requesting_username}' not found")

			if requester.role != "admin":
				# Check if requester owns any portfolio with investments in this security
				own_inv = (
					session.query(Investment)
					.join(Portfolio, Investment.portfolio_id == Portfolio.id)
					.filter(Portfolio.owner_username == requesting_username, Investment.ticker == security_id)
					.first()
				)
				if not own_inv:
					raise PermissionError("Not authorized to view these transactions.")

			txs = (
				session.query(Transaction)
				.options(selectinload(Transaction.user), selectinload(Transaction.portfolio), selectinload(Transaction.security))
				.filter_by(security_id=security_id)
				.order_by(Transaction.timestamp.desc())
				.all()
			)
			return txs
		finally:
			session.close()


