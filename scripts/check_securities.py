"""Check current securities in the configured database and print them.

Run with:
    py scripts/check_securities.py

This script will print ticker, name, and price for all rows in the `security` table
using the same `app.db` configuration as the application.
"""
import os
import sys
from decimal import Decimal

# Ensure project root is on sys.path so `from app import ...` works
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.db import get_session
from app.models import Security


def print_securities():
    session = get_session()
    try:
        secs = session.query(Security).all()
        if not secs:
            print("No securities found in DB.")
            return
        print(f"{'Ticker':10}{'Name':40}{'Price':>10}")
        for s in secs:
            price = Decimal(getattr(s, "price", Decimal('0.00')))
            print(f"{s.ticker:10}{getattr(s, 'name', ''):40}{price:10.2f}")
    finally:
        session.close()


if __name__ == "__main__":
    print_securities()
