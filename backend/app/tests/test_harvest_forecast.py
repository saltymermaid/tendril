"""Tests for the week-by-week harvest forecast bucketing."""

from datetime import date

from app.models.category import Category
from app.models.container import Container
from app.models.planting import Planting
from app.models.variety import Variety
from app.services.harvest_forecast import build_forecast, pluralize

# Wednesday — the forecast's first week is Mon 2026-09-28 .. Sun 2026-10-04
TODAY = date(2026, 9, 30)
BED = Container(id=1, name="Bed A")
_next_id = iter(range(1, 1000))


def _variety(
    name, harvest_type="single", override=None, unit=None, pps=None, dth=(60, 60), cat_unit=None, cat_pps=None
):
    cat = Category(
        id=next(_next_id),
        name=f"{name} cat",
        color="#123456",
        harvest_type=harvest_type,
        harvest_unit=cat_unit,
        plants_per_square=cat_pps,
    )
    return Variety(
        id=next(_next_id),
        name=name,
        category=cat,
        harvest_type_override=override,
        harvest_unit=unit,
        plants_per_square=pps,
        days_to_harvest_min=dth[0],
        days_to_harvest_max=dth[1],
    )


def _planting(variety, start, end, status="in_progress", quantity=None, seed_start=None):
    return Planting(
        id=next(_next_id),
        variety=variety,
        container=BED,
        container_id=BED.id,
        square_x=0,
        square_y=0,
        start_date=start,
        end_date=end,
        seed_start_date=seed_start,
        status=status,
        quantity=quantity,
    )


def _labels(weeks):
    return [[i["label"] for i in w["items"]] for w in weeks]


def test_weeks_run_monday_to_sunday():
    weeks = build_forecast([], TODAY, 2)
    assert weeks[0]["week_start"] == "2026-09-28"
    assert weeks[0]["week_end"] == "2026-10-04"
    assert weeks[1]["week_start"] == "2026-10-05"


def test_single_harvest_lands_in_end_date_week_and_sums_counts():
    cauli = _variety("Snowball Cauliflower", unit="head")
    plantings = [
        _planting(cauli, date(2026, 8, 1), date(2026, 10, 7), quantity=1),
        _planting(cauli, date(2026, 8, 1), date(2026, 10, 9), quantity=1),
    ]
    weeks = build_forecast(plantings, TODAY, 3)
    assert _labels(weeks) == [[], ["Snowball Cauliflower: 2 heads"], []]
    assert weeks[1]["items"][0]["count"] == 2


def test_count_falls_back_to_plants_per_square_then_planting():
    radish = _variety("Watermelon Radish", unit="radish", pps=9)
    onion = _variety("Evergreen", unit="onion")
    plantings = [
        _planting(radish, date(2026, 8, 1), date(2026, 10, 1)),
        _planting(onion, date(2026, 8, 1), date(2026, 10, 1)),
    ]
    assert _labels(build_forecast(plantings, TODAY, 1)) == [
        ["Evergreen: 1 planting", "Watermelon Radish: 9 radishes"]
    ]


def test_unit_and_count_inherit_from_category_unless_variety_overrides():
    carrot = _variety("Danvers", cat_unit="carrot", cat_pps=16)
    round_carrot = _variety("Paris Market", cat_unit="carrot", cat_pps=16, pps=9)
    plantings = [
        _planting(carrot, date(2026, 8, 1), date(2026, 10, 1)),
        _planting(round_carrot, date(2026, 8, 1), date(2026, 10, 1)),
    ]
    assert _labels(build_forecast(plantings, TODAY, 1)) == [["Danvers: 16 carrots", "Paris Market: 9 carrots"]]


def test_continuous_spans_harvest_start_through_end_date():
    pepper = _variety("Sweet Banana Pepper", harvest_type="continuous", dth=(70, 70))
    # Seed 2026-07-27 + 70 days → harvest from 2026-10-05 (week 1), end 2026-10-20 (week 3)
    p = _planting(pepper, date(2026, 8, 20), date(2026, 10, 20), seed_start=date(2026, 7, 27))
    assert _labels(build_forecast([p], TODAY, 5)) == [
        [],
        ["Sweet Banana Pepper: continuous (starts this week)"],
        ["Sweet Banana Pepper: continuous"],
        ["Sweet Banana Pepper: continuous (last week)"],
        [],
    ]


def test_variety_override_beats_category_and_none_is_excluded():
    head_lettuce = _variety("Buttercrunch", harvest_type="continuous", override="single", unit="head")
    marigold = _variety("Marigold", harvest_type="continuous", override="none")
    plantings = [
        _planting(head_lettuce, date(2026, 8, 1), date(2026, 10, 1), quantity=4),
        _planting(marigold, date(2026, 8, 1), date(2026, 10, 1)),
    ]
    assert _labels(build_forecast(plantings, TODAY, 1)) == [["Buttercrunch: 4 heads"]]


def test_overdue_in_progress_shows_in_first_week_only():
    cabbage = _variety("Copenhagen", unit="head")
    okra = _variety("Clemson", harvest_type="continuous")
    plantings = [
        _planting(cabbage, date(2026, 7, 1), date(2026, 9, 20), quantity=1),
        _planting(okra, date(2026, 5, 1), date(2026, 9, 1)),
        # A planned planting whose dates passed without going in is dropped
        _planting(cabbage, date(2026, 7, 1), date(2026, 9, 20), status="not_started", quantity=1),
    ]
    weeks = build_forecast(plantings, TODAY, 2)
    assert _labels(weeks) == [
        ["Copenhagen: 1 head (overdue)", "Clemson: continuous (past planned end)"],
        [],
    ]


def test_single_harvest_beyond_range_is_skipped():
    cabbage = _variety("Copenhagen", unit="head")
    p = _planting(cabbage, date(2026, 9, 1), date(2026, 12, 1), status="not_started", quantity=1)
    assert _labels(build_forecast([p], TODAY, 2)) == [[], []]


def test_pluralize():
    assert pluralize("head", 2) == "heads"
    assert pluralize("head", 1) == "head"
    assert pluralize("bunch", 3) == "bunches"
    assert pluralize("radish", 3) == "radishes"
    assert pluralize("berry", 3) == "berries"
