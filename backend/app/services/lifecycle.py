"""Lifecycle phase computation for plantings.

Computes the current growth phase of an in-progress planting based on
the planting start date and the variety's growth timing data.

Phases:
  1. Germination: start_date → start_date + days_to_germination
  2. Growing: end of germination → start_date + days_to_harvest
  3. Harvesting: start_date + days_to_harvest → end_date
"""

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class LifecyclePhase:
    """Computed lifecycle phase for a planting."""

    phase: str  # "germination", "growing", "harvesting", "not_started", "complete"
    phase_display: str  # Human-readable label
    day_number: int  # Days since planting started
    total_days: int  # Total days in the planting period
    phase_start_date: date | None  # When this phase started
    phase_end_date: date | None  # When this phase ends
    phase_day: int  # Day within the current phase
    phase_total_days: int  # Total days in the current phase
    progress_percent: float  # Overall progress 0-100


def compute_lifecycle_phase(
    status: str,
    start_date: date,
    end_date: date,
    days_to_germination_min: int | None = None,
    days_to_germination_max: int | None = None,
    days_to_harvest_min: int | None = None,
    days_to_harvest_max: int | None = None,
    as_of: date | None = None,
) -> LifecyclePhase:
    """Compute the current lifecycle phase for a planting.

    Args:
        status: Planting status (not_started, in_progress, complete)
        start_date: When the planting was started
        end_date: When the planting ends/ended
        days_to_germination_min: Min days to germination from variety
        days_to_germination_max: Max days to germination from variety
        days_to_harvest_min: Min days to harvest from variety
        days_to_harvest_max: Max days to harvest from variety
        as_of: Date to compute phase for (defaults to today)

    Returns:
        LifecyclePhase with computed phase information
    """
    if as_of is None:
        as_of = date.today()

    total_days = max((end_date - start_date).days, 1)

    if status == "not_started":
        return LifecyclePhase(
            phase="not_started",
            phase_display="Planned",
            day_number=0,
            total_days=total_days,
            phase_start_date=None,
            phase_end_date=start_date,
            phase_day=0,
            phase_total_days=0,
            progress_percent=0.0,
        )

    if status == "complete":
        return LifecyclePhase(
            phase="complete",
            phase_display="Complete",
            day_number=total_days,
            total_days=total_days,
            phase_start_date=None,
            phase_end_date=None,
            phase_day=0,
            phase_total_days=0,
            progress_percent=100.0,
        )

    # Status is in_progress — compute phase from dates
    day_number = (as_of - start_date).days
    progress_percent = min(max((day_number / total_days) * 100, 0), 100)

    # Use average of min/max for germination and harvest timing
    germ_days = _avg_days(days_to_germination_min, days_to_germination_max, default=7)
    harvest_days = _avg_days(days_to_harvest_min, days_to_harvest_max, default=60)

    # Phase boundaries
    germ_end_date = start_date + timedelta(days=germ_days)
    harvest_start_date = start_date + timedelta(days=harvest_days)

    if as_of < germ_end_date:
        # Germination phase
        phase_total = germ_days
        phase_day = day_number
        return LifecyclePhase(
            phase="germination",
            phase_display=f"Germination — Day {max(day_number, 0) + 1}",
            day_number=day_number,
            total_days=total_days,
            phase_start_date=start_date,
            phase_end_date=germ_end_date,
            phase_day=max(phase_day, 0),
            phase_total_days=phase_total,
            progress_percent=progress_percent,
        )
    elif as_of < harvest_start_date:
        # Growing phase
        phase_total = (harvest_start_date - germ_end_date).days
        phase_day = (as_of - germ_end_date).days
        return LifecyclePhase(
            phase="growing",
            phase_display=f"Growing — Day {day_number + 1}",
            day_number=day_number,
            total_days=total_days,
            phase_start_date=germ_end_date,
            phase_end_date=harvest_start_date,
            phase_day=phase_day,
            phase_total_days=max(phase_total, 1),
            progress_percent=progress_percent,
        )
    else:
        # Harvesting phase
        phase_total = (end_date - harvest_start_date).days
        phase_day = (as_of - harvest_start_date).days
        return LifecyclePhase(
            phase="harvesting",
            phase_display=f"Harvesting — Day {day_number + 1}",
            day_number=day_number,
            total_days=total_days,
            phase_start_date=harvest_start_date,
            phase_end_date=end_date,
            phase_day=phase_day,
            phase_total_days=max(phase_total, 1),
            progress_percent=progress_percent,
        )


def _avg_days(min_val: int | None, max_val: int | None, default: int) -> int:
    """Compute average of min/max, falling back to default."""
    if min_val is not None and max_val is not None:
        return (min_val + max_val) // 2
    if min_val is not None:
        return min_val
    if max_val is not None:
        return max_val
    return default
