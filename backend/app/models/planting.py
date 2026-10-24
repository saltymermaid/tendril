"""Planting model — the core data structure."""

from datetime import date, datetime

from sqlalchemy import ColumnElement, Date, DateTime, ForeignKey, Integer, String, and_, func, or_
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Planting(Base):
    """A planting record assigning a variety to a square/level for a time period. Per-user data."""

    __tablename__ = "plantings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    container_id: Mapped[int] = mapped_column(ForeignKey("containers.id", ondelete="CASCADE"), nullable=False)
    variety_id: Mapped[int] = mapped_column(ForeignKey("varieties.id", ondelete="CASCADE"), nullable=False)
    start_id: Mapped[int | None] = mapped_column(
        ForeignKey("plant_starts.id", ondelete="SET NULL"), nullable=True
    )  # The Plant Start this was transplanted from, if any

    # Position
    square_x: Mapped[int] = mapped_column(Integer, nullable=False)
    square_y: Mapped[int] = mapped_column(Integer, nullable=False)
    square_width: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 1 or 2
    square_height: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 1 or 2
    tower_level: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Only for tower plantings

    # Dates
    start_date: Mapped[date] = mapped_column(Date, nullable=False)  # When this went into the ground/square
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    seed_start_date: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )  # When the seed was started, if transplanted — anchors days_to_harvest, since that's measured from seed

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
    plant_start: Mapped["PlantStart | None"] = relationship(back_populates="plantings")  # noqa: F821
    events: Mapped[list["Event"]] = relationship(back_populates="planting")  # noqa: F821
    journal_notes: Mapped[list["JournalNote"]] = relationship(back_populates="planting")  # noqa: F821
    tasks: Mapped[list["Task"]] = relationship(back_populates="planting")  # noqa: F821

    @classmethod
    def in_ground_on(cls, on: date) -> ColumnElement[bool]:
        """SQL filter for plantings occupying their squares on `on`.

        end_date is only an estimate, so a planting that's still in_progress past it stays
        in the ground until it's marked complete — through today, not into the future, so
        views of upcoming dates still show the plan.
        """
        not_ended = cls.end_date > on
        if on <= date.today():
            not_ended = or_(not_ended, cls.status == "in_progress")
        return and_(cls.start_date <= on, not_ended)

    def __repr__(self) -> str:
        return f"<Planting(id={self.id}, variety_id={self.variety_id}, status='{self.status}')>"
