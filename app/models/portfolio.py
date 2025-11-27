from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey
from app.db import Base

if TYPE_CHECKING:
    from .user import User
    from .investment import Investment

class Portfolio(Base):
    __tablename__ = "portfolio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    owner_username: Mapped[str] = mapped_column(String(50), ForeignKey("user.username"), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="portfolios")
    investments: Mapped[list["Investment"]] = relationship(
        "Investment",
        back_populates="portfolio",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Backwards-compatible alias: some code refers to `holdings`
    @property
    def holdings(self) -> list["Investment"]:
        return self.investments
