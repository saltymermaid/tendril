"""Tests for Planting.in_ground_on — which plantings occupy their squares on a date."""

from datetime import date, timedelta

from sqlalchemy.dialects import postgresql

from app.models.planting import Planting


def _sql(on: date) -> str:
    clause = Planting.in_ground_on(on)
    return str(clause.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))


def test_today_keeps_in_progress_plantings_past_their_end_date():
    sql = _sql(date.today())
    assert "plantings.end_date >" in sql
    assert "plantings.status = 'in_progress'" in sql


def test_past_date_keeps_in_progress_plantings_past_their_end_date():
    assert "plantings.status = 'in_progress'" in _sql(date.today() - timedelta(days=30))


def test_future_date_uses_estimated_end_date_only():
    sql = _sql(date.today() + timedelta(days=1))
    assert "plantings.end_date >" in sql
    assert "status" not in sql
