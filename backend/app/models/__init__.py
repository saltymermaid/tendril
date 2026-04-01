"""SQLAlchemy models — import all models here so Alembic can discover them."""

from app.models.user import User
from app.models.category import Category, PlantingSeason, CompanionRule
from app.models.variety import Variety
from app.models.container import Container, SquareSupport
from app.models.planting import Planting
from app.models.event import Event
from app.models.journal_note import JournalNote
from app.models.task import Task
from app.models.push_subscription import PushSubscription

__all__ = [
    "User",
    "Category",
    "PlantingSeason",
    "CompanionRule",
    "Variety",
    "Container",
    "SquareSupport",
    "Planting",
    "Event",
    "JournalNote",
    "Task",
    "PushSubscription",
]
