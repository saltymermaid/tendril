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
    {"name": "Tomatoes",        "color": "#E53E3E", "harvest_type": "continuous", "icon_svg": _emoji_svg("🍅")},
    {"name": "Peppers",         "color": "#DD6B20", "harvest_type": "continuous", "icon_svg": _emoji_svg("🌶️")},
    {"name": "Cucumbers",       "color": "#38A169", "harvest_type": "continuous", "icon_svg": _emoji_svg("🥒")},
    {"name": "Squash",          "color": "#D69E2E", "harvest_type": "continuous", "icon_svg": _emoji_svg("🎃")},
    {"name": "Beans",           "color": "#276749", "harvest_type": "continuous", "icon_svg": _emoji_svg("🫘")},
    {"name": "Sweet Potatoes",  "color": "#C05621", "harvest_type": "single",     "icon_svg": _emoji_svg("🍠")},
    {"name": "Bunching Onions", "color": "#9F7AEA", "harvest_type": "single",     "icon_svg": _emoji_svg("🧅")},
    {"name": "Peas",            "color": "#48BB78", "harvest_type": "continuous", "icon_svg": _emoji_svg("🫛")},
    {"name": "Lettuce",         "color": "#68D391", "harvest_type": "continuous", "icon_svg": _emoji_svg("🥬")},
    {"name": "Kale",            "color": "#2F855A", "harvest_type": "continuous", "icon_svg": _emoji_svg("🥗")},
    {"name": "Spinach",         "color": "#22543D", "harvest_type": "continuous", "icon_svg": _emoji_svg("🍃")},
    {"name": "Cabbage",         "color": "#4FD1C5", "harvest_type": "single",     "icon_svg": _emoji_svg("🥬")},
    {"name": "Melons",          "color": "#F6AD55", "harvest_type": "single",     "icon_svg": _emoji_svg("🍈")},
    {"name": "Radishes",        "color": "#FC8181", "harvest_type": "single",     "icon_svg": _emoji_svg("🔴")},
    {"name": "Herbs",           "color": "#9AE6B4", "harvest_type": "continuous", "icon_svg": _emoji_svg("🌿")},
    {"name": "Flowers",         "color": "#F687B3", "harvest_type": "continuous", "icon_svg": _emoji_svg("🌸")},
    {"name": "Okra",            "color": "#68B984", "harvest_type": "continuous", "icon_svg": _emoji_svg("🌱")},
    {"name": "Eggplant",        "color": "#805AD5", "harvest_type": "continuous", "icon_svg": _emoji_svg("🍆")},
]

# ─── Planting Seasons for Zone 10a ───────────────────────────────────────────
PLANTING_SEASONS_10A = [
    ("Tomatoes",        8, 15, 3, 15),
    ("Peppers",         8, 15, 3, 15),
    ("Cucumbers",       9,  1, 3,  1),
    ("Squash",          8, 15, 3, 15),
    ("Beans",           9,  1, 4,  1),
    ("Sweet Potatoes",  3,  1, 6, 30),
    ("Bunching Onions", 9,  1, 2, 28),
    ("Peas",           10,  1, 2, 28),
    ("Lettuce",        10,  1, 2, 28),
    ("Kale",           10,  1, 2, 28),
    ("Spinach",        10,  1, 2, 28),
    ("Cabbage",         9, 15, 1, 31),
    ("Melons",          2,  1, 4, 15),
    ("Radishes",       10,  1, 3,  1),
    ("Herbs",           1,  1, 12, 31),
    ("Flowers",         9,  1, 4, 30),
    ("Okra",            3,  1, 7, 31),
    ("Eggplant",        2,  1, 5, 31),
]

