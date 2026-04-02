"""Recommendation engine — deterministic 'What can I plant here?' logic."""

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category, CompanionRule, PlantingSeason
from app.models.container import Container, SquareSupport
from app.models.planting import Planting
from app.models.variety import Variety


@dataclass
class RecommendationResult:
    """A single variety recommendation with scoring details."""

    variety_id: int
    variety_name: str
    category_id: int
    category_name: str
    category_color: str
    score: float = 0.0
    days_to_harvest_min: int | None = None
    days_to_harvest_max: int | None = None
    planting_method: str = "both"
    is_climbing: bool = False
    spacing: str = "1x1"
    warnings: list[str] = field(default_factory=list)
    boosts: list[str] = field(default_factory=list)


def _parse_spacing(spacing: str) -> tuple[int, int]:
    """Parse spacing string like '1x1' or '2x2' into (width, height)."""
    try:
        parts = spacing.lower().split("x")
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return 1, 1


def _date_in_season(
    check_date: date,
    start_month: int,
    start_day: int,
    end_month: int,
    end_day: int,
) -> bool:
    """Check if a date falls within a planting season window.

    Handles wrap-around seasons (e.g., Oct-Mar).
    """
    check_md = (check_date.month, check_date.day)
    start_md = (start_month, start_day)
    end_md = (end_month, end_day)

    if start_md <= end_md:
        # Normal season (e.g., Mar-Jun)
        return start_md <= check_md <= end_md
    else:
        # Wrap-around season (e.g., Oct-Mar)
        return check_md >= start_md or check_md <= end_md


def _days_remaining_in_season(
    check_date: date,
    end_month: int,
    end_day: int,
    start_month: int,
    start_day: int,
) -> int:
    """Estimate days remaining in the planting season from check_date."""
    year = check_date.year

    try:
        end_date = date(year, end_month, end_day)
    except ValueError:
        end_date = date(year, end_month, 28)

    if end_date < check_date:
        # Season wraps to next year
        try:
            end_date = date(year + 1, end_month, end_day)
        except ValueError:
            end_date = date(year + 1, end_month, 28)

    return (end_date - check_date).days


