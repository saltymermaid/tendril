"""Seed data script for Tendril development database.

Run with: docker compose exec backend python -m scripts.seed_data
"""

import asyncio
from datetime import date, timedelta

from app.database import async_session
from app.models import (
    Category,
    CompanionRule,
    Container,
    Event,
    JournalNote,
    Planting,
    PlantingSeason,
    SquareSupport,
    User,
    Variety,
)


def _emoji_svg(emoji: str) -> str:
    """Wrap an emoji in a minimal SVG for use as a category icon."""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><text y="28" font-size="28">{emoji}</text></svg>'


# ─── Categories ───────────────────────────────────────────────────────────────
CATEGORIES = [
    {"name": "Tomatoes", "color": "#E53E3E", "harvest_type": "continuous", "icon_svg": _emoji_svg("🍅")},
    {"name": "Peppers", "color": "#DD6B20", "harvest_type": "continuous", "icon_svg": _emoji_svg("🌶️")},
    {"name": "Cucumbers", "color": "#38A169", "harvest_type": "continuous", "icon_svg": _emoji_svg("🥒")},
    {"name": "Squash", "color": "#D69E2E", "harvest_type": "continuous", "icon_svg": _emoji_svg("🎃")},
    {"name": "Beans", "color": "#276749", "harvest_type": "continuous", "icon_svg": _emoji_svg("🫘")},
    {"name": "Sweet Potatoes", "color": "#C05621", "harvest_type": "single", "icon_svg": _emoji_svg("🍠")},
    {"name": "Bunching Onions", "color": "#9F7AEA", "harvest_type": "single", "icon_svg": _emoji_svg("🧅")},
    {"name": "Peas", "color": "#48BB78", "harvest_type": "continuous", "icon_svg": _emoji_svg("🫛")},
    {"name": "Lettuce", "color": "#68D391", "harvest_type": "continuous", "icon_svg": _emoji_svg("🥬")},
    {"name": "Kale", "color": "#2F855A", "harvest_type": "continuous", "icon_svg": _emoji_svg("🥗")},
    {"name": "Spinach", "color": "#22543D", "harvest_type": "continuous", "icon_svg": _emoji_svg("🍃")},
    {"name": "Cabbage", "color": "#4FD1C5", "harvest_type": "single", "icon_svg": _emoji_svg("🥬")},
    {"name": "Melons", "color": "#F6AD55", "harvest_type": "single", "icon_svg": _emoji_svg("🍈")},
    {"name": "Radishes", "color": "#FC8181", "harvest_type": "single", "icon_svg": _emoji_svg("🔴")},
    {"name": "Herbs", "color": "#9AE6B4", "harvest_type": "continuous", "icon_svg": _emoji_svg("🌿")},
    {"name": "Flowers", "color": "#F687B3", "harvest_type": "continuous", "icon_svg": _emoji_svg("🌸")},
]

# ─── Planting Seasons for Zone 10a ───────────────────────────────────────────
PLANTING_SEASONS_10A = [
    ("Tomatoes", 8, 15, 3, 15),
    ("Peppers", 8, 15, 3, 15),
    ("Cucumbers", 9, 1, 3, 1),
    ("Squash", 8, 15, 3, 15),
    ("Beans", 9, 1, 4, 1),
    ("Sweet Potatoes", 3, 1, 6, 30),
    ("Bunching Onions", 9, 1, 2, 28),
    ("Peas", 10, 1, 2, 28),
    ("Lettuce", 10, 1, 2, 28),
    ("Kale", 10, 1, 2, 28),
    ("Spinach", 10, 1, 2, 28),
    ("Cabbage", 9, 15, 1, 31),
    ("Melons", 2, 1, 4, 15),
    ("Radishes", 10, 1, 3, 1),
    ("Herbs", 1, 1, 12, 31),
    ("Flowers", 9, 1, 4, 30),
]