# ─── Companion Planting Matrix ───────────────────────────────────────────────
COMPANION_RULES = [
    ("Tomatoes",  "Peppers",         "compatible"),
    ("Tomatoes",  "Herbs",           "compatible"),
    ("Tomatoes",  "Flowers",         "compatible"),
    ("Tomatoes",  "Beans",           "incompatible"),
    ("Tomatoes",  "Cabbage",         "incompatible"),
    ("Tomatoes",  "Cucumbers",       "compatible"),
    ("Tomatoes",  "Radishes",        "compatible"),
    ("Peppers",   "Herbs",           "compatible"),
    ("Peppers",   "Beans",           "compatible"),
    ("Peppers",   "Spinach",         "compatible"),
    ("Cucumbers", "Beans",           "compatible"),
    ("Cucumbers", "Peas",            "compatible"),
    ("Cucumbers", "Radishes",        "compatible"),
    ("Cucumbers", "Lettuce",         "compatible"),
    ("Cucumbers", "Herbs",           "compatible"),
    ("Cucumbers", "Melons",          "incompatible"),
    ("Squash",    "Beans",           "compatible"),
    ("Squash",    "Radishes",        "compatible"),
    ("Squash",    "Flowers",         "compatible"),
    ("Squash",    "Herbs",           "compatible"),
    ("Beans",     "Radishes",        "compatible"),
    ("Beans",     "Lettuce",         "compatible"),
    ("Beans",     "Peas",            "compatible"),
    ("Beans",     "Bunching Onions", "incompatible"),
    ("Sweet Potatoes", "Beans",      "compatible"),
    ("Sweet Potatoes", "Radishes",   "compatible"),
    ("Bunching Onions", "Tomatoes",  "compatible"),
    ("Bunching Onions", "Peppers",   "compatible"),
    ("Bunching Onions", "Lettuce",   "compatible"),
    ("Bunching Onions", "Cabbage",   "compatible"),
    ("Bunching Onions", "Peas",      "incompatible"),
    ("Peas",      "Radishes",        "compatible"),
    ("Peas",      "Lettuce",         "compatible"),
    ("Lettuce",   "Radishes",        "compatible"),
    ("Lettuce",   "Herbs",           "compatible"),
    ("Kale",      "Herbs",           "compatible"),
    ("Kale",      "Bunching Onions", "compatible"),
    ("Kale",      "Radishes",        "compatible"),
    ("Spinach",   "Radishes",        "compatible"),
    ("Spinach",   "Beans",           "compatible"),
    ("Spinach",   "Peas",            "compatible"),
    ("Cabbage",   "Herbs",           "compatible"),
    ("Cabbage",   "Tomatoes",        "incompatible"),
    ("Melons",    "Flowers",         "compatible"),
    ("Melons",    "Radishes",        "compatible"),
    ("Herbs",     "Lettuce",         "compatible"),
    ("Flowers",   "Squash",          "compatible"),
    ("Flowers",   "Melons",          "compatible"),
    ("Flowers",   "Peppers",         "compatible"),
    ("Flowers",   "Beans",           "compatible"),
    ("Okra",      "Flowers",         "compatible"),
    ("Okra",      "Herbs",           "compatible"),
    ("Okra",      "Peppers",         "compatible"),
    ("Eggplant",  "Herbs",           "compatible"),
    ("Eggplant",  "Beans",           "compatible"),
    ("Eggplant",  "Peppers",         "compatible"),
]

