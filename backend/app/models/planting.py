"""Planting model — the core data structure."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Planting(Base):
    """A planting record assigning a variety to a square/level for a time period. Per-user data."""

    __tablename__ = "plantings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    container_id: Mapped[int] = mapped_column(ForeignKey("containers.id", ondelete="CASCADE"), nullable=False)
    variety_id: Mapped[int] = mapped_column(ForeignKey("varieties.id", ondelete="CASCADE"), nullable=False)

    # Position
    square_x: Mapped[int] = mapped_column(Integer, nullable=False)
    square_y: Mapped[int] = mapped_column(Integer, nullable=False)
    square_width: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 1 or 2
    square_height: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 1 or 2
    tower_level: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Only for tower plantings

    # Dates
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="not_started"
    )  # not_started, in_progress, complete
    planting_method: Mapped[str | None] = mapped_column(String(20), nullable=True)  # direct_sow, transplant
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    removal_reason: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # harvest_complete, died, pulled_early, pest_disease, other

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="plantings")  # noqa: F821
    container: Mapped["Container"] = relationship(back_populates="plantings")  # noqa: F821
    variety: Mapped["Variety"] = relationship(back_populates="plantings")  # noqa: F821
    events: Mapped[list["Event"]] = relationship(back_populates="planting")  # noqa: F821
    journal_notes: Mapped[list["JournalNote"]] = relationship(back_populates="planting")  # noqa: F821
    tasks: Mapped[list["Task"]] = relationship(back_populates="planting")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Planting(id={self.id}, variety_id={self.variety_id}, status='{self.status}')>"