# ─── Companion Planting Matrix ───────────────────────────────────────────────
COMPANION_RULES = [
    ("Tomatoes", "Peppers", "compatible"),
    ("Tomatoes", "Herbs", "compatible"),
    ("Tomatoes", "Flowers", "compatible"),
    ("Tomatoes", "Beans", "incompatible"),
    ("Tomatoes", "Cabbage", "incompatible"),
    ("Tomatoes", "Cucumbers", "compatible"),
    ("Tomatoes", "Radishes", "compatible"),
    ("Peppers", "Herbs", "compatible"),
    ("Peppers", "Beans", "compatible"),
    ("Peppers", "Spinach", "compatible"),
    ("Cucumbers", "Beans", "compatible"),
    ("Cucumbers", "Peas", "compatible"),
    ("Cucumbers", "Radishes", "compatible"),
    ("Cucumbers", "Lettuce", "compatible"),
    ("Cucumbers", "Herbs", "compatible"),
    ("Cucumbers", "Melons", "incompatible"),
    ("Squash", "Beans", "compatible"),
    ("Squash", "Radishes", "compatible"),
    ("Squash", "Flowers", "compatible"),
    ("Squash", "Herbs", "compatible"),
    ("Beans", "Radishes", "compatible"),
    ("Beans", "Lettuce", "compatible"),
    ("Beans", "Peas", "compatible"),
    ("Beans", "Bunching Onions", "incompatible"),
    ("Sweet Potatoes", "Beans", "compatible"),
    ("Sweet Potatoes", "Radishes", "compatible"),
    ("Bunching Onions", "Tomatoes", "compatible"),
    ("Bunching Onions", "Peppers", "compatible"),
    ("Bunching Onions", "Lettuce", "compatible"),
    ("Bunching Onions", "Cabbage", "compatible"),
    ("Bunching Onions", "Peas", "incompatible"),
    ("Peas", "Radishes", "compatible"),
    ("Peas", "Lettuce", "compatible"),
    ("Lettuce", "Radishes", "compatible"),
    ("Lettuce", "Herbs", "compatible"),
    ("Kale", "Herbs", "compatible"),
    ("Kale", "Bunching Onions", "compatible"),
    ("Kale", "Radishes", "compatible"),
    ("Spinach", "Radishes", "compatible"),
    ("Spinach", "Beans", "compatible"),
    ("Spinach", "Peas", "compatible"),
    ("Cabbage", "Herbs", "compatible"),
    ("Cabbage", "Tomatoes", "incompatible"),
    ("Melons", "Flowers", "compatible"),
    ("Melons", "Radishes", "compatible"),
    ("Herbs", "Lettuce", "compatible"),
    ("Flowers", "Squash", "compatible"),
    ("Flowers", "Melons", "compatible"),
    ("Flowers", "Peppers", "compatible"),
    ("Flowers", "Beans", "compatible"),
]

