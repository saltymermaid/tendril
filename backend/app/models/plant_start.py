"""PlantStart model — a batch of seedlings started in trays, not yet assigned to a bed."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PlantStart(Base):
    """A started batch of a variety (e.g. seeded in trays), with a remaining quantity
    not yet planted into a bed. Per-user data. No location — just variety, date, quantity.

    `quantity` is what's still available to assign. Seedlings assigned to a bed are
    subtracted from it and tracked via the linked plantings: a `not_started` planting
    reserves them (still in the tray, but spoken for); once the planting is in progress
    or complete they've been transplanted. Breakdown properties need `plantings` loaded."""

    __tablename__ = "plant_starts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    variety_id: Mapped[int] = mapped_column(ForeignKey("varieties.id", ondelete="CASCADE"), nullable=False)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="plant_starts")  # noqa: F821
    variety: Mapped["Variety"] = relationship(back_populates="plant_starts")  # noqa: F821
    plantings: Mapped[list["Planting"]] = relationship(back_populates="plant_start")  # noqa: F821

    @property
    def planned_quantity(self) -> int:
        """Seedlings reserved by planned (not_started) plantings — still in the tray."""
        return sum(p.quantity or 1 for p in self.plantings if p.status == "not_started")

    @property
    def transplanted_quantity(self) -> int:
        """Seedlings already in the ground (in_progress or complete plantings)."""
        return sum(p.quantity or 1 for p in self.plantings if p.status != "not_started")

    @property
    def total_quantity(self) -> int:
        return self.quantity + self.planned_quantity + self.transplanted_quantity

    def __repr__(self) -> str:
        return f"<PlantStart(id={self.id}, variety_id={self.variety_id}, quantity={self.quantity})>"
