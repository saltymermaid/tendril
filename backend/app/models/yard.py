"""Yard and YardObject models — spatial layout of a garden area."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Yard(Base):
    """A named area of the garden (e.g. "North yard"), laid out as a grid of squares. Per-user data."""

    __tablename__ = "yards"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="yards")  # noqa: F821
    objects: Mapped[list["YardObject"]] = relationship(
        back_populates="yard", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Yard(id={self.id}, name='{self.name}', {self.width}x{self.height})>"


class YardObject(Base):
    """Something occupying one or more squares of a yard — a placed bed or a freeform feature."""

    __tablename__ = "yard_objects"
    __table_args__ = (UniqueConstraint("container_id", name="uq_yard_objects_container_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    yard_id: Mapped[int] = mapped_column(ForeignKey("yards.id", ondelete="CASCADE"), nullable=False)
    object_type: Mapped[str] = mapped_column(String(20), nullable=False)  # bed, path, mulch, building, tree, water, other
    container_id: Mapped[int | None] = mapped_column(
        ForeignKey("containers.id", ondelete="CASCADE"), nullable=True
    )
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Position — top-left corner
    square_x: Mapped[int] = mapped_column(Integer, nullable=False)
    square_y: Mapped[int] = mapped_column(Integer, nullable=False)

    # Footprint — required for non-bed types; null for "bed" (derived live from the container's own size)
    square_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    square_height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    yard: Mapped["Yard"] = relationship(back_populates="objects")
    container: Mapped["Container | None"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<YardObject(id={self.id}, yard_id={self.yard_id}, type='{self.object_type}')>"
