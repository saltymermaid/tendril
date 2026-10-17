"""Tests for moving a planting to a different spot (shared by REST update and the MCP tool)."""

from datetime import date

import pytest
from fastapi import HTTPException

from app.models.container import Container
from app.models.planting import Planting
from app.routers.plantings import move_planting_in_place


class _FakeResult:
    def __init__(self, plantings):
        self._plantings = plantings

    def scalars(self):
        return self

    def all(self):
        return self._plantings


class _FakeSession:
    """Just enough of AsyncSession for a move: the overlap query returns `existing`;
    the bulk UPDATEs that re-point events/notes/tasks are recorded."""

    def __init__(self, existing=()):
        self.existing = list(existing)
        self.updates = []

    async def execute(self, query):
        if query.is_select:
            return _FakeResult(self.existing)
        self.updates.append(query)
        return _FakeResult([])


def _planting(status="in_progress", **kw):
    fields = dict(
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
    )
    fields.update(kw)
    return Planting(**fields)


def _bed(id=2, width=4, height=4):
    return Container(id=id, user_id=1, name="Bed", type="grid_bed", width=width, height=height)


def _tower(id=5, levels=4, pockets=6):
    return Container(id=id, user_id=1, name="Tower", type="tower", levels=levels, pockets_per_level=pockets)


async def test_move_within_bed_keeps_status_and_repoints_history():
    db = _FakeSession()
    planting = _planting()
    bed = _bed()
    await move_planting_in_place(db, planting, bed, square_x=3, square_y=2, tower_level=None)

    assert (planting.container_id, planting.square_x, planting.square_y) == (2, 3, 2)
    assert planting.status == "in_progress"
    # events, journal notes, tasks
    assert len(db.updates) == 3


async def test_move_to_another_container():
    planting = _planting()
    other = _bed(id=9)
    await move_planting_in_place(_FakeSession(), planting, other, square_x=1, square_y=1, tower_level=None)
    assert planting.container is other
    assert planting.container_id == 9


async def test_move_into_tower_requires_level_and_out_of_tower_clears_it():
    planting = _planting()
    with pytest.raises(HTTPException, match="tower_level required"):
        await move_planting_in_place(_FakeSession(), planting, _tower(), 1, 0, tower_level=None)

    await move_planting_in_place(_FakeSession(), planting, _tower(), 1, 0, tower_level=2)
    assert planting.tower_level == 2

    await move_planting_in_place(_FakeSession(), planting, _bed(), 1, 1, tower_level=2)
    assert planting.tower_level is None


async def test_move_rejects_out_of_bounds_keeping_footprint():
    planting = _planting(square_width=2, square_height=2)
    with pytest.raises(HTTPException, match="beyond container bounds"):
        await move_planting_in_place(_FakeSession(), planting, _bed(), 3, 0, tower_level=None)
    assert planting.square_x == 0


async def test_move_rejects_overlap_at_new_spot():
    occupant = _planting(id=8, square_x=2, square_y=2)
    planting = _planting()
    with pytest.raises(HTTPException, match="Overlap"):
        await move_planting_in_place(_FakeSession([occupant]), planting, _bed(), 2, 2, tower_level=None)
    assert planting.square_x == 0