# ─── Varieties ────────────────────────────────────────────────────────────────
# (category, name, germ_min, germ_max, harvest_min, harvest_max, spacing,
#  is_climbing, planting_method, depth, sunlight, notes)
VARIETIES = [
    # Tomatoes
    ("Tomatoes", "Golden Jubilee",               7, 14,  72,  80, "2x2", False, "transplant",  "1/4 inch", "full_sun", None),
    ("Tomatoes", "Husky Cherry Red",              7, 14,  65,  70, "1x1", False, "transplant",  "1/4 inch", "full_sun", "Compact determinate"),
    ("Tomatoes", "Everglades",                    7, 14,  60,  70, "2x2", False, "both",        "1/4 inch", "full_sun", "Heat tolerant, Florida native"),
    ("Tomatoes", "White Everglades Tomato",       7, 14,  60,  75, "1x1", False, "transplant",  "1/4 inch", "full_sun", "White fruited Everglades type, heat tolerant"),
    ("Tomatoes", "Red Everglades Tomato",         7, 14,  60,  75, "1x1", False, "transplant",  "1/4 inch", "full_sun", "Red fruited Everglades type, heat tolerant"),
    # Peppers
    ("Peppers",  "Jalapeño",                     10, 14,  70,  80, "1x1", False, "transplant",  "1/4 inch", "full_sun", None),
    ("Peppers",  "Cubanelle",                    10, 14,  65,  75, "1x1", False, "transplant",  "1/4 inch", "full_sun", None),
    ("Peppers",  "Orange Sweet",                 10, 14,  75,  85, "1x1", False, "transplant",  "1/4 inch", "full_sun", None),
    ("Peppers",  "Poblano",                      10, 14,  70,  80, "1x1", False, "transplant",  "1/4 inch", "full_sun", None),
    ("Peppers",  "Sweet Banana Pepper",          10, 14,  65,  75, "1x1", False, "transplant",  "1/4 inch", "full_sun", "Stake for support"),
    # Cucumbers
    ("Cucumbers","Garden Bush Slicer",            7, 10,  55,  65, "1x2", False, "direct_sow",  "1 inch",   "full_sun", None),
    ("Cucumbers","Double Yield Pickling",         7, 10,  50,  60, "1x2", True,  "direct_sow",  "1 inch",   "full_sun", None),
    # Squash
    ("Squash",   "Crookneck",                    7, 10,  50,  60, "2x2", False, "direct_sow",  "1 inch",   "full_sun", None),
    ("Squash",   "Easy Pick Gold Zucchini",      7, 10,  45,  55, "2x2", False, "direct_sow",  "1 inch",   "full_sun", None),
    ("Squash",   "Summer Golden Zucchini",       7, 10,  50,  60, "2x2", False, "direct_sow",  "1 inch",   "full_sun", "Future variety"),
    ("Squash",   "Pumpkin Spookie",              7, 10,  90, 110, "2x2", True,  "direct_sow",  "1 inch",   "full_sun", "Future variety"),
    ("Squash",   "Seminole Pumpkin",             7, 10,  90, 100, "1x1", True,  "direct_sow",  "1 inch",   "full_sun", "Vining; trellis required"),
    ("Squash",   "Loofah",                       7, 14,  90, 120, "1x1", True,  "direct_sow",  "1 inch",   "full_sun", "Vining; trellis required; harvest when dry for sponges"),
    ("Squash",   "Silver-line Melon",            7, 10,  70,  85, "1x1", True,  "direct_sow",  "1 inch",   "full_sun", "Vining melon; trellis required"),
    # Beans
    ("Beans",    "Royal Burgundy Bush",          7, 10,  50,  60, "1x1", False, "direct_sow",  "1 inch",   "full_sun", None),
    ("Beans",    "Bush Cantare",                 7, 10,  50,  55, "1x1", False, "direct_sow",  "1 inch",   "full_sun", None),
    ("Beans",    "Blue Lake Bush",               7, 10,  55,  60, "1x1", False, "direct_sow",  "1 inch",   "full_sun", None),
    ("Beans",    "Pole Blue Lake",               7, 10,  60,  70, "1x1", True,  "direct_sow",  "1 inch",   "full_sun", "Future variety"),
    ("Beans",    "Midnight Bean",                7, 10,  55,  65, "1x1", False, "direct_sow",  "1 inch",   "full_sun", "Black bean; bush type"),
    ("Beans",    "PR Black Bean (vining)",       7, 10,  70,  85, "1x1", True,  "direct_sow",  "1 inch",   "full_sun", "Puerto Rican black bean; vigorous vining type; trellis required"),
    # Sweet Potatoes
    ("Sweet Potatoes", "Beauregard",             None, None, 90, 120, "2x2", False, "transplant", "slips",  "full_sun", "Plant from slips"),
    # Bunching Onions
    ("Bunching Onions", "Evergreen",             10, 14,  60,  70, "1x1", False, "direct_sow",  "1/4 inch", "full_sun", None),
    ("Bunching Onions", "Red Beard",             10, 14,  60,  70, "1x1", False, "direct_sow",  "1/4 inch", "full_sun", None),
    ("Bunching Onions", "Warrior",               10, 14,  60,  70, "1x1", False, "direct_sow",  "1/4 inch", "full_sun", None),
    ("Bunching Onions", "Bunching Onion",        10, 14,  60,  70, "1x1", False, "direct_sow",  "1/4 inch", "full_sun", "Generic bunching onion"),
    # Peas
    ("Peas",     "Snap Patio Pride",              7, 10,  55,  65, "1x1", True,  "direct_sow",  "1 inch",   "full_sun", "Future variety"),
    # Cabbage
    ("Cabbage",  "Dwarf Pak Choi",               5, 10,  45,  55, "1x1", False, "both",        "1/4 inch", "partial_shade", "Future variety"),
    # Melons
    ("Melons",   "Honey Rock Cantaloupe",        7, 10,  80,  90, "2x2", True,  "direct_sow",  "1 inch",   "full_sun", "Future variety"),
    # Radishes
    ("Radishes", "Watermelon Radish",            5,  7,  55,  65, "1x1", False, "direct_sow",  "1/2 inch", "full_sun", None),
    # Herbs
    ("Herbs",    "Rosemary",                    14, 21,  80,  90, "1x1", False, "transplant",  "surface",  "full_sun", "Perennial in 10a"),
    ("Herbs",    "English Thyme",               14, 21,  70,  80, "1x1", False, "transplant",  "surface",  "full_sun", "Perennial in 10a"),
    ("Herbs",    "French Thyme",                14, 21,  70,  80, "1x1", False, "transplant",  "surface",  "full_sun", "Future variety"),
    ("Herbs",    "Slow-Bolt Cilantro",           7, 10,  45,  55, "1x1", False, "direct_sow",  "1/4 inch", "partial_shade", None),
    ("Herbs",    "Bouquet Dill",                10, 14,  60,  70, "1x1", False, "direct_sow",  "1/4 inch", "full_sun", None),
    ("Herbs",    "Mammoth Dill",                10, 14,  65,  75, "1x1", False, "direct_sow",  "1/4 inch", "full_sun", "Future variety"),
    ("Herbs",    "Italian Large Leaf Basil",     7, 10,  50,  60, "1x1", False, "both",        "1/4 inch", "full_sun", None),
    ("Herbs",    "Green Basil",                  7, 10,  50,  60, "1x1", False, "both",        "1/4 inch", "full_sun", "Sweet green basil"),
    ("Herbs",    "Purple Basil",                 7, 10,  50,  60, "1x1", False, "both",        "1/4 inch", "full_sun", "Ornamental and culinary"),
    ("Herbs",    "Common Chives",               14, 21,  75,  90, "1x1", False, "transplant",  "1/4 inch", "full_sun", "Perennial"),
    ("Herbs",    "Chives",                      14, 21,  75,  90, "1x1", False, "direct_sow",  "1/4 inch", "full_sun", "Garlic or common chives"),
    ("Herbs",    "Parsley",                     14, 21,  70,  90, "1x1", False, "direct_sow",  "1/4 inch", "full_sun", "Flat-leaf or curly"),
    ("Herbs",    "Oregano",                     10, 14,  80,  90, "1x1", False, "transplant",  "surface",  "full_sun", "Mediterranean herb; perennial in 10a"),
    # Flowers
    ("Flowers",  "Naughty Marietta Marigold",    5,  7,  50,  60, "1x1", False, "direct_sow",  "1/4 inch", "full_sun", "Great companion"),
    ("Flowers",  "French Red Cherry Marigold",   5,  7,  50,  60, "1x1", False, "direct_sow",  "1/4 inch", "full_sun", "Great companion"),
    ("Flowers",  "Marigold (French Double Dwarf)",5, 7,  50,  60, "1x1", False, "direct_sow",  "1/4 inch", "full_sun", "Compact double-flowered marigold"),
    ("Flowers",  "Marigold",                     5,  7,  50,  60, "1x1", False, "direct_sow",  "1/4 inch", "full_sun", "General marigold; pest deterrent"),
    ("Flowers",  "Roselle",                     10, 14, 120, 150, "2x2", False, "direct_sow",  "1/4 inch", "full_sun", "Hibiscus for teas; ornamental"),
    ("Flowers",  "Thai Red Roselle",            10, 14, 120, 150, "2x2", False, "direct_sow",  "1/4 inch", "full_sun", "Red-stemmed Roselle variety; calyces for hibiscus tea"),
    ("Flowers",  "Roselle V2",                  10, 14, 120, 150, "2x2", False, "direct_sow",  "1/4 inch", "full_sun", "Second Roselle variety; ornamental and edible calyces"),
    ("Flowers",  "Cranberry Hibiscus",           7, 14,  90, 120, "2x2", False, "direct_sow",  "1/4 inch", "full_sun", "Deep red foliage; edible leaves; ornamental"),
    ("Flowers",  "Butterfly Pea",               7, 14,  60,  90, "1x1", True,  "direct_sow",  "1/4 inch", "full_sun", "Vining; trellis required; blue flowers for tea"),
    ("Flowers",  "Nasturtium (Jewel Mixed Colors)", 7, 10, 55, 70, "1x1", False, "direct_sow", "1/2 inch", "full_sun", "Edible flowers and leaves; compact mounding"),
    ("Flowers",  "Zinnia (Pinwheel Mixed Colors)",  5,  7, 60, 75, "1x1", False, "direct_sow", "1/4 inch", "full_sun", "Bright mixed colors; pollinator attractor"),
    # Okra
    ("Okra",     "Okra V1",                      5,  7,  50,  65, "1x1", False, "direct_sow",  "1/2 inch", "full_sun", "First okra variety"),
    ("Okra",     "Okra V2",                      5,  7,  50,  65, "1x1", False, "direct_sow",  "1/2 inch", "full_sun", "Second okra variety"),
    # Eggplant
    ("Eggplant", "Little Fingers Eggplant",     10, 14,  65,  80, "1x1", False, "transplant",  "1/4 inch", "full_sun", "Slender finger-sized fruits; prolific producer"),
    ("Eggplant", "Ping Tung Eggplant",          10, 14,  65,  80, "1x1", False, "transplant",  "1/4 inch", "full_sun", "Long slender Taiwanese variety; mild flavor"),
]