# ─── Varieties ────────────────────────────────────────────────────────────────
VARIETIES = [
    ("Tomatoes", "Golden Jubilee", 7, 14, 72, 80, "2x2", False, "transplant", "1/4 inch", "full_sun", None),
    ("Tomatoes", "Husky Cherry Red", 7, 14, 65, 70, "1x1", False, "transplant", "1/4 inch", "full_sun", "Compact determinate"),
    ("Tomatoes", "Everglades", 7, 14, 60, 70, "2x2", False, "both", "1/4 inch", "full_sun", "Heat tolerant, Florida native"),
    ("Peppers", "Jalapeño", 10, 14, 70, 80, "1x1", False, "transplant", "1/4 inch", "full_sun", None),
    ("Peppers", "Cubanelle", 10, 14, 65, 75, "1x1", False, "transplant", "1/4 inch", "full_sun", None),
    ("Peppers", "Orange Sweet", 10, 14, 75, 85, "1x1", False, "transplant", "1/4 inch", "full_sun", None),
    ("Peppers", "Poblano", 10, 14, 70, 80, "1x1", False, "transplant", "1/4 inch", "full_sun", None),
    ("Cucumbers", "Garden Bush Slicer", 7, 10, 55, 65, "1x2", False, "direct_sow", "1 inch", "full_sun", None),
    ("Cucumbers", "Double Yield Pickling", 7, 10, 50, 60, "1x2", True, "direct_sow", "1 inch", "full_sun", None),
    ("Squash", "Crookneck", 7, 10, 50, 60, "2x2", False, "direct_sow", "1 inch", "full_sun", None),
    ("Squash", "Easy Pick Gold Zucchini", 7, 10, 45, 55, "2x2", False, "direct_sow", "1 inch", "full_sun", None),
    ("Squash", "Summer Golden Zucchini", 7, 10, 50, 60, "2x2", False, "direct_sow", "1 inch", "full_sun", "Future variety"),
    ("Squash", "Pumpkin Spookie", 7, 10, 90, 110, "2x2", True, "direct_sow", "1 inch", "full_sun", "Future variety"),
    ("Squash", "Seminole Pumpkin", 7, 10, 90, 100, "2x2", True, "direct_sow", "1 inch", "full_sun", "Future variety"),
    ("Beans", "Royal Burgundy Bush", 7, 10, 50, 60, "1x1", False, "direct_sow", "1 inch", "full_sun", None),
    ("Beans", "Bush Cantare", 7, 10, 50, 55, "1x1", False, "direct_sow", "1 inch", "full_sun", None),
    ("Beans", "Blue Lake Bush", 7, 10, 55, 60, "1x1", False, "direct_sow", "1 inch", "full_sun", None),
    ("Beans", "Pole Blue Lake", 7, 10, 60, 70, "1x1", True, "direct_sow", "1 inch", "full_sun", "Future variety"),
    ("Sweet Potatoes", "Beauregard", None, None, 90, 120, "2x2", False, "transplant", "slips", "full_sun", "Plant from slips"),
    ("Bunching Onions", "Evergreen", 10, 14, 60, 70, "1x1", False, "direct_sow", "1/4 inch", "full_sun", None),
    ("Bunching Onions", "Red Beard", 10, 14, 60, 70, "1x1", False, "direct_sow", "1/4 inch", "full_sun", None),
    ("Bunching Onions", "Warrior", 10, 14, 60, 70, "1x1", False, "direct_sow", "1/4 inch", "full_sun", None),
    ("Peas", "Snap Patio Pride", 7, 10, 55, 65, "1x1", True, "direct_sow", "1 inch", "full_sun", "Future variety"),
    ("Cabbage", "Dwarf Pak Choi", 5, 10, 45, 55, "1x1", False, "both", "1/4 inch", "partial_shade", "Future variety"),
    ("Melons", "Honey Rock Cantaloupe", 7, 10, 80, 90, "2x2", True, "direct_sow", "1 inch", "full_sun", "Future variety"),
    ("Radishes", "Watermelon Radish", 5, 7, 55, 65, "1x1", False, "direct_sow", "1/2 inch", "full_sun", None),
    ("Herbs", "Rosemary", 14, 21, 80, 90, "1x1", False, "transplant", "surface", "full_sun", "Perennial in 10a"),
    ("Herbs", "English Thyme", 14, 21, 70, 80, "1x1", False, "transplant", "surface", "full_sun", "Perennial in 10a"),
    ("Herbs", "French Thyme", 14, 21, 70, 80, "1x1", False, "transplant", "surface", "full_sun", "Future variety"),
    ("Herbs", "Slow-Bolt Cilantro", 7, 10, 45, 55, "1x1", False, "direct_sow", "1/4 inch", "partial_shade", None),
    ("Herbs", "Bouquet Dill", 10, 14, 60, 70, "1x1", False, "direct_sow", "1/4 inch", "full_sun", None),
    ("Herbs", "Mammoth Dill", 10, 14, 65, 75, "1x1", False, "direct_sow", "1/4 inch", "full_sun", "Future variety"),
    ("Herbs", "Italian Large Leaf Basil", 7, 10, 50, 60, "1x1", False, "both", "1/4 inch", "full_sun", None),
    ("Herbs", "Common Chives", 14, 21, 75, 90, "1x1", False, "transplant", "1/4 inch", "full_sun", "Perennial"),
    ("Flowers", "Naughty Marietta Marigold", 5, 7, 50, 60, "1x1", False, "direct_sow", "1/4 inch", "full_sun", "Great companion"),
    ("Flowers", "French Red Cherry Marigold", 5, 7, 50, 60, "1x1", False, "direct_sow", "1/4 inch", "full_sun", "Great companion"),
    ("Flowers", "Roselle", 10, 14, 120, 150, "2x2", False, "direct_sow", "1/4 inch", "full_sun", "Future variety"),
]

