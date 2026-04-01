"""JournalNote model — free-form observational notes."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JournalNote(Base):
    """A free-form journal note. Per-user data."""

    __tablename__ = "journal_notes"

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
    square_x: Mapped[int | None] = mapped_column(Integer, nullable=True)
    square_y: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tower_level: Mapped[int | None] = mapped_column(Integer, nullable=True)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="journal_notes")  # noqa: F821
    container: Mapped["Container"] = relationship()  # noqa: F821
    planting: Mapped["Planting"] = relationship(back_populates="journal_notes")  # noqa: F821
    variety: Mapped["Variety"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<JournalNote(id={self.id}, date={self.date})>"
