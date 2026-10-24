"""Tests for Planting.in_ground_on — which plantings occupy their squares on a date."""

from datetime import date, timedelta

from sqlalchemy.dialects import postgresql

from app.models.planting import Planting


def _sql(on: date) -> str:
    clause = Planting.in_ground_on(on)
    return str(clause.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))


def test_in_progress_plantings_stay_in_ground_past_their_end_date():
    for on in (date.today() - timedelta(days=30), date.today(), date.today() + timedelta(days=30)):
        sql = _sql(on)
        assert "plantings.start_date <=" in sql
        assert "plantings.end_date >" in sql
        assert "plantings.status = 'in_progress'" in sql