# ─── Containers ───────────────────────────────────────────────────────────────
CONTAINERS = [
    {"name": "Bed 1", "type": "grid_bed", "location_description": "Back yard, south side",
     "width": 4, "height": 4, "irrigation_type": "drip", "irrigation_duration_minutes": 30, "irrigation_frequency": "daily"},
    {"name": "Bed 2", "type": "grid_bed", "location_description": "Back yard, center",
     "width": 4, "height": 4, "irrigation_type": "drip", "irrigation_duration_minutes": 30, "irrigation_frequency": "daily"},
    {"name": "Bed 3", "type": "grid_bed", "location_description": "Back yard, north side",
     "width": 4, "height": 4, "irrigation_type": "drip", "irrigation_duration_minutes": 30, "irrigation_frequency": "daily"},
    {"name": "Mobile Bed", "type": "grid_bed", "location_description": "Patio, movable",
     "width": 2, "height": 4, "irrigation_type": "manual", "irrigation_duration_minutes": 10, "irrigation_frequency": "daily"},
    {"name": "Tower", "type": "tower", "location_description": "Patio, near kitchen door",
     "levels": 7, "pockets_per_level": 6, "irrigation_type": "drip", "irrigation_duration_minutes": 15, "irrigation_frequency": "2x_daily"},
]

SUPPORT_STRUCTURES = [
    ("Bed 1", 0, 3, "trellis"), ("Bed 1", 1, 3, "trellis"),
    ("Bed 1", 2, 3, "trellis"), ("Bed 1", 3, 3, "trellis"),
    ("Bed 2", 1, 1, "cage"), ("Bed 2", 2, 2, "cage"),
    ("Bed 3", 0, 3, "trellis"), ("Bed 3", 1, 3, "trellis"),
]


