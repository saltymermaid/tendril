"""User model."""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """User account, created on first OAuth login."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    varieties: Mapped[list["Variety"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # noqa: F821
    containers: Mapped[list["Container"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # noqa: F821
    plantings: Mapped[list["Planting"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # noqa: F821
    events: Mapped[list["Event"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # noqa: F821
    journal_notes: Mapped[list["JournalNote"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # noqa: F821
    tasks: Mapped[list["Task"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # noqa: F821
    push_subscriptions: Mapped[list["PushSubscription"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # noqa: F821

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
