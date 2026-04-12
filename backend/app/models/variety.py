"""Variety model — per-user plant varieties."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Variety(Base):
    """A specific plant variety under a category. Per-user data."""

    __tablename__ = "varieties"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Season override (optional — overrides category planting season)
    season_override_start_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    season_override_start_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    season_override_end_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    season_override_end_day: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Growth data
    days_to_germination_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    days_to_germination_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    days_to_harvest_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    days_to_harvest_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seed_start_days: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Days to grow in tray before transplanting

    # Planting details
    planting_depth: Mapped[str | None] = mapped_column(String(50), nullable=True)
    spacing: Mapped[str] = mapped_column(String(10), nullable=False, default="1x1")  # 1x1, 1x2, 2x2
    sunlight: Mapped[str | None] = mapped_column(String(50), nullable=True)  # full_sun, partial_shade, etc.
    is_climbing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    planting_method: Mapped[str] = mapped_column(
        String(20), nullable=False, default="both"
    )  # direct_sow, transplant, both

    # Media & links
    seed_packet_photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="varieties")  # noqa: F821
    category: Mapped["Category"] = relationship(back_populates="varieties")  # noqa: F821
    plantings: Mapped[list["Planting"]] = relationship(back_populates="variety")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Variety(id={self.id}, name='{self.name}', category_id={self.category_id})>"