# ─── Containers ───────────────────────────────────────────────────────────────
CONTAINERS = [
    # Original 4×4 beds — North fence
    {"name": "Bed 1", "type": "grid_bed", "location_description": "North fence",
     "width": 4, "height": 4, "irrigation_type": "drip", "irrigation_duration_minutes": 30, "irrigation_frequency": "daily"},
    {"name": "Bed 2", "type": "grid_bed", "location_description": "North fence",
     "width": 4, "height": 4, "irrigation_type": "drip", "irrigation_duration_minutes": 30, "irrigation_frequency": "daily"},
    {"name": "Bed 3", "type": "grid_bed", "location_description": "North fence",
     "width": 4, "height": 4, "irrigation_type": "drip", "irrigation_duration_minutes": 30, "irrigation_frequency": "daily"},
    # New 5×5 beds — Back yard west
    {"name": "Bed 4", "type": "grid_bed", "location_description": "Back yard - west",
     "width": 5, "height": 5, "irrigation_type": "drip", "irrigation_duration_minutes": 30, "irrigation_frequency": "daily"},
    {"name": "Bed 5", "type": "grid_bed", "location_description": "Back yard - west",
     "width": 5, "height": 5, "irrigation_type": "drip", "irrigation_duration_minutes": 30, "irrigation_frequency": "daily"},
    {"name": "Bed 6", "type": "grid_bed", "location_description": "Back yard - west",
     "width": 5, "height": 5, "irrigation_type": "drip", "irrigation_duration_minutes": 30, "irrigation_frequency": "daily"},
    # Rolling bed — North fence
    {"name": "Rolling Bed", "type": "grid_bed", "location_description": "North fence",
     "width": 2, "height": 4, "irrigation_type": "manual", "irrigation_duration_minutes": 10, "irrigation_frequency": "daily"},
    {"name": "Tower", "type": "tower", "location_description": "Patio, near kitchen door",
     "levels": 7, "pockets_per_level": 6, "irrigation_type": "drip", "irrigation_duration_minutes": 15, "irrigation_frequency": "2x_daily"},
]

