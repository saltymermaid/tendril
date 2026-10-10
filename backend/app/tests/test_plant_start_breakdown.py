"""Tests for the PlantStart available / planned / transplanted breakdown."""

from datetime import date

from app.models.plant_start import PlantStart
from app.models.planting import Planting


def _planting(status, quantity):
    return Planting(status=status, quantity=quantity, start_date=date(2026, 10, 1), end_date=date(2026, 12, 1))


def test_breakdown_splits_by_planting_status():
    start = PlantStart(
        quantity=1,
        plantings=[
            _planting("in_progress", 1),
            _planting("complete", 1),
            _planting("not_started", 2),
        ],
    )
    assert start.transplanted_quantity == 2
    assert start.planned_quantity == 2
    assert start.total_quantity == 5


def test_null_planting_quantity_counts_as_one():
    start = PlantStart(quantity=0, plantings=[_planting("not_started", None)])
    assert start.planned_quantity == 1
    assert start.total_quantity == 1


def test_no_plantings():
    start = PlantStart(quantity=4, plantings=[])
    assert (start.planned_quantity, start.transplanted_quantity, start.total_quantity) == (0, 0, 4)