async def get_recommendations(
    db: AsyncSession,
    user_id: int,
    container_id: int,
    square_x: int,
    square_y: int,
    target_date: date,
    usda_zone: str = "10a",
) -> list[RecommendationResult]:
    """Get variety recommendations for a specific square on a given date.

    Filtering:
    1. Planting season check (is the date within the variety's planting window?)
    2. Time remaining (enough days for germination + growth?)
    3. Size compatibility (variety fits in available space?)

    Scoring:
    4. Companion planting (boost compatible neighbors, penalize incompatible)
    5. Support structure compatibility (boost climbing varieties if trellis present)
    """
    # Load container
    result = await db.execute(
        select(Container)
        .options(selectinload(Container.square_supports))
        .where(Container.id == container_id, Container.user_id == user_id)
    )
    container = result.scalar_one_or_none()
    if not container:
        return []

    # Load all user varieties with categories
    var_result = await db.execute(
        select(Variety)
        .options(selectinload(Variety.category).selectinload(Category.planting_seasons))
        .where(Variety.user_id == user_id)
    )
    varieties = var_result.scalars().all()

    # Load planting seasons for all categories
    season_result = await db.execute(
        select(PlantingSeason).where(PlantingSeason.usda_zone == usda_zone)
    )
    seasons_by_category: dict[int, list[PlantingSeason]] = {}
    for s in season_result.scalars().all():
        seasons_by_category.setdefault(s.category_id, []).append(s)

    # Load companion rules
    rule_result = await db.execute(select(CompanionRule))
    companion_rules = rule_result.scalars().all()
    rules_by_category: dict[int, list[CompanionRule]] = {}
    for r in companion_rules:
        rules_by_category.setdefault(r.category_id, []).append(r)

    # Load current plantings in this container (active on target_date)
    planting_result = await db.execute(
        select(Planting)
        .options(selectinload(Planting.variety))
        .where(
            Planting.container_id == container_id,
            Planting.user_id == user_id,
            Planting.start_date <= target_date,
            Planting.end_date > target_date,
        )
    )
    active_plantings = planting_result.scalars().all()

    # Get neighbor category IDs (adjacent squares)
    neighbor_category_ids: set[int] = set()
    for p in active_plantings:
        # Check if planting is adjacent to target square
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                adj_x, adj_y = square_x + dx, square_y + dy
                if (
                    p.square_x <= adj_x < p.square_x + p.square_width
                    and p.square_y <= adj_y < p.square_y + p.square_height
                ):
                    if p.variety:
                        neighbor_category_ids.add(p.variety.category_id)

    # Check support structure at target square
    support_at_square = None
    for s in container.square_supports:
        if s.square_x == square_x and s.square_y == square_y:
            support_at_square = s.support_type
            break

    # Available space from target square
    max_width = (container.width or 1) - square_x
    max_height = (container.height or 1) - square_y

    results: list[RecommendationResult] = []

    for variety in varieties:
        category = variety.category
        if not category:
            continue

        # --- Filter 1: Planting season ---
        # Check variety-level season override first, then category seasons
        in_season = False
        season_end_month = 0
        season_end_day = 0
        season_start_month = 0
        season_start_day = 0

        if (
            variety.season_override_start_month
            and variety.season_override_end_month
        ):
            in_season = _date_in_season(
                target_date,
                variety.season_override_start_month,
                variety.season_override_start_day or 1,
                variety.season_override_end_month,
                variety.season_override_end_day or 28,
            )
            season_end_month = variety.season_override_end_month
            season_end_day = variety.season_override_end_day or 28
            season_start_month = variety.season_override_start_month
            season_start_day = variety.season_override_start_day or 1
        else:
            cat_seasons = seasons_by_category.get(category.id, [])
            for season in cat_seasons:
                if _date_in_season(
                    target_date,
                    season.start_month,
                    season.start_day,
                    season.end_month,
                    season.end_day,
                ):
                    in_season = True
                    season_end_month = season.end_month
                    season_end_day = season.end_day
                    season_start_month = season.start_month
                    season_start_day = season.start_day
                    break

        if not in_season:
            continue

        # --- Filter 2: Time remaining ---
        days_remaining = _days_remaining_in_season(
            target_date, season_end_month, season_end_day,
            season_start_month, season_start_day,
        )
        min_days_needed = (variety.days_to_harvest_min or 60)
        if days_remaining < min_days_needed:
            continue

        # --- Filter 3: Size compatibility ---
        var_w, var_h = _parse_spacing(variety.spacing)
        if var_w > max_width or var_h > max_height:
            continue

        # --- Scoring ---
        rec = RecommendationResult(
            variety_id=variety.id,
            variety_name=variety.name,
            category_id=category.id,
            category_name=category.name,
            category_color=category.color,
            score=50.0,  # Base score
            days_to_harvest_min=variety.days_to_harvest_min,
            days_to_harvest_max=variety.days_to_harvest_max,
            planting_method=variety.planting_method,
            is_climbing=variety.is_climbing,
            spacing=variety.spacing,
        )

        # Score 4: Companion planting
        cat_rules = rules_by_category.get(category.id, [])
        for rule in cat_rules:
            if rule.companion_category_id in neighbor_category_ids:
                companion_cat = None
                for p in active_plantings:
                    if p.variety and p.variety.category_id == rule.companion_category_id:
                        companion_cat = p.variety.category
                        break
                companion_name = companion_cat.name if companion_cat else f"category {rule.companion_category_id}"

                if rule.relationship_type == "compatible":
                    rec.score += 20
                    rec.boosts.append(f"Good companion with nearby {companion_name}")
                elif rule.relationship_type == "incompatible":
                    rec.score -= 30
                    rec.warnings.append(f"Poor companion with nearby {companion_name}")

        # Score 5: Support structure compatibility
        if variety.is_climbing:
            if support_at_square in ("trellis", "pole", "cage"):
                rec.score += 15
                rec.boosts.append(f"Climbing variety matches {support_at_square} support")
            else:
                rec.score -= 10
                rec.warnings.append("Climbing variety — no support structure present")
        elif support_at_square:
            # Non-climbing variety with support — slight boost (can still use cage)
            rec.score += 5

        # Bonus for more days remaining (better timing)
        timing_bonus = min(10, (days_remaining - min_days_needed) / 10)
        rec.score += timing_bonus

        results.append(rec)

    # Sort by score descending
    results.sort(key=lambda r: r.score, reverse=True)
    return results
