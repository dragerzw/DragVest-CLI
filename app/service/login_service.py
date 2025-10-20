# app/service/login_service.py
from typing import Optional

import db  # Direct import since db.py is at project root and app runs as `python -m main`

class LoginService:
	"""
	Simple login service used by the CLI.
	Provides authenticate(username, password) -> bool and logout().
	If an `app.db` module is present and follows expected shape (users dict and logged_in_user var),
	it will be used to validate credentials and set the logged in user. Otherwise this service
	behaves in a safe, non-crashing fallback mode.
	"""

	def __init__(self) -> None:
		# no state required for now
		pass

	def authenticate(self, username: str, password: str) -> bool:
		"""
		Validate username/password against app.db if available.
		On success, sets db.logged_in_user to the user object (if db exists) and returns True.
		Returns False on failure.
		"""
		if db is None:
			# fallback: do not authenticate (no users available)
			return False

		# expected shape: db.users : dict[str, User], db.logged_in_user : Optional[User]
		users = getattr(db, "users", None)
		if not isinstance(users, dict):
			return False

		user = users.get(username)
		if user is None:
			return False

		# compare password attribute; be tolerant to attribute names
		user_password = getattr(user, "password", None)
		if user_password is None:
			return False

		if str(user_password) == str(password):
			# set logged in user if possible
			if hasattr(db, "logged_in_user"):
				try:
					setattr(db, "logged_in_user", user)
				except Exception:
					# ignore failures to set attribute
					pass
			return True
		return False

	def logout(self) -> None:
		"""Clear logged_in_user in db if present."""
		if db is None:
			return
		if hasattr(db, "logged_in_user"):
			try:
				setattr(db, "logged_in_user", None)
			except Exception:
				pass
			try:
				setattr(db, "logged_in_user", None)
			except Exception:
				pass
