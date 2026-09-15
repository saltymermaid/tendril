"""PlantStart model — a batch of seedlings started in trays, not yet assigned to a bed."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PlantStart(Base):
    """A started batch of a variety (e.g. seeded in trays), with a remaining quantity
    not yet planted into a bed. Per-user data. No location — just variety, date, quantity."""

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

    def __repr__(self) -> str:
        return f"<PlantStart(id={self.id}, variety_id={self.variety_id}, quantity={self.quantity})>"
