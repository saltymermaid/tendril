"""Container and SquareSupport models."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Container(Base):
    """A garden container (grid bed or tower). Per-user data."""

    __tablename__ = "containers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # grid_bed / tower
    location_description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Grid bed dimensions (nullable — only for grid_bed type)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Tower dimensions (nullable — only for tower type)
    levels: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pockets_per_level: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Irrigation
    irrigation_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # drip, manual, sprinkler
    irrigation_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    irrigation_frequency: Mapped[str | None] = mapped_column(String(100), nullable=True)  # daily, 2x_daily, every_X_days, specific_days

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="containers")  # noqa: F821
    plantings: Mapped[list["Planting"]] = relationship(back_populates="container")  # noqa: F821
    square_supports: Mapped[list["SquareSupport"]] = relationship(
        back_populates="container", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Container(id={self.id}, name='{self.name}', type='{self.type}')>"


class SquareSupport(Base):
    """Support structure on a specific square of a grid bed."""

    __tablename__ = "square_supports"

    id: Mapped[int] = mapped_column(primary_key=True)
    container_id: Mapped[int] = mapped_column(
        ForeignKey("containers.id", ondelete="CASCADE"), nullable=False
    )
    square_x: Mapped[int] = mapped_column(Integer, nullable=False)
    square_y: Mapped[int] = mapped_column(Integer, nullable=False)
    support_type: Mapped[str] = mapped_column(String(20), nullable=False)  # trellis, cage, pole

    # Relationships
    container: Mapped["Container"] = relationship(back_populates="square_supports")

    def __repr__(self) -> str:
        return f"<SquareSupport(container={self.container_id}, x={self.square_x}, y={self.square_y}, type='{self.support_type}')>"
