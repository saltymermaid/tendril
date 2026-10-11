"""Tests for marking a planned planting as planted (shared by REST activate and the MCP tool)."""

from datetime import date

import pytest
from fastapi import HTTPException

from app.models.event import Event
from app.models.planting import Planting
from app.routers.plantings import activate_planting_in_place


class _FakeResult:
    def scalars(self):
        return self

    def all(self):
        return []


class _FakeSession:
    """Just enough of AsyncSession for activate: no overlapping plantings, records adds."""

    def __init__(self):
        self.added = []

    async def execute(self, _query):
        return _FakeResult()

    def add(self, obj):
        self.added.append(obj)


def _planting(status="not_started"):
    return Planting(
        id=7,
        user_id=1,
        container_id=2,
        variety_id=3,
        square_x=0,
        square_y=0,
        square_width=1,
        square_height=1,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 12, 1),
        status=status,
        planting_method="direct_sow",
    )


async def test_activate_moves_start_date_and_logs_event():
    db = _FakeSession()
    planting = _planting()
    await activate_planting_in_place(db, planting, date(2026, 10, 11))

    assert planting.status == "in_progress"
    assert planting.start_date == date(2026, 10, 11)
    assert planting.end_date == date(2026, 12, 1)
    [event] = db.added
    assert isinstance(event, Event)
    assert event.event_type == "planting"
    assert event.date == date(2026, 10, 11)
    assert event.planting_id == 7


async def test_activate_rejects_already_planted():
    with pytest.raises(HTTPException, match="Only 'not_started'"):
        await activate_planting_in_place(_FakeSession(), _planting("in_progress"), None)


async def test_activate_rejects_start_on_or_after_end():
    with pytest.raises(HTTPException, match="before end_date"):
        await activate_planting_in_place(_FakeSession(), _planting(), date(2026, 12, 1))