async def seed_database():
    """Seed the database with reference data and sample data."""
    async with async_session() as session:
        # ── 1. Create dev user ────────────────────────────────────────────
        user = User(
            email="dev@tendril.garden",
            name="Dev User",
            settings={
                "usda_zone": "10a",
                "weather_lat": 27.7676,
                "weather_lon": -82.6403,
                "weather_zip_code": "33701",
            },
        )
        session.add(user)
        await session.flush()
        print(f"  Created user: {user.email} (id={user.id})")

        # ── 2. Create categories ──────────────────────────────────────────
        cat_map: dict[str, Category] = {}
        for cat_data in CATEGORIES:
            cat = Category(**cat_data)
            session.add(cat)
            await session.flush()
            cat_map[cat.name] = cat
        print(f"  Created {len(cat_map)} categories")

        # ── 3. Create planting seasons ────────────────────────────────────
        count = 0
        for cat_name, sm, sd, em, ed in PLANTING_SEASONS_10A:
            session.add(PlantingSeason(
                category_id=cat_map[cat_name].id, usda_zone="10a",
                start_month=sm, start_day=sd, end_month=em, end_day=ed,
            ))
            count += 1
        await session.flush()
        print(f"  Created {count} planting seasons for Zone 10a")

        # ── 4. Create companion rules ─────────────────────────────────────
        count = 0
        for cat_name, comp_name, rel_type in COMPANION_RULES:
            session.add(CompanionRule(
                category_id=cat_map[cat_name].id,
                companion_category_id=cat_map[comp_name].id,
                relationship_type=rel_type,
            ))
            count += 1
        await session.flush()
        print(f"  Created {count} companion planting rules")

        # ── 5. Create varieties ───────────────────────────────────────────
        var_map: dict[str, Variety] = {}
        for v in VARIETIES:
            cat_name, name, dg_min, dg_max, dh_min, dh_max, spacing, climbing, method, depth, sun, notes = v
            variety = Variety(
                user_id=user.id, category_id=cat_map[cat_name].id, name=name,
                days_to_germination_min=dg_min, days_to_germination_max=dg_max,
                days_to_harvest_min=dh_min, days_to_harvest_max=dh_max,
                spacing=spacing, is_climbing=climbing, planting_method=method,
                planting_depth=depth, sunlight=sun, notes=notes,
            )
            session.add(variety)
            await session.flush()
            var_map[name] = variety
        print(f"  Created {len(var_map)} varieties")

        # ── 6. Create containers ──────────────────────────────────────────
        cont_map: dict[str, Container] = {}
        for c_data in CONTAINERS:
            container = Container(user_id=user.id, **c_data)
            session.add(container)
            await session.flush()
            cont_map[container.name] = container
        print(f"  Created {len(cont_map)} containers")

        # ── 7. Create support structures ──────────────────────────────────
        count = 0
        for cont_name, sx, sy, stype in SUPPORT_STRUCTURES:
            session.add(SquareSupport(
                container_id=cont_map[cont_name].id,
                square_x=sx, square_y=sy, support_type=stype,
            ))
            count += 1
        await session.flush()
        print(f"  Created {count} support structures")

        # ── 8. Create sample plantings ────────────────────────────────────
        today = date.today()
        planting_map: dict[str, Planting] = {}

        plantings_data = [
            # In Progress — Bed 1
            ("p1", "Bed 1", "Golden Jubilee", 0, 0, 2, 2, -30, 50, "in_progress", "transplant", 1),
            ("p2", "Bed 1", "Jalapeño", 2, 0, 1, 1, -25, 55, "in_progress", "transplant", 1),
            ("p3", "Bed 1", "Cubanelle", 3, 0, 1, 1, -25, 55, "in_progress", "transplant", 1),
            ("p4", "Bed 1", "Double Yield Pickling", 0, 3, 2, 1, -20, 40, "in_progress", "direct_sow", 4),
            # In Progress — Bed 2
            ("p5", "Bed 2", "Orange Sweet", 0, 0, 1, 1, -35, 50, "in_progress", "transplant", 1),
            ("p6", "Bed 2", "Poblano", 1, 0, 1, 1, -35, 50, "in_progress", "transplant", 1),
            ("p7", "Bed 2", "Italian Large Leaf Basil", 2, 0, 1, 1, -20, 40, "in_progress", "transplant", 3),
            ("p8", "Bed 2", "Naughty Marietta Marigold", 3, 0, 1, 1, -40, 20, "in_progress", "direct_sow", 4),
            # In Progress — Bed 3
            ("p9", "Bed 3", "Royal Burgundy Bush", 0, 0, 1, 1, -15, 45, "in_progress", "direct_sow", 9),
            ("p10", "Bed 3", "Bush Cantare", 1, 0, 1, 1, -15, 45, "in_progress", "direct_sow", 9),
            ("p11", "Bed 3", "Evergreen", 2, 0, 1, 1, -40, 30, "in_progress", "direct_sow", 16),
            # In Progress — Mobile Bed (herbs)
            ("p12", "Mobile Bed", "Rosemary", 0, 0, 1, 1, -60, 300, "in_progress", "transplant", 1),
            ("p13", "Mobile Bed", "English Thyme", 1, 0, 1, 1, -60, 300, "in_progress", "transplant", 1),
            ("p14", "Mobile Bed", "Slow-Bolt Cilantro", 0, 1, 1, 1, -14, 40, "in_progress", "direct_sow", 6),
            # In Progress — Tower
            ("p15", "Tower", "Husky Cherry Red", 0, 0, 1, 1, -30, 40, "in_progress", "transplant", 1),
            # Not Started — planned future plantings
            ("p16", "Bed 3", "Watermelon Radish", 3, 0, 1, 1, 7, 70, "not_started", "direct_sow", 9),
            ("p17", "Bed 2", "Bouquet Dill", 0, 1, 1, 1, 14, 80, "not_started", "direct_sow", 4),
            ("p18", "Bed 1", "Blue Lake Bush", 2, 1, 1, 1, 10, 70, "not_started", "direct_sow", 9),
            # Complete — historical plantings
            ("p19", "Bed 3", "Warrior", 3, 1, 1, 1, -90, -10, "complete", "direct_sow", 16),
            ("p20", "Bed 2", "French Red Cherry Marigold", 3, 1, 1, 1, -100, -5, "complete", "direct_sow", 4),
        ]

        for key, cont_name, var_name, x, y, w, h, start_off, end_off, status, method, qty in plantings_data:
            p = Planting(
                user_id=user.id,
                container_id=cont_map[cont_name].id,
                variety_id=var_map[var_name].id,
                square_x=x, square_y=y, square_width=w, square_height=h,
                tower_level=1 if cont_map[cont_name].type == "tower" else None,
                start_date=today + timedelta(days=start_off),
                end_date=today + timedelta(days=end_off),
                status=status,
                planting_method=method,
                quantity=qty,
                removal_reason="harvest_complete" if status == "complete" else None,
            )
            session.add(p)
            await session.flush()
            planting_map[key] = p

        print(f"  Created {len(planting_map)} plantings")

        # ── 9. Create sample events ──────────────────────────────────────
        event_count = 0
        # Planting events for in-progress plantings
        for key in ["p1", "p2", "p3", "p4", "p5", "p6", "p9", "p10", "p11", "p12", "p13", "p14", "p15"]:
            p = planting_map[key]
            session.add(Event(
                user_id=user.id,
                container_id=p.container_id,
                planting_id=p.id,
                variety_id=p.variety_id,
                event_type="planting",
                date=p.start_date,
                quantity=p.quantity,
                square_x=p.square_x,
                square_y=p.square_y,
                tower_level=p.tower_level,
                notes=f"Planted {p.quantity} via {p.planting_method}",
            ))
            event_count += 1

        # Harvest events for completed plantings
        for key in ["p19", "p20"]:
            p = planting_map[key]
            session.add(Event(
                user_id=user.id,
                container_id=p.container_id,
                planting_id=p.id,
                variety_id=p.variety_id,
                event_type="harvest",
                date=p.end_date,
                quantity=2,
                unit="bunches" if key == "p19" else "count",
                square_x=p.square_x,
                square_y=p.square_y,
                notes="Final harvest before removal",
            ))
            event_count += 1

        await session.flush()
        print(f"  Created {event_count} events")

        # ── 10. Create sample journal notes ──────────────────────────────
        note_count = 0
        session.add(JournalNote(
            user_id=user.id,
            container_id=cont_map["Bed 1"].id,
            content="Tomatoes looking healthy, good new growth this week. Staked the Golden Jubilee.",
            date=today - timedelta(days=5),
        ))
        note_count += 1

        session.add(JournalNote(
            user_id=user.id,
            container_id=cont_map["Bed 3"].id,
            planting_id=planting_map["p11"].id,
            variety_id=var_map["Evergreen"].id,
            square_x=2, square_y=0,
            content="Onions are starting to thicken up nicely. Should be ready to harvest in a few weeks.",
            date=today - timedelta(days=3),
        ))
        note_count += 1

        await session.flush()
        print(f"  Created {note_count} journal notes")

        await session.commit()
        print("\nSeed data complete!")


async def main():
    """Run the seed script."""
    print("Seeding Tendril database...")
    await seed_database()


if __name__ == "__main__":
    asyncio.run(main())
