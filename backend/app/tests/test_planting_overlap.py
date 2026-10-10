"""Tests for which squares/pockets count as occupied in the planting overlap check."""

from app.models.planting import Planting
from app.routers.plantings import _occupies_same_squares


def _planting(x, y, w=1, h=1, tower_level=None):
    return Planting(square_x=x, square_y=y, square_width=w, square_height=h, tower_level=tower_level)


def test_tower_same_pocket_different_level_is_free():
    existing = _planting(2, 0, tower_level=0)
    assert not _occupies_same_squares(existing, 2, 0, 1, 1, tower_level=1)


def test_tower_same_pocket_same_level_collides():
    existing = _planting(2, 0, tower_level=1)
    assert _occupies_same_squares(existing, 2, 0, 1, 1, tower_level=1)


def test_tower_different_pocket_same_level_is_free():
    existing = _planting(2, 0, tower_level=1)
    assert not _occupies_same_squares(existing, 3, 0, 1, 1, tower_level=1)


def test_grid_multi_square_planting_collides():
    existing = _planting(0, 0, w=2, h=2)
    assert _occupies_same_squares(existing, 1, 1, 1, 1, tower_level=None)
    assert not _occupies_same_squares(existing, 2, 0, 1, 1, tower_level=None)


def test_recommendation_footprint_maps_tower_to_pocket_by_level():
    from app.services.recommendations import _footprint

    tower = _planting(3, 0, tower_level=2)
    assert _footprint(tower, is_tower=True) == (3, 2, 1, 1)
    grid = _planting(1, 2, w=2, h=1)
    assert _footprint(grid, is_tower=False) == (1, 2, 2, 1)
