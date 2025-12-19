from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Numeric
from decimal import Decimal
from app.database import sqldb as db

if TYPE_CHECKING:
    from .investment import Investment

class Security(db.Model):
    __tablename__ = "security"

    ticker: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    investments: Mapped[list["Investment"]] = relationship(
        "Investment",
        back_populates="security",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
