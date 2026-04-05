"""Reference data seeder for Tendril — shared between dev and production.

Seeds: user, categories, planting seasons, companion rules, varieties.
Returns (user, cat_map, var_map) for use by environment-specific seeders.

Not meant to be run directly — called by seed_dev.py and seed_production.py.
"""

from app.models import (
    Category,
    CompanionRule,
    PlantingSeason,
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
    ("Bunching Onions", "Lisbon Bunching Onion", 10, 14,  60,  70, "1x1", False, "direct_sow",  "1/4 inch", "full_sun", "Generic bunching onion"),
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
    ("Herbs",    "Oregano",                     10, 14,  80,  90, "1x1", False, "both",        "surface",  "full_sun", "Mediterranean herb; perennial in 10a"),
    # Flowers
    ("Flowers",  "Queen Sophia Marigold",        5,  7,  50,  60, "1x1", False, "direct_sow",  "1/4 inch", "full_sun", "Great companion"),
    ("Flowers",  "Naughty Marietta Marigold",    5,  7,  50,  60, "1x1", False, "direct_sow",  "1/4 inch", "full_sun", "Great companion"),
    ("Flowers",  "French Red Cherry Marigold",   5,  7,  50,  60, "1x1", False, "direct_sow",  "1/4 inch", "full_sun", "Great companion"),
    ("Flowers",  "Marigold (French Double Dwarf)",5, 7,  50,  60, "1x1", False, "direct_sow",  "1/4 inch", "full_sun", "Compact double-flowered marigold"),
    ("Flowers",  "Marigold",                     5,  7,  50,  60, "1x1", False, "direct_sow",  "1/4 inch", "full_sun", "General marigold; pest deterrent"),
    ("Flowers",  "Roselle",                     10, 14, 120, 150, "2x2", False, "direct_sow",  "1/4 inch", "full_sun", "Hibiscus for teas; ornamental"),
    ("Flowers",  "Thai Red Roselle",            10, 14, 120, 150, "2x2", False, "direct_sow",  "1/4 inch", "full_sun", "Red-stemmed Roselle variety; calyces for hibiscus tea"),
    ("Flowers",  "Roselle St. Kitts & Nevis",   10, 14, 120, 150, "2x2", False, "direct_sow",  "1/4 inch", "full_sun", "Second Roselle variety; ornamental and edible calyces"),
    ("Flowers",  "Cranberry Hibiscus",          7, 14,  90, 120, "2x2", False, "direct_sow",  "1/4 inch", "full_sun", "Deep red foliage; edible leaves; ornamental"),
    ("Flowers",  "Butterfly Pea",               7, 14,  60,  90, "1x1", True,  "direct_sow",  "1/4 inch", "full_sun", "Vining; trellis required; blue flowers for tea"),
    ("Flowers",  "Nasturtium (Jewel Mixed Colors)", 7, 10, 55, 70, "1x1", False, "direct_sow", "1/2 inch", "full_sun", "Edible flowers and leaves; compact mounding"),
    ("Flowers",  "Zinnia (Pinwheel Mixed Colors)",  5,  7, 60, 75, "1x1", False, "direct_sow", "1/4 inch", "full_sun", "Bright mixed colors; pollinator attractor"),
    # Okra
    ("Okra",     "Red Burgundy",                5,  7,  50,  65, "1x1", False, "direct_sow",  "1/2 inch", "full_sun", "First okra variety"),
    ("Okra",     "Clemson Spineless 80",        5,  7,  50,  65, "1x1", False, "direct_sow",  "1/2 inch", "full_sun", "Second okra variety"),
    # Eggplant
    ("Eggplant", "Little Fingers Eggplant",     10, 14,  65,  80, "1x1", False, "transplant",  "1/4 inch", "full_sun", "Slender finger-sized fruits; prolific producer"),
    ("Eggplant", "Rosa Bianca Eggplant",        10, 14,  65,  80, "1x1", False, "transplant",  "1/4 inch", "full_sun", "Slender finger-sized fruits; prolific producer"),
    ("Eggplant", "Ping Tung Eggplant",          10, 14,  65,  80, "1x1", False, "transplant",  "1/4 inch", "full_sun", "Long slender Taiwanese variety; mild flavor"),
]


async def seed_reference(session, email: str, name: str = "Dev User"):
    """Seed all shared reference data and return (user, cat_map, var_map).

    Args:
        session: An active AsyncSession.
        email: The user's email address.
        name: The user's display name.

    Returns:
        Tuple of (user, cat_map, var_map) for use in environment-specific seeders.
    """
    # ── 1. Create user ────────────────────────────────────────────────────────
    user = User(
        email=email,
        name=name,
        settings={
            "usda_zone": "10a",
            "weather_lat": 27.7676,
            "weather_lon": -82.6403,
            "weather_city": "St. Petersburg",
        },
    )
    session.add(user)
    await session.flush()
    print(f"  Created user: {user.email} (id={user.id})")

    # ── 2. Create categories ──────────────────────────────────────────────────
    cat_map: dict[str, Category] = {}
    for cat_data in CATEGORIES:
        cat = Category(**cat_data)
        session.add(cat)
        await session.flush()
        cat_map[cat.name] = cat
    print(f"  Created {len(cat_map)} categories")

    # ── 3. Create planting seasons ────────────────────────────────────────────
    count = 0
    for cat_name, sm, sd, em, ed in PLANTING_SEASONS_10A:
        session.add(PlantingSeason(
            category_id=cat_map[cat_name].id, usda_zone="10a",
            start_month=sm, start_day=sd, end_month=em, end_day=ed,
        ))
        count += 1
    await session.flush()
    print(f"  Created {count} planting seasons for Zone 10a")

    # ── 4. Create companion rules ─────────────────────────────────────────────
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

    # ── 5. Create varieties ───────────────────────────────────────────────────
    var_map: dict[str, Variety] = {}
    for v in VARIETIES:
        cat_name, vname, dg_min, dg_max, dh_min, dh_max, spacing, climbing, method, depth, sun, notes = v
        variety = Variety(
            user_id=user.id, category_id=cat_map[cat_name].id, name=vname,
            days_to_germination_min=dg_min, days_to_germination_max=dg_max,
            days_to_harvest_min=dh_min, days_to_harvest_max=dh_max,
            spacing=spacing, is_climbing=climbing, planting_method=method,
            planting_depth=depth, sunlight=sun, notes=notes,
        )
        session.add(variety)
        await session.flush()
        var_map[vname] = variety
    print(f"  Created {len(var_map)} varieties")

    return user, cat_map, var_map
