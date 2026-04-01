"""Event model — structured planting and harvest events."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Event(Base):
    """A structured event (planting or harvest). Per-user data."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    container_id: Mapped[int | None] = mapped_column(
        ForeignKey("containers.id", ondelete="SET NULL"), nullable=True
    )
    planting_id: Mapped[int | None] = mapped_column(
        ForeignKey("plantings.id", ondelete="SET NULL"), nullable=True
    )
    variety_id: Mapped[int | None] = mapped_column(
        ForeignKey("varieties.id", ondelete="SET NULL"), nullable=True
    )

    event_type: Mapped[str] = mapped_column(String(20), nullable=False)  # planting, harvest
    date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)  # lbs, count, bunches
    square_x: Mapped[int | None] = mapped_column(Integer, nullable=True)
    square_y: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tower_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="events")  # noqa: F821
    container: Mapped["Container"] = relationship()  # noqa: F821
    planting: Mapped["Planting"] = relationship(back_populates="events")  # noqa: F821
    variety: Mapped["Variety"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, type='{self.event_type}', date={self.date})>"
