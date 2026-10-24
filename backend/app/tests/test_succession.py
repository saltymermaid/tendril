"""Tests for overdue plantings and the planned plantings waiting on their squares."""

from datetime import date

from app.models.planting import Planting
from app.services.succession import is_overdue, next_plantings_for_overdue, shares_squares

TODAY = date(2026, 10, 24)


class _FakeResult:
    def __init__(self, plantings):
        self._plantings = plantings

    def scalars(self):
        return self

    def all(self):
        return self._plantings


class _FakeSession:
    """Returns `planned` for the not_started query, already sorted by start_date as SQL would."""

    def __init__(self, planned=()):
        self.planned = sorted(planned, key=lambda p: p.start_date)
        self.queries = 0

    async def execute(self, query):
        self.queries += 1
        return _FakeResult(self.planned)


def _planting(id, status="in_progress", **kw):
    fields = dict(
        id=id,
        user_id=1,
        container_id=2,
        variety_id=3,
        square_x=0,
        square_y=0,
        square_width=1,
        square_height=1,
        tower_level=None,
        start_date=date(2026, 8, 1),
        end_date=date(2026, 10, 1),
        status=status,
    )
    fields.update(kw)
    return Planting(**fields)


def test_is_overdue_only_for_in_progress_on_or_after_end_date():
    assert is_overdue(_planting(1), TODAY)
    assert is_overdue(_planting(1, end_date=TODAY), TODAY)
    assert not is_overdue(_planting(1, end_date=date(2026, 11, 1)), TODAY)
    assert not is_overdue(_planting(1, status="complete"), TODAY)
    assert not is_overdue(_planting(1, status="not_started"), TODAY)


def test_shares_squares_handles_multi_square_containers_and_tower_levels():
    big = _planting(1, square_width=2, square_height=2)
    assert shares_squares(big, _planting(2, square_x=1, square_y=1))
    assert not shares_squares(big, _planting(2, square_x=2))
    assert not shares_squares(big, _planting(2, container_id=9))
    assert not shares_squares(_planting(1, tower_level=0), _planting(2, tower_level=1))


async def test_next_planting_is_earliest_planned_on_shared_squares():
    old = _planting(1, square_width=2)
    later = _planting(2, status="not_started", square_x=1, start_date=date(2026, 12, 1), end_date=date(2027, 2, 1))
    sooner = _planting(3, status="not_started", start_date=date(2026, 10, 2), end_date=date(2026, 12, 1))
    elsewhere = _planting(4, status="not_started", square_y=3, start_date=date(2026, 10, 1), end_date=date(2026, 12, 1))

    nexts = await next_plantings_for_overdue(_FakeSession([later, sooner, elsewhere]), [old], TODAY)
    assert nexts == {1: sooner}


async def test_no_query_when_nothing_is_overdue():
    db = _FakeSession([_planting(2, status="not_started", start_date=date(2026, 12, 1))])
    on_time = _planting(1, end_date=date(2026, 11, 1))
    assert await next_plantings_for_overdue(db, [on_time], TODAY) == {}
    assert db.queries == 0
