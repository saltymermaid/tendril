"""seed varieties from Southern Exposure order

Revision ID: e3f4a5b6c7d8
Revises: c1d2e3f4a5b6
Create Date: 2026-08-23 00:00:00.000000

Adds new plant varieties (and any categories they need) from a real Southern
Exposure Seed Exchange order to the account's catalog. Idempotent: skips any
variety whose name already exists for the owner, and any category whose name
already exists globally, so it's safe to re-run.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import Session

revision: str = 'e3f4a5b6c7d8'
down_revision: Union[str, None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OWNER_EMAIL = "msblades@gmail.com"

categories = sa.table(
    "categories",
    sa.column("id", sa.Integer),
    sa.column("name", sa.String),
    sa.column("color", sa.String),
    sa.column("harvest_type", sa.String),
    sa.column("icon_svg", sa.Text),
)
varieties = sa.table(
    "varieties",
    sa.column("id", sa.Integer),
    sa.column("user_id", sa.Integer),
    sa.column("category_id", sa.Integer),
    sa.column("name", sa.String),
    sa.column("days_to_germination_min", sa.Integer),
    sa.column("days_to_germination_max", sa.Integer),
    sa.column("days_to_harvest_min", sa.Integer),
    sa.column("days_to_harvest_max", sa.Integer),
    sa.column("seed_start_days", sa.Integer),
    sa.column("planting_depth", sa.String),
    sa.column("spacing", sa.String),
    sa.column("sunlight", sa.String),
    sa.column("is_climbing", sa.Boolean),
    sa.column("planting_method", sa.String),
    sa.column("notes", sa.Text),
)


def _emoji_svg(emoji: str) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><text y="28" font-size="28">{emoji}</text></svg>'


# New categories needed for this order; skipped at insert time if the name
# already exists (categories.name is globally unique).
NEW_CATEGORIES = [
    {"name": "Sunflowers",  "color": "#F6E05E", "harvest_type": "single", "icon_svg": _emoji_svg("🌻")},
    {"name": "Beets",       "color": "#97266D", "harvest_type": "single", "icon_svg": _emoji_svg("🟣")},
    {"name": "Broccoli",    "color": "#319795", "harvest_type": "single", "icon_svg": _emoji_svg("🥦")},
    {"name": "Swiss Chard", "color": "#B83280", "harvest_type": "continuous", "icon_svg": _emoji_svg("🌈")},
    {"name": "Kohlrabi",    "color": "#4C51BF", "harvest_type": "single", "icon_svg": _emoji_svg("🟢")},
    {"name": "Cauliflower", "color": "#A0AEC0", "harvest_type": "single", "icon_svg": _emoji_svg("⚪")},
    {"name": "Carrots",     "color": "#ED8936", "harvest_type": "single", "icon_svg": _emoji_svg("🥕")},
    {"name": "Peanuts",     "color": "#B7791F", "harvest_type": "single", "icon_svg": _emoji_svg("🥜")},
    {"name": "Corn",        "color": "#ECC94B", "harvest_type": "single", "icon_svg": _emoji_svg("🌽")},
    {"name": "Onions",      "color": "#6B46C1", "harvest_type": "single", "icon_svg": _emoji_svg("🧅")},
]

# (category, name, germ_min, germ_max, harvest_min, harvest_max, spacing,
#  is_climbing, planting_method, depth, sunlight, notes, seed_start_days)
#
# Varieties from the order that duplicate what's already in the starter
# reference catalog (Jalapeño, Sweet Banana Pepper, Seminole Pumpkin, Thai Red
# Roselle, Roselle St. Kitts & Nevis, Ping Tung Eggplant, Everglades tomato)
# are intentionally omitted here.
NEW_VARIETIES = [
    ("Tomatoes",  "Cherokee Purple Tomato",                    7, 14,  75,  85, "2x2", False, "transplant",  "1/4 inch", "full_sun", "Classic pink-purple beefsteak heirloom; indeterminate", 56),
    ("Peppers",   "Chinese Five-Color Hot Pepper",             7, 10,  68,  82, "1x1", False, "transplant",  "1/4 inch", "full_sun", "Ornamental/edible; fruits ripen purple, cream, yellow, orange, red", 70),
    ("Peppers",   "Hungarian Wax (Hot Banana) Hot Pepper",    10, 14,  65,  75, "1x1", False, "transplant",  "1/4 inch", "full_sun", "Medium-heat wax pepper; ripens yellow to red", 70),
    ("Peppers",   "Sweet Pickle (Christmas Tree) Pepper",     10, 14,  55,  65, "1x1", False, "transplant",  "1/4 inch", "full_sun", "Compact 18-24in ornamental/edible; multicolor upright fruits", 70),
    ("Eggplant",  "Florida High Bush Eggplant",                 7, 10,  75,  85, "1x1", False, "transplant",  "1/4 inch", "full_sun", "Vigorous upright heirloom bred in Florida; disease and drought resistant", 56),
    ("Sunflowers","Evening Sun Sunflower",                      7, 14,  85, 100, "1x1", False, "direct_sow",  "1/2 inch", "full_sun", "6-8 ft branching sunflower; bicolor dark-centered blooms", None),
    ("Beets",     "Bull's Blood Beet",                          5, 12,  35,  60, "1x1", False, "direct_sow",  "1/2 inch", "full_sun", "Deep red-purple leaves; excellent baby greens or roots", None),
    ("Radishes",  "Black Spanish Round Fall Radish",            5,  8,  50,  60, "1x1", False, "direct_sow",  "1/2 inch", "full_sun", "Winter storage radish; black skin, firm white flesh; good keeper", None),
    ("Beets",     "Chioggia Beet",                              6, 12,  55,  65, "1x1", False, "direct_sow",  "1/2 inch", "full_sun", "Italian heirloom; candy-cane pink-and-white rings when sliced", None),
    ("Broccoli",  "Calabrese (Italian Green Sprouting) Broccoli", 5, 10, 60,  75, "1x1", False, "transplant",  "1/4 inch", "full_sun", "Classic Italian sprouting broccoli; central head plus abundant side shoots", 35),
    ("Sunflowers","Sunspot Dwarf Sunflower",                    7, 14,  60,  70, "1x1", False, "direct_sow",  "1/2 inch", "full_sun", "4-4.5 ft dwarf sunflower; single 8-12in head; good for seed or ornamental", None),
    ("Sunflowers","Short Stuff Dwarf Sunflower",                7, 10,  53,  60, "1x1", False, "direct_sow",  "1/2 inch", "full_sun", "30in dwarf sunflower; good for containers and small beds", None),
    ("Swiss Chard","Rainbow (Five Color Silverbeet) Swiss Chard", 7, 14,  50,  60, "1x1", False, "direct_sow", "1/2 inch", "full_sun", "Vibrant multicolor stems; cut-and-come-again leafy green", None),
    ("Kohlrabi",  "Early Purple Vienna Kohlrabi",                5, 10,  55,  65, "1x1", False, "both",        "1/4 inch", "full_sun", "Pre-1860 heirloom; purple bulb-like stem, mild turnip-cabbage flavor", 28),
    ("Radishes",  "Misato Rose Fall Radish",                    5, 10,  55,  65, "1x1", False, "direct_sow",  "1/2 inch", "full_sun", "Watermelon-type winter radish; green shoulders, rose-pink flesh; forgiving of crowding", None),
    ("Cauliflower","Snowball Self-Blanching Fall Cauliflower",  7, 14,  60,  70, "1x1", False, "transplant",  "1/4 inch", "full_sun", "Self-wrapping leaves protect curds from sun; good fall variety for FL", 35),
    ("Cabbage",   "Early Flat Dutch Cabbage",                   7, 10,  75,  85, "1x1", False, "transplant",  "1/4 inch", "full_sun", "Heirloom flat-headed storage cabbage", 42),
    ("Herbs",     "Cilantro (Coriander)",                       7, 10,  45,  55, "1x1", False, "direct_sow",  "1/4 inch", "partial_shade", "Bolts fast in FL heat; sow in shade, succession plant monthly", None),
    ("Carrots",   "Cosmic Purple Carrots",                     10, 14,  65,  75, "1x1", False, "direct_sow",  "1/4 inch", "full_sun", "Purple skin, orange interior; striking heirloom carrot", None),
    ("Peanuts",   "Carolina Black Peanut",                     10, 14, 100, 120, "1x1", False, "direct_sow",  "1 1/2 inch", "full_sun", "Heirloom black-skinned peanut; drought tolerant; needs a full FL growing season", None),
    ("Kale",      "Lacinato (Dinosaur) Kale",                   5, 10,  60,  70, "1x1", False, "both",        "1/4 inch", "full_sun", "Dark blue-green savoyed leaves; classic Tuscan kale, heat tolerant for FL", 28),
    ("Corn",      "Bodacious RM Sweet Corn",                    7, 10,  75,  80, "1x1", False, "direct_sow",  "1 1/2 inch", "full_sun", "Sugary-enhanced hybrid; plant in blocks of 4+ rows for pollination", None),
    ("Carrots",   "Fantasia Carrots",                          10, 14,  65,  75, "1x1", False, "direct_sow",  "1/4 inch", "full_sun", "Rainbow blend of orange, yellow, and purple carrots", None),
    ("Onions",    "Granex Hybrid Dry Bulb Onion",                7, 14, 100, 120, "1x1", False, "transplant",  "1/4 inch", "full_sun", "Sweet short-day onion (Vidalia-type); best for Zone 10a's short-day window", 70),
    ("Peppers",   "Charleston Belle Sweet Bell Pepper",        10, 14,  65,  75, "1x1", False, "transplant",  "1/4 inch", "full_sun", "Nematode-resistant bell pepper bred for Southern gardens", 70),
    ("Peppers",   "Carolina Wonder Sweet Bell Pepper",         10, 14,  70,  80, "1x1", False, "transplant",  "1/4 inch", "full_sun", "Nematode-resistant bell pepper; large blocky 3-4 lobed fruit", 70),
    ("Peppers",   "Marconi Sweet Bell Pepper",                 10, 14,  75,  90, "1x1", False, "transplant",  "1/4 inch", "full_sun", "Elongated Italian frying pepper; sweet, can ripen to red or gold", 70),
    ("Beans",     "Broad Windsor Fava Bean",                    7, 14,  80,  90, "1x1", False, "direct_sow",  "1 inch",   "full_sun", "Large-seeded cool-season fava; sow fall/winter in FL, harvest before summer heat", None),
    ("Onions",    "Texas Early Grano Dry Bulb Onion",            7, 14,  90, 110, "1x1", False, "transplant",  "1/4 inch", "full_sun", "Early short-day sweet onion; good choice for FL's mild winters", 70),
    ("Beans",     "Sweet Lorane Fava Bean",                      7, 14,  80,  90, "1x1", False, "direct_sow",  "1 inch",   "full_sun", "Small-seeded, productive, cold-hardy fava; excellent flavor", None),
]

# Aliases already present in the starter reference catalog: if any of these
# names already exist for the owner, we skip that NEW_VARIETIES row entirely
# (see module docstring) — this list documents which ones were excluded and
# why, so the mapping is discoverable on downgrade/re-read.
SKIPPED_AS_DUPLICATE_OF = {
    "Sweet Banana (Long Sweet Hungarian) Sweet Pepper": "Sweet Banana Pepper",
    "Ping Tung Long Eggplant": "Ping Tung Eggplant",
    "Jalapeño Hot Pepper": "Jalapeño",
    "Seminole Pumpkin": "Seminole Pumpkin",
    "Roselle, Thai Red": "Thai Red Roselle",
    "Roselle, St. Kitts and Nevis": "Roselle St. Kitts & Nevis",
    "Everglades Cherry Tomato": "Everglades",
}


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)

    owner_id = session.execute(
        sa.text("SELECT id FROM users WHERE email = :email"),
        {"email": OWNER_EMAIL},
    ).scalar_one_or_none()
    if owner_id is None:
        raise RuntimeError(
            f"No user found with email {OWNER_EMAIL!r}; refusing to seed varieties "
            "without a target owner. Update OWNER_EMAIL in this migration and re-run."
        )

    # Categories: insert any that don't already exist (name is globally unique).
    cat_ids: dict[str, int] = {}
    for cat in NEW_CATEGORIES:
        existing_id = session.execute(
            sa.text("SELECT id FROM categories WHERE name = :name"),
            {"name": cat["name"]},
        ).scalar_one_or_none()
        if existing_id is not None:
            cat_ids[cat["name"]] = existing_id
            continue
        result = session.execute(
            categories.insert().values(**cat).returning(categories.c.id)
        )
        cat_ids[cat["name"]] = result.scalar_one()

    # Resolve ids for existing categories referenced by NEW_VARIETIES that
    # weren't just created above.
    needed_cat_names = {v[0] for v in NEW_VARIETIES} - set(cat_ids)
    if needed_cat_names:
        rows = session.execute(
            sa.text("SELECT id, name FROM categories WHERE name IN :names").bindparams(
                sa.bindparam("names", expanding=True)
            ),
            {"names": list(needed_cat_names)},
        ).all()
        found = {name: cid for cid, name in rows}
        missing = needed_cat_names - set(found)
        if missing:
            raise RuntimeError(f"Categories not found and not newly created: {sorted(missing)}")
        cat_ids.update(found)

    # Varieties: skip any name that already exists for this owner.
    existing_names = {
        row[0]
        for row in session.execute(
            sa.text("SELECT name FROM varieties WHERE user_id = :uid"),
            {"uid": owner_id},
        ).all()
    }

    inserted = 0
    skipped = 0
    for (cat_name, name, dg_min, dg_max, dh_min, dh_max, spacing, climbing,
         method, depth, sun, notes, ssd) in NEW_VARIETIES:
        if name in existing_names:
            skipped += 1
            continue
        session.execute(
            varieties.insert().values(
                user_id=owner_id,
                category_id=cat_ids[cat_name],
                name=name,
                days_to_germination_min=dg_min,
                days_to_germination_max=dg_max,
                days_to_harvest_min=dh_min,
                days_to_harvest_max=dh_max,
                seed_start_days=ssd,
                planting_depth=depth,
                spacing=spacing,
                sunlight=sun,
                is_climbing=climbing,
                planting_method=method,
                notes=notes,
            )
        )
        inserted += 1

    print(f"  Inserted {inserted} varieties, skipped {skipped} already present "
          f"(plus {len(SKIPPED_AS_DUPLICATE_OF)} omitted as near-duplicates of the starter catalog)")

    session.commit()


def downgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)

    owner_id = session.execute(
        sa.text("SELECT id FROM users WHERE email = :email"),
        {"email": OWNER_EMAIL},
    ).scalar_one_or_none()
    if owner_id is None:
        return

    # Match on name + harvest range + spacing (not name alone) so we only
    # remove rows this migration actually inserted, not a pre-existing
    # variety of the owner's that happens to share a name with one of ours.
    for (cat_name, name, dg_min, dg_max, dh_min, dh_max, spacing, climbing,
         method, depth, sun, notes, ssd) in NEW_VARIETIES:
        session.execute(
            sa.text(
                "DELETE FROM varieties WHERE user_id = :uid AND name = :name "
                "AND days_to_harvest_min = :dh_min AND days_to_harvest_max = :dh_max "
                "AND spacing = :spacing"
            ),
            {"uid": owner_id, "name": name, "dh_min": dh_min, "dh_max": dh_max, "spacing": spacing},
        )

    # Deliberately leave categories alone: this migration can't tell, from a
    # separate downgrade run, whether a NEW_CATEGORIES row it finds now was
    # created by this migration's upgrade() or already existed for an
    # unrelated reason (categories are global, not owner-scoped). An empty
    # leftover category is harmless; deleting a pre-existing one on a name
    # coincidence is not.

    session.commit()