# Support structures: (container_name, square_x, square_y, support_type)
# Grid convention: Row A=y=0, B=y=1, C=y=2, D=y=3, E=y=4
#                  Col 1=x=0, 2=x=1, 3=x=2, 4=x=3, 5=x=4
SUPPORT_STRUCTURES = [
    # Original beds (4×4) — keep cages from original data
    ("Bed 2", 1, 1, "cage"),
    ("Bed 2", 2, 2, "cage"),
    # New beds (5×5) — Bed 4: E row (y=4) trellis
    ("Bed 4", 0, 4, "trellis"), ("Bed 4", 1, 4, "trellis"), ("Bed 4", 2, 4, "trellis"),
    ("Bed 4", 3, 4, "trellis"), ("Bed 4", 4, 4, "trellis"),
    # Bed 5: A row (y=0) and E row (y=4) trellis
    ("Bed 5", 0, 0, "trellis"), ("Bed 5", 1, 0, "trellis"), ("Bed 5", 2, 0, "trellis"),
    ("Bed 5", 3, 0, "trellis"), ("Bed 5", 4, 0, "trellis"),
    ("Bed 5", 0, 4, "trellis"), ("Bed 5", 1, 4, "trellis"), ("Bed 5", 2, 4, "trellis"),
    ("Bed 5", 3, 4, "trellis"), ("Bed 5", 4, 4, "trellis"),
    # Bed 6: A row (y=0) and E row (y=4) trellis; stake at D3 (x=2, y=3)
    ("Bed 6", 0, 0, "trellis"), ("Bed 6", 1, 0, "trellis"), ("Bed 6", 2, 0, "trellis"),
    ("Bed 6", 3, 0, "trellis"), ("Bed 6", 4, 0, "trellis"),
    ("Bed 6", 0, 4, "trellis"), ("Bed 6", 1, 4, "trellis"), ("Bed 6", 2, 4, "trellis"),
    ("Bed 6", 3, 4, "trellis"), ("Bed 6", 4, 4, "trellis"),
    ("Bed 6", 2, 3, "stake"),
    # Rolling Bed
    ("Rolling Bed", 0, 0, "cage"), ("Rolling Bed", 1, 0, "cage"),
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

        # ── 8. Create plantings ───────────────────────────────────────────
        # Grid coordinate convention:
        #   Row A=y=0, B=y=1, C=y=2, D=y=3, E=y=4
        #   Col 1=x=0, 2=x=1, 3=x=2, 4=x=3, 5=x=4
        today = date.today()
        planting_map: dict[str, Planting] = {}

        def add_planting(key, cont_name, var_name, x, y, w, h, start_off, end_off,
                         status, method, qty, tower_level=None, removal_reason=None):
            p = Planting(
                user_id=user.id,
                container_id=cont_map[cont_name].id,
                variety_id=var_map[var_name].id,
                square_x=x, square_y=y, square_width=w, square_height=h,
                tower_level=tower_level,
                start_date=today + timedelta(days=start_off),
                end_date=today + timedelta(days=end_off),
                status=status,
                planting_method=method,
                quantity=qty,
                removal_reason=removal_reason,
            )
            return p

        def make_bed_planting(key, bed_name, var_name, x, y, w=1, h=1):
            variety = var_map[var_name]
            end_days = variety.days_to_harvest_max or 90
            return Planting(
                user_id=user.id,
                container_id=cont_map[bed_name].id,
                variety_id=variety.id,
                square_x=x, square_y=y, square_width=w, square_height=h,
                tower_level=None,
                start_date=today,
                end_date=today + timedelta(days=end_days),
                status="not_started",
                planting_method=variety.planting_method,
                quantity=1,
            )

        # ── BED 1 (4×4, North fence) ─────────────────────────────────────
        # All in_progress (transplanted ~30 days ago)
        bed1_data = [
            # (key, var_name, x, y, w, h, start_off, end_off, status, method, qty)
            ("p1_A1", "Golden Jubilee",           0, 0, 2, 2, -30,  50, "in_progress", "transplant", 1),
            ("p1_C1", "Husky Cherry Red",          0, 2, 2, 2, -30,  40, "in_progress", "transplant", 1),
            ("p1_A3", "Poblano",                   2, 0, 1, 1, -25,  55, "in_progress", "transplant", 1),
            ("p1_A4", "Cubanelle",                 3, 0, 1, 1, -25,  55, "in_progress", "transplant", 1),
            ("p1_B3", "Orange Sweet",              2, 1, 1, 1, -25,  60, "in_progress", "transplant", 1),
            ("p1_B4", "Jalapeño",                  3, 1, 1, 1, -25,  55, "in_progress", "transplant", 1),
            # C3 empty — no planting
            ("p1_C4", "Italian Large Leaf Basil",  3, 2, 1, 1, -20,  40, "in_progress", "transplant", 1),
            ("p1_D3", "Marigold",                  2, 3, 1, 1, -30,  20, "in_progress", "transplant", 1),
            ("p1_D4", "Little Fingers Eggplant",   3, 3, 1, 1, -25,  55, "in_progress", "transplant", 1),
        ]
        for row in bed1_data:
            key, var_name, x, y, w, h, s_off, e_off, status, method, qty = row
            p = add_planting(key, "Bed 1", var_name, x, y, w, h, s_off, e_off, status, method, qty)
            session.add(p)
            await session.flush()
            planting_map[key] = p

        # ── BED 2 (4×4, North fence) ─────────────────────────────────────
        # All in_progress cucumbers and squash
        bed2_data = [
            ("p2_A1", "Garden Bush Slicer",    0, 0, 1, 1, -20,  45, "in_progress", "direct_sow", 3),
            ("p2_A2", "Garden Bush Slicer",    1, 0, 1, 1, -20,  45, "in_progress", "direct_sow", 3),
            ("p2_B1", "Garden Bush Slicer",    0, 1, 1, 1, -20,  45, "in_progress", "direct_sow", 3),
            ("p2_B2", "Garden Bush Slicer",    1, 1, 1, 1, -20,  45, "in_progress", "direct_sow", 3),
            ("p2_A3", "Double Yield Pickling", 2, 0, 1, 1, -20,  40, "in_progress", "direct_sow", 3),
            ("p2_A4", "Double Yield Pickling", 3, 0, 1, 1, -20,  40, "in_progress", "direct_sow", 3),
            ("p2_B3", "Double Yield Pickling", 2, 1, 1, 1, -20,  40, "in_progress", "direct_sow", 3),
            ("p2_B4", "Double Yield Pickling", 3, 1, 1, 1, -20,  40, "in_progress", "direct_sow", 3),
            ("p2_C1", "Crookneck",             0, 2, 2, 2, -20,  40, "in_progress", "direct_sow", 2),  # 2×2
            ("p2_C3", "Easy Pick Gold Zucchini", 2, 2, 2, 2, -20, 35, "in_progress", "direct_sow", 2),  # 2×2
        ]
        for row in bed2_data:
            key, var_name, x, y, w, h, s_off, e_off, status, method, qty = row
            p = add_planting(key, "Bed 2", var_name, x, y, w, h, s_off, e_off, status, method, qty)
            session.add(p)
            await session.flush()
            planting_map[key] = p

        # ── BED 3 (4×4, North fence) ─────────────────────────────────────
        bed3_data = [
            ("p3_A1", "Rosemary",                 0, 0, 1, 1, -60, 300, "in_progress", "transplant",  1),
            ("p3_A2", "English Thyme",             1, 0, 1, 1, -60, 300, "in_progress", "transplant",  1),
            ("p3_A3", "Chives",                    2, 0, 1, 1, -40,  50, "in_progress", "direct_sow",  9),
            # A4 empty
            ("p3_B1", "Italian Large Leaf Basil",  0, 1, 1, 1, -20,  40, "in_progress", "transplant",  3),
            ("p3_B2", "Slow-Bolt Cilantro",        1, 1, 1, 1, -14,  40, "in_progress", "direct_sow",  6),
            ("p3_B3", "Slow-Bolt Cilantro",        2, 1, 1, 1, -14,  40, "in_progress", "direct_sow",  6),
            ("p3_B4", "Bouquet Dill",              3, 1, 1, 1, -14,  56, "in_progress", "direct_sow",  4),
            ("p3_C1", "Royal Burgundy Bush",       0, 2, 1, 1, -15,  45, "in_progress", "direct_sow",  9),
            ("p3_C2", "Royal Burgundy Bush",       1, 2, 1, 1, -15,  45, "in_progress", "direct_sow",  9),
            ("p3_C3", "Bush Cantare",              2, 2, 1, 1, -15,  40, "in_progress", "direct_sow",  9),
            ("p3_C4", "Bush Cantare",              3, 2, 1, 1, -15,  40, "in_progress", "direct_sow",  9),
            ("p3_D1", "Watermelon Radish",         0, 3, 1, 1, -15,  50, "in_progress", "direct_sow",  9),
            ("p3_D2", "Marigold",                  1, 3, 1, 1, -30,  20, "in_progress", "direct_sow",  4),
            ("p3_D3", "Marigold",                  2, 3, 1, 1, -30,  20, "in_progress", "direct_sow",  4),
            ("p3_D4", "Bouquet Dill",              3, 3, 1, 1, -14,  56, "in_progress", "direct_sow",  4),
        ]
        for row in bed3_data:
            key, var_name, x, y, w, h, s_off, e_off, status, method, qty = row
            p = add_planting(key, "Bed 3", var_name, x, y, w, h, s_off, e_off, status, method, qty)
            session.add(p)
            await session.flush()
            planting_map[key] = p

        # ── ROLLING BED (2×4, North fence) ───────────────────────────────
        rolling_data = [
            ("pr_A1", "Blue Lake Bush",  0, 0, 1, 1, -15,  45, "in_progress", "direct_sow", 9),
            ("pr_A2", "Beauregard",      1, 0, 1, 1, -30,  90, "in_progress", "transplant", 1),
            ("pr_B1", "Blue Lake Bush",  0, 1, 1, 1, -15,  45, "in_progress", "direct_sow", 9),
            ("pr_B2", "Beauregard",      1, 1, 1, 1, -30,  90, "in_progress", "transplant", 1),
            ("pr_C1", "Warrior",         0, 2, 1, 1, -40,  30, "in_progress", "direct_sow", 16),
            ("pr_C2", "Beauregard",      1, 2, 1, 1, -30,  90, "in_progress", "transplant", 1),
            ("pr_D1", "Red Beard",       0, 3, 1, 1, -40,  30, "in_progress", "direct_sow", 16),
            ("pr_D2", "Beauregard",      1, 3, 1, 1, -30,  90, "in_progress", "transplant", 1),
        ]
        for row in rolling_data:
            key, var_name, x, y, w, h, s_off, e_off, status, method, qty = row
            p = add_planting(key, "Rolling Bed", var_name, x, y, w, h, s_off, e_off, status, method, qty)
            session.add(p)
            await session.flush()
            planting_map[key] = p

        # ── BED 4 (5×5, Back yard west, planned 4/3) ─────────────────────
        bed4_rows = [
            ("b4_A1", "Chives",                   0, 0),
            ("b4_A2", "Thai Red Roselle",          1, 0, 2, 2),  # A2/A3/B2/B3
            ("b4_A4", "Okra V1",                  3, 0),
            ("b4_A5", "Marigold",                 4, 0),
            ("b4_B1", "Midnight Bean",            0, 1),
            ("b4_B4", "Parsley",                  3, 1),
            ("b4_B5", "Midnight Bean",            4, 1),
            ("b4_C1", "Marigold",                 0, 2),
            ("b4_C2", "Okra V2",                  1, 2),
            ("b4_C3", "Green Basil",              2, 2),
            ("b4_C4", "Midnight Bean",            3, 2),
            ("b4_C5", "Chives",                   4, 2),
            ("b4_D1", "Midnight Bean",            0, 3),
            ("b4_D2", "Purple Basil",             1, 3),
            ("b4_D3", "Marigold",                 2, 3),
            ("b4_D4", "Green Basil",              3, 3),
            ("b4_D5", "Midnight Bean",            4, 3),
            ("b4_E1", "White Everglades Tomato",  0, 4),
            ("b4_E2", "Butterfly Pea",            1, 4),
            ("b4_E3", "Seminole Pumpkin",         2, 4),
            ("b4_E4", "Loofah",                   3, 4),
            ("b4_E5", "Silver-line Melon",        4, 4),
        ]
        for row in bed4_rows:
            key = row[0]
            vn = row[1]
            x = row[2]
            y = row[3]
            w = row[4] if len(row) > 4 else 1
            h = row[5] if len(row) > 5 else 1
            p = make_bed_planting(key, "Bed 4", vn, x, y, w, h)
            session.add(p)
            await session.flush()
            planting_map[key] = p

        # ── BED 5 (5×5, Back yard west, planned 4/3) ─────────────────────
        bed5_rows = [
            ("b5_A1", "Seminole Pumpkin",         0, 0),
            ("b5_A2", "PR Black Bean (vining)",   1, 0),
            ("b5_A3", "Butterfly Pea",            2, 0),
            ("b5_A4", "White Everglades Tomato",  3, 0),
            ("b5_A5", "PR Black Bean (vining)",   4, 0),
            ("b5_B1", "Okra V1",                  0, 1),
            ("b5_B2", "Roselle V2",               1, 1, 2, 2),  # B2/B3/C2/C3
            ("b5_B4", "Bunching Onion",           3, 1),
            ("b5_B5", "Marigold",                 4, 1),
            ("b5_C1", "Midnight Bean",            0, 2),
            ("b5_C4", "Little Fingers Eggplant",  3, 2),
            ("b5_C5", "Oregano",                  4, 2),
            ("b5_D1", "Chives",                   0, 3),
            ("b5_D2", "Ping Tung Eggplant",       1, 3),
            ("b5_D3", "Marigold",                 2, 3),
            ("b5_D4", "Midnight Bean",            3, 3),
            ("b5_D5", "Bunching Onion",           4, 3),
            ("b5_E1", "Butterfly Pea",            0, 4),
            ("b5_E2", "White Everglades Tomato",  1, 4),
            ("b5_E3", "Silver-line Melon",        2, 4),
            ("b5_E4", "Seminole Pumpkin",         3, 4),
            ("b5_E5", "Loofah",                   4, 4),
        ]
        for row in bed5_rows:
            key = row[0]
            vn = row[1]
            x = row[2]
            y = row[3]
            w = row[4] if len(row) > 4 else 1
            h = row[5] if len(row) > 5 else 1
            p = make_bed_planting(key, "Bed 5", vn, x, y, w, h)
            session.add(p)
            await session.flush()
            planting_map[key] = p

        # ── BED 6 (5×5, Back yard west, planned 4/3) ─────────────────────
        bed6_rows = [
            ("b6_A1", "White Everglades Tomato",  0, 0),
            ("b6_A2", "Silver-line Melon",        1, 0),
            ("b6_A3", "PR Black Bean (vining)",   2, 0),
            ("b6_A4", "Seminole Pumpkin",         3, 0),
            ("b6_A5", "Butterfly Pea",            4, 0),
            ("b6_B1", "Bunching Onion",           0, 1),
            ("b6_B2", "Cranberry Hibiscus",       1, 1, 2, 2),  # B2/B3/C2/C3
            ("b6_B4", "Okra V2",                  3, 1),
            ("b6_B5", "Parsley",                  4, 1),
            ("b6_C1", "Little Fingers Eggplant",  0, 2),
            ("b6_C4", "Marigold",                 3, 2),
            ("b6_C5", "Midnight Bean",            4, 2),
            ("b6_D1", "Purple Basil",             0, 3),
            ("b6_D2", "Okra V2",                  1, 3),
            ("b6_D3", "Sweet Banana Pepper",      2, 3),
            ("b6_D4", "Ping Tung Eggplant",       3, 3),
            ("b6_D5", "Marigold",                 4, 3),
            ("b6_E1", "Butterfly Pea",            0, 4),
            ("b6_E2", "Red Everglades Tomato",    1, 4),
            ("b6_E3", "Loofah",                   2, 4),
            ("b6_E4", "White Everglades Tomato",  3, 4),
            ("b6_E5", "PR Black Bean (vining)",   4, 4),
        ]
        for row in bed6_rows:
            key = row[0]
            vn = row[1]
            x = row[2]
            y = row[3]
            w = row[4] if len(row) > 4 else 1
            h = row[5] if len(row) > 5 else 1
            p = make_bed_planting(key, "Bed 6", vn, x, y, w, h)
            session.add(p)
            await session.flush()
            planting_map[key] = p

        # ── TOWER (7 levels × 6 pockets, planted March 27) ───────────────
        # tower_level is 0-indexed (0 = top / Level 1 in UI)
        # square_x is pocket index (0-indexed, 0 = Pocket 1 … 5 = Pocket 6)
        planting_date_tower = today - timedelta(days=7)
        tower_levels = [
            (0, "Naughty Marietta Marigold"),        # Level 1 (top)
            (1, "Nasturtium (Jewel Mixed Colors)"),  # Level 2
            (2, "Marigold (French Double Dwarf)"),   # Level 3
            (3, "Zinnia (Pinwheel Mixed Colors)"),   # Level 4
            (4, "French Red Cherry Marigold"),       # Level 5
            (5, "Naughty Marietta Marigold"),        # Level 6
            (6, "Nasturtium (Jewel Mixed Colors)"),  # Level 7 (bottom)
        ]
        tower_count = 0
        for level_idx, var_name in tower_levels:
            variety = var_map[var_name]
            end_days = variety.days_to_harvest_max or 60
            for pocket in range(6):
                p = Planting(
                    user_id=user.id,
                    container_id=cont_map["Tower"].id,
                    variety_id=variety.id,
                    square_x=pocket, square_y=0, square_width=1, square_height=1,
                    tower_level=level_idx,
                    start_date=planting_date_tower,
                    end_date=planting_date_tower + timedelta(days=end_days),
                    status="in_progress",
                    planting_method=variety.planting_method,
                    quantity=1,
                )
                session.add(p)
                await session.flush()
                planting_map[f"tower_L{level_idx}_P{pocket}"] = p
                tower_count += 1

        print(f"  Created {len(planting_map)} plantings (including {tower_count} tower pockets)")

        # ── 9. Create events ──────────────────────────────────────────────
        event_count = 0

        # Planting events for all in-progress bed plantings
        for key, p in planting_map.items():
            if key.startswith("tower_") or p.status != "in_progress":
                continue
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

        # Planting events for tower
        for level_idx, _ in tower_levels:
            for pocket in range(6):
                p = planting_map[f"tower_L{level_idx}_P{pocket}"]
                session.add(Event(
                    user_id=user.id,
                    container_id=p.container_id,
                    planting_id=p.id,
                    variety_id=p.variety_id,
                    event_type="planting",
                    date=p.start_date,
                    quantity=1,
                    square_x=p.square_x,
                    square_y=p.square_y,
                    tower_level=p.tower_level,
                    notes=f"Planted level {level_idx + 1} pocket {pocket + 1} via {p.planting_method}",
                ))
                event_count += 1

        await session.flush()
        print(f"  Created {event_count} events")

        # ── 10. Create sample journal notes ──────────────────────────────
        note_count = 0
        session.add(JournalNote(
            user_id=user.id,
            container_id=cont_map["Bed 1"].id,
            content="Tomatoes and peppers looking healthy. Golden Jubilee putting out new growth. Eggplant and basil are settling in nicely.",
            date=today - timedelta(days=5),
        ))
        note_count += 1

        session.add(JournalNote(
            user_id=user.id,
            container_id=cont_map["Bed 2"].id,
            content="Cucumbers are climbing well. Squash starting to spread — may need to train them. Picklers looking more vigorous than slicers.",
            date=today - timedelta(days=3),
        ))
        note_count += 1

        session.add(JournalNote(
            user_id=user.id,
            container_id=cont_map["Tower"].id,
            content="Seeded all 7 tower levels with flowers on March 27. Marigolds, nasturtiums, and zinnias. Should look beautiful once they fill in.",
            date=planting_date_tower,
        ))
        note_count += 1

        session.add(JournalNote(
            user_id=user.id,
            content="Planned out Beds 4, 5, and 6 (new 5×5 beds, back yard west). Lots of tropical/heat-tolerant varieties for the season. Trellis rows for climbers.",
            date=today,
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
