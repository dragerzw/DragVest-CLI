from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Float, ForeignKey, String
from app.db import Base

if TYPE_CHECKING:
    from .portfolio import Portfolio
    from .security import Security

class Investment(Base):
    __tablename__ = "investment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), ForeignKey("security.ticker"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    purchase_price: Mapped[float] = mapped_column(Float, nullable=False)
    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey("portfolio.id"), nullable=False)

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="investments")
    security: Mapped["Security"] = relationship("Security", back_populates="investments")
