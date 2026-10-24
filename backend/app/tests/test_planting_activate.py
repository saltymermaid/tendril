"""Tests for marking a planned planting as planted (shared by REST activate and the MCP tool)."""

from datetime import date

import pytest
from fastapi import HTTPException

from app.models.event import Event
from app.models.planting import Planting
from app.models.variety import Variety
from app.routers.plantings import activate_planting_in_place


class _FakeResult:
    def __init__(self, plantings):
        self._plantings = plantings

    def scalars(self):
        return self

    def all(self):
        return self._plantings


class _FakeSession:
    """Just enough of AsyncSession for activate: queries return `growing` (nothing by
    default — no overlaps, nothing still in the ground); records adds."""

    def __init__(self, growing=()):
        self.growing = list(growing)
        self.added = []

    async def execute(self, _query):
        return _FakeResult(self.growing)

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


def _growing(id=5, **kw):
    fields = dict(
        id=id,
        user_id=1,
        container_id=2,
        variety_id=4,
        square_x=0,
        square_y=0,
        square_width=1,
        square_height=1,
        start_date=date(2026, 6, 1),
        end_date=date(2026, 9, 1),
        status="in_progress",
        variety=Variety(id=4, name="Roselle"),
    )
    fields.update(kw)
    return Planting(**fields)


async def test_activate_refuses_while_something_is_still_growing_there():
    old = _growing()
    with pytest.raises(HTTPException) as exc:
        await activate_planting_in_place(_FakeSession([old]), _planting(), date(2026, 10, 1))

    assert exc.value.status_code == 409
    assert "Roselle (planting 5) still growing" in exc.value.detail["message"]
    assert exc.value.detail["still_growing"] == [
        {"id": 5, "variety_name": "Roselle", "start_date": "2026-06-01"}
    ]
    assert old.status == "in_progress"


async def test_activate_with_replace_reason_completes_whats_still_growing():
    old = _growing()
    planting = _planting()
    await activate_planting_in_place(_FakeSession([old]), planting, date(2026, 10, 1), "harvest_complete")

    assert old.status == "complete"
    assert old.end_date == date(2026, 10, 1)
    assert old.removal_reason == "harvest_complete"
    assert planting.status == "in_progress"


async def test_activate_rejects_unknown_replace_reason():
    with pytest.raises(HTTPException, match="Invalid removal reason"):
        await activate_planting_in_place(_FakeSession([_growing()]), _planting(), date(2026, 10, 1), "eaten")


async def test_activate_ignores_growing_plantings_on_other_squares():
    elsewhere = _growing(square_x=3)
    planting = _planting()
    await activate_planting_in_place(_FakeSession([elsewhere]), planting, date(2026, 10, 1))

    assert planting.status == "in_progress"
    assert elsewhere.status == "in_progress"
