"""Category and related models (PlantingSeason, CompanionRule)."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Category(Base):
    """Plant category (e.g., Tomatoes, Peppers). Global shared data."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)  # Hex color e.g. #FF5733
    harvest_type: Mapped[str] = mapped_column(String(20), nullable=False, default="continuous")  # single/continuous
    icon_svg: Mapped[str | None] = mapped_column(Text, nullable=True)  # SVG markup or emoji placeholder
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    planting_seasons: Mapped[list["PlantingSeason"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )
    varieties: Mapped[list["Variety"]] = relationship(back_populates="category")  # noqa: F821
    companion_rules: Mapped[list["CompanionRule"]] = relationship(
        back_populates="category",
        foreign_keys="CompanionRule.category_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}')>"


class PlantingSeason(Base):
    """Zone-specific planting season for a category. Global shared data."""

    __tablename__ = "planting_seasons"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    usda_zone: Mapped[str] = mapped_column(String(10), nullable=False)  # e.g. "10a"
    start_month: Mapped[int] = mapped_column(Integer, nullable=False)
    start_day: Mapped[int] = mapped_column(Integer, nullable=False)
    end_month: Mapped[int] = mapped_column(Integer, nullable=False)
    end_day: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    category: Mapped["Category"] = relationship(back_populates="planting_seasons")

    def __repr__(self) -> str:
        return f"<PlantingSeason(category_id={self.category_id}, zone='{self.usda_zone}', {self.start_month}/{self.start_day}-{self.end_month}/{self.end_day})>"


class CompanionRule(Base):
    """Companion planting rule between two categories. Global shared data."""

    __tablename__ = "companion_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    companion_category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # compatible/incompatible

    # Relationships
    category: Mapped["Category"] = relationship(
        back_populates="companion_rules", foreign_keys=[category_id]
    )
    companion_category: Mapped["Category"] = relationship(foreign_keys=[companion_category_id])

    def __repr__(self) -> str:
        return f"<CompanionRule(cat={self.category_id}, companion={self.companion_category_id}, type='{self.relationship_type}')>"
