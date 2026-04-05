"""Production initial seed for Tendril — run ONCE on first deployment.

Seeds the real garden state as of early April 2026:
  Beds 1–3      planted 2026-03-15
  Rolling Bed   planted 2026-03-20
  Tower         planted 2026-03-25
  Beds 4–6      planted 2026-04-03

Each planting row has its own explicit start_date and end_date so you can
edit individual rows before running without touching any shared logic.

Run with:
  docker compose -f docker-compose.prod.yml run --rm backend \
      python -m scripts.seed_production
"""

import asyncio
import os
from datetime import date

from app.database import async_session
from app.models import Container, Event, JournalNote, Planting, SquareSupport
from scripts.seed_reference import seed_reference


async def seed_database():
    """Seed the production database with reference data and real garden state."""
    # Read the primary allowed email from the environment variable.
    # ALLOWED_EMAILS is set in docker-compose.prod.yml from the .env file.
    allowed_emails_raw = os.environ.get("ALLOWED_EMAILS", "")
    owner_email = allowed_emails_raw.split(",")[0].strip() if allowed_emails_raw else "admin@tendril.garden"
    owner_name = owner_email.split("@")[0].replace(".", " ").title()

    print(f"Seeding reference data for owner: {owner_email}")

    async with async_session() as session:
        print("Seeding reference data...")
        user, cat_map, var_map = await seed_reference(
            session,
            email=owner_email,
            name=owner_name,
        )

        # ── Containers ────────────────────────────────────────────────────────
        containers_data = [
            # Original 4×4 beds — North fence
            {"name": "Bed 1", "type": "grid_bed", "location_description": "North fence",
             "width": 4, "height": 4, "irrigation_type": "drip",
             "irrigation_duration_minutes": 30, "irrigation_frequency": "daily"},
            {"name": "Bed 2", "type": "grid_bed", "location_description": "North fence",
             "width": 4, "height": 4, "irrigation_type": "drip",
             "irrigation_duration_minutes": 30, "irrigation_frequency": "daily"},
            {"name": "Bed 3", "type": "grid_bed", "location_description": "North fence",
             "width": 4, "height": 4, "irrigation_type": "drip",
             "irrigation_duration_minutes": 30, "irrigation_frequency": "daily"},
            # New 5×5 beds — Back yard west
            {"name": "Bed 4", "type": "grid_bed", "location_description": "Back yard - west",
             "width": 5, "height": 5, "irrigation_type": "drip",
             "irrigation_duration_minutes": 30, "irrigation_frequency": "daily"},
            {"name": "Bed 5", "type": "grid_bed", "location_description": "Back yard - west",
             "width": 5, "height": 5, "irrigation_type": "drip",
             "irrigation_duration_minutes": 30, "irrigation_frequency": "daily"},
            {"name": "Bed 6", "type": "grid_bed", "location_description": "Back yard - west",
             "width": 5, "height": 5, "irrigation_type": "drip",
             "irrigation_duration_minutes": 30, "irrigation_frequency": "daily"},
            # Rolling bed — North fence
            {"name": "Rolling Bed", "type": "grid_bed", "location_description": "North fence",
             "width": 2, "height": 4, "irrigation_type": "manual",
             "irrigation_duration_minutes": 10, "irrigation_frequency": "daily"},
        ]
        cont_map: dict[str, Container] = {}
        for c_data in containers_data:
            c = Container(user_id=user.id, **c_data)
            session.add(c)
            await session.flush()
            cont_map[c.name] = c

        tower = Container(
            user_id=user.id,
            name="Tower",
            type="tower",
            location_description="Patio, near kitchen door",
            levels=7,
            pockets_per_level=6,
            irrigation_type="drip",
            irrigation_duration_minutes=15,
            irrigation_frequency="2x_daily",
        )
        session.add(tower)
        await session.flush()
        cont_map["Tower"] = tower
        print(f"  Created {len(cont_map)} containers")

        # ── Support structures ────────────────────────────────────────────────
        # Grid convention: Row A=y=0 … E=y=4 / Col 1=x=0 … 5=x=4
        support_data = [
            # Bed 2 — cages
            ("Bed 2", 1, 1, "cage"),
            ("Bed 2", 2, 2, "cage"),
            # Bed 4 — E row (y=4) trellis
            ("Bed 4", 0, 4, "trellis"), ("Bed 4", 1, 4, "trellis"), ("Bed 4", 2, 4, "trellis"),
            ("Bed 4", 3, 4, "trellis"), ("Bed 4", 4, 4, "trellis"),
            # Bed 5 — A row (y=0) and E row (y=4) trellis
            ("Bed 5", 0, 0, "trellis"), ("Bed 5", 1, 0, "trellis"), ("Bed 5", 2, 0, "trellis"),
            ("Bed 5", 3, 0, "trellis"), ("Bed 5", 4, 0, "trellis"),
            ("Bed 5", 0, 4, "trellis"), ("Bed 5", 1, 4, "trellis"), ("Bed 5", 2, 4, "trellis"),
            ("Bed 5", 3, 4, "trellis"), ("Bed 5", 4, 4, "trellis"),
            # Bed 6 — A row (y=0) and E row (y=4) trellis; stake at D3 (x=2, y=3)
            ("Bed 6", 0, 0, "trellis"), ("Bed 6", 1, 0, "trellis"), ("Bed 6", 2, 0, "trellis"),
            ("Bed 6", 3, 0, "trellis"), ("Bed 6", 4, 0, "trellis"),
            ("Bed 6", 0, 4, "trellis"), ("Bed 6", 1, 4, "trellis"), ("Bed 6", 2, 4, "trellis"),
            ("Bed 6", 3, 4, "trellis"), ("Bed 6", 4, 4, "trellis"),
            ("Bed 6", 2, 3, "stake"),
            # Rolling Bed — cages
            ("Rolling Bed", 0, 0, "cage"), ("Rolling Bed", 1, 0, "cage"),
        ]
        for cont_name, sx, sy, stype in support_data:
            session.add(SquareSupport(
                container_id=cont_map[cont_name].id,
                square_x=sx, square_y=sy, support_type=stype,
            ))
        await session.flush()
        print(f"  Created {len(support_data)} support structures")

        # ── Planting helper ───────────────────────────────────────────────────
        all_plantings: list[Planting] = []

        def add_p(cont_name, var_name, x, y, w, h,
                  start_date, end_date, status, method, qty,
                  tower_level=None):
            p = Planting(
                user_id=user.id,
                container_id=cont_map[cont_name].id,
                variety_id=var_map[var_name].id,
                square_x=x, square_y=y,
                square_width=w, square_height=h,
                tower_level=tower_level,
                start_date=start_date,
                end_date=end_date,
                status=status,
                planting_method=method,
                quantity=qty,
            )
            all_plantings.append(p)
            return p

        # ── BED 1 (4×4, North fence) — transplanted 2026-03-15 ───────────────
        # (var_name, x, y, w, h, start_date, end_date, status, method, qty)
        add_p("Bed 1", "Golden Jubilee",           0, 0, 2, 2, date(2026, 3, 15), date(2026, 6,  3), "in_progress", "transplant", 1)
        add_p("Bed 1", "Husky Cherry Red",          0, 2, 2, 2, date(2026, 3, 15), date(2026, 5, 24), "in_progress", "transplant", 1)
        add_p("Bed 1", "Poblano",                   2, 0, 1, 1, date(2026, 3, 15), date(2026, 6,  3), "in_progress", "transplant", 1)
        add_p("Bed 1", "Cubanelle",                 3, 0, 1, 1, date(2026, 3, 15), date(2026, 5, 29), "in_progress", "transplant", 1)
        add_p("Bed 1", "Orange Sweet",              2, 1, 1, 1, date(2026, 3, 15), date(2026, 6,  8), "in_progress", "transplant", 1)
        add_p("Bed 1", "Jalapeño",                  3, 1, 1, 1, date(2026, 3, 15), date(2026, 6,  3), "in_progress", "transplant", 1)
        add_p("Bed 1", "Clemson Spineless 80",      2, 2, 1, 1, date(2026, 4, 4), date(2026, 6, 7), "in_progress", "direct_sow", 1)
        add_p("Bed 1", "Italian Large Leaf Basil",  3, 2, 1, 1, date(2026, 3, 15), date(2026, 5, 14), "in_progress", "transplant", 1)
        add_p("Bed 1", "Marigold",                  2, 3, 1, 1, date(2026, 3, 15), date(2026, 5, 14), "in_progress", "transplant", 1)
        add_p("Bed 1", "Little Fingers Eggplant",   3, 3, 1, 1, date(2026, 4, 2), date(2026, 6, 22), "in_progress", "transplant", 1)

        # ── BED 2 (4×4, North fence) — direct sowed 2026-03-15 ───────────────
        add_p("Bed 2", "Garden Bush Slicer",     0, 0, 1, 1, date(2026, 3, 15), date(2026, 5, 19), "in_progress", "direct_sow", 3)
        add_p("Bed 2", "Garden Bush Slicer",     1, 0, 1, 1, date(2026, 3, 15), date(2026, 5, 19), "in_progress", "direct_sow", 3)
        add_p("Bed 2", "Garden Bush Slicer",     0, 1, 1, 1, date(2026, 3, 15), date(2026, 5, 19), "in_progress", "direct_sow", 3)
        add_p("Bed 2", "Garden Bush Slicer",     1, 1, 1, 1, date(2026, 3, 15), date(2026, 5, 19), "in_progress", "direct_sow", 3)
        add_p("Bed 2", "Double Yield Pickling",  2, 0, 1, 1, date(2026, 3, 15), date(2026, 5, 14), "in_progress", "direct_sow", 3)
        add_p("Bed 2", "Double Yield Pickling",  3, 0, 1, 1, date(2026, 3, 15), date(2026, 5, 14), "in_progress", "direct_sow", 3)
        add_p("Bed 2", "Double Yield Pickling",  2, 1, 1, 1, date(2026, 3, 15), date(2026, 5, 14), "in_progress", "direct_sow", 3)
        add_p("Bed 2", "Double Yield Pickling",  3, 1, 1, 1, date(2026, 3, 15), date(2026, 5, 14), "in_progress", "direct_sow", 3)
        add_p("Bed 2", "Crookneck",              0, 2, 2, 2, date(2026, 3, 15), date(2026, 5, 14), "in_progress", "direct_sow", 2)
        add_p("Bed 2", "Easy Pick Gold Zucchini", 2, 2, 2, 2, date(2026, 3, 15), date(2026, 5,  9), "in_progress", "direct_sow", 2)

        # ── BED 3 (4×4, North fence) — mixed dates 2026-03-15 ────────────────
        add_p("Bed 3", "Rosemary",                 0, 0, 1, 1, date(2026, 3, 15), date(2026, 6, 13), "in_progress", "transplant",  1)
        add_p("Bed 3", "English Thyme",             1, 0, 1, 1, date(2026, 3, 15), date(2026, 6,  3), "in_progress", "transplant",  1)
        add_p("Bed 3", "Chives",                    2, 0, 1, 1, date(2026, 3, 15), date(2026, 6, 13), "in_progress", "direct_sow",  9)
        # A4 empty
        add_p("Bed 3", "Italian Large Leaf Basil",  0, 1, 1, 1, date(2026, 3, 15), date(2026, 5, 14), "in_progress", "transplant",  3)
        add_p("Bed 3", "Slow-Bolt Cilantro",        1, 1, 1, 1, date(2026, 3, 15), date(2026, 5,  9), "in_progress", "direct_sow",  6)
        add_p("Bed 3", "Slow-Bolt Cilantro",        2, 1, 1, 1, date(2026, 3, 15), date(2026, 5,  9), "in_progress", "direct_sow",  6)
        add_p("Bed 3", "Bouquet Dill",              3, 1, 1, 1, date(2026, 3, 15), date(2026, 5, 24), "in_progress", "direct_sow",  4)
        add_p("Bed 3", "Royal Burgundy Bush",       0, 2, 1, 1, date(2026, 3, 15), date(2026, 5, 14), "in_progress", "direct_sow",  9)
        add_p("Bed 3", "Royal Burgundy Bush",       1, 2, 1, 1, date(2026, 3, 15), date(2026, 5, 14), "in_progress", "direct_sow",  9)
        add_p("Bed 3", "Bush Cantare",              2, 2, 1, 1, date(2026, 3, 15), date(2026, 5,  9), "in_progress", "direct_sow",  9)
        add_p("Bed 3", "Bush Cantare",              3, 2, 1, 1, date(2026, 3, 15), date(2026, 5,  9), "in_progress", "direct_sow",  9)
        add_p("Bed 3", "Watermelon Radish",         0, 3, 1, 1, date(2026, 3, 15), date(2026, 5, 19), "in_progress", "direct_sow",  16)
        add_p("Bed 3", "Marigold",                  1, 3, 1, 1, date(2026, 3, 15), date(2026, 5, 14), "in_progress", "direct_sow",  4)
        add_p("Bed 3", "Marigold",                  2, 3, 1, 1, date(2026, 3, 15), date(2026, 5, 14), "in_progress", "direct_sow",  4)
        add_p("Bed 3", "Bouquet Dill",              3, 3, 1, 1, date(2026, 3, 15), date(2026, 5, 24), "in_progress", "direct_sow",  4)

        # ── ROLLING BED (2×4, North fence) — transplanted/sowed 2026-03-20 ───
        add_p("Rolling Bed", "Blue Lake Bush",  0, 0, 1, 1, date(2026, 3, 20), date(2026, 5, 19), "in_progress", "direct_sow", 9)
        add_p("Rolling Bed", "Beauregard",      1, 0, 1, 1, date(2026, 3, 20), date(2026, 7, 18), "in_progress", "transplant", 1)
        add_p("Rolling Bed", "Blue Lake Bush",  0, 1, 1, 1, date(2026, 3, 20), date(2026, 5, 19), "in_progress", "direct_sow", 9)
        add_p("Rolling Bed", "Beauregard",      1, 1, 1, 1, date(2026, 3, 20), date(2026, 7, 18), "in_progress", "transplant", 1)
        add_p("Rolling Bed", "Warrior",         0, 2, 1, 1, date(2026, 3, 20), date(2026, 5, 29), "in_progress", "direct_sow", 16)
        add_p("Rolling Bed", "Beauregard",      1, 2, 1, 1, date(2026, 3, 20), date(2026, 7, 18), "in_progress", "transplant", 1)
        add_p("Rolling Bed", "Warrior",       0, 3, 1, 1, date(2026, 3, 20), date(2026, 5, 29), "in_progress", "direct_sow", 16)
        add_p("Rolling Bed", "Beauregard",      1, 3, 1, 1, date(2026, 3, 20), date(2026, 7, 18), "in_progress", "transplant", 1)

        # ── BED 4 (5×5, Back yard west) — direct sowed 2026-04-03 ────────────
        # (var_name, x, y, w, h, start_date, end_date, status, method, qty)
        add_p("Bed 4", "Chives",                   0, 0, 1, 1, date(2026, 4, 3), date(2026, 7,  2), "in_progress", "direct_sow", 9)
        add_p("Bed 4", "Thai Red Roselle",          1, 0, 2, 2, date(2026, 4, 3), date(2026, 8, 31), "in_progress", "direct_sow", 1)  # A2/A3/B2/B3
        add_p("Bed 4", "Red Burgundy",              3, 0, 1, 1, date(2026, 4, 4), date(2026, 6,  8), "in_progress", "direct_sow", 1)
        add_p("Bed 4", "Queen Sophia Marigold",     4, 0, 1, 1, date(2026, 4, 3), date(2026, 6,  2), "in_progress", "direct_sow", 1)
        add_p("Bed 4", "Midnight Bean",             0, 1, 1, 1, date(2026, 4, 3), date(2026, 6,  7), "in_progress", "direct_sow", 9)
        add_p("Bed 4", "Parsley",                   3, 1, 1, 1, date(2026, 4, 3), date(2026, 7,  2), "in_progress", "direct_sow", 9)
        add_p("Bed 4", "Midnight Bean",             4, 1, 1, 1, date(2026, 4, 3), date(2026, 6,  7), "in_progress", "direct_sow", 9)
        add_p("Bed 4", "Naughty Marietta Marigold", 0, 2, 1, 1, date(2026, 4, 3), date(2026, 6,  2), "in_progress", "direct_sow", 1)
        add_p("Bed 4", "Clemson Spineless 80",      1, 2, 1, 1, date(2026, 4, 4), date(2026, 6,  8), "in_progress", "direct_sow", 1)
        add_p("Bed 4", "Green Basil",               2, 2, 1, 1, date(2026, 4, 3), date(2026, 6,  2), "in_progress", "direct_sow", 4)
        add_p("Bed 4", "Midnight Bean",             3, 2, 1, 1, date(2026, 4, 3), date(2026, 6,  7), "in_progress", "direct_sow", 9)
        add_p("Bed 4", "Chives",                    4, 2, 1, 1, date(2026, 4, 3), date(2026, 7,  2), "in_progress", "direct_sow", 9)
        add_p("Bed 4", "Midnight Bean",             0, 3, 1, 1, date(2026, 4, 3), date(2026, 6,  7), "in_progress", "direct_sow", 9)
        add_p("Bed 4", "Purple Basil",              1, 3, 1, 1, date(2026, 4, 3), date(2026, 6,  2), "in_progress", "direct_sow", 4)
        add_p("Bed 4", "French Red Cherry Marigold", 2, 3, 1, 1, date(2026, 4, 3), date(2026, 6,  2), "in_progress", "direct_sow", 1)
        add_p("Bed 4", "Purple Basil",               3, 3, 1, 1, date(2026, 4, 3), date(2026, 6,  2), "in_progress", "direct_sow", 4)
        add_p("Bed 4", "Midnight Bean",             4, 3, 1, 1, date(2026, 4, 3), date(2026, 6,  7), "in_progress", "direct_sow", 9)
        add_p("Bed 4", "White Everglades Tomato",   0, 4, 1, 1, date(2026, 4, 3), date(2026, 6, 17), "in_progress", "direct_sow", 1)
        add_p("Bed 4", "Butterfly Pea",             1, 4, 1, 1, date(2026, 4, 4), date(2026, 7,  3), "in_progress", "direct_sow", 3)
        add_p("Bed 4", "Seminole Pumpkin",          2, 4, 1, 1, date(2026, 4, 3), date(2026, 7, 12), "in_progress", "direct_sow", 1)
        add_p("Bed 4", "Loofah",                    3, 4, 1, 1, date(2026, 4, 3), date(2026, 8,  1), "in_progress", "direct_sow", 1)
        add_p("Bed 4", "Silver-line Melon",         4, 4, 1, 1, date(2026, 4, 3), date(2026, 6, 27), "in_progress", "direct_sow", 1)

        # ── BED 5 (5×5, Back yard west) — direct sowed 2026-04-03 ────────────
        add_p("Bed 5", "Seminole Pumpkin",          0, 0, 1, 1, date(2026, 4, 3), date(2026, 7, 12), "in_progress", "direct_sow", 1)
        add_p("Bed 5", "PR Black Bean (vining)",    1, 0, 1, 1, date(2026, 4, 4), date(2026, 6, 27), "in_progress", "direct_sow", 1)
        add_p("Bed 5", "Butterfly Pea",             2, 0, 1, 1, date(2026, 4, 4), date(2026, 7,  2), "in_progress", "direct_sow", 3)
        add_p("Bed 5", "White Everglades Tomato",   3, 0, 1, 1, date(2026, 4, 3), date(2026, 6, 17), "in_progress", "direct_sow", 1)
        add_p("Bed 5", "PR Black Bean (vining)",    4, 0, 1, 1, date(2026, 4, 4), date(2026, 6, 27), "in_progress", "direct_sow", 1)
        add_p("Bed 5", "Midnight Bean",             0, 1, 1, 1, date(2026, 4, 4), date(2026, 6,  7), "in_progress", "direct_sow", 1)
        add_p("Bed 5", "Roselle St. Kitts & Nevis", 1, 1, 2, 2, date(2026, 4, 3), date(2026, 8, 31), "in_progress", "direct_sow", 1)  # B2/B3/C2/C3
        add_p("Bed 5", "Lisbon Bunching Onion",     3, 1, 1, 1, date(2026, 4, 4), date(2026, 6, 12), "in_progress", "direct_sow", 9)
        add_p("Bed 5", "Queen Sophia Marigold",     4, 1, 1, 1, date(2026, 4, 3), date(2026, 6,  2), "in_progress", "direct_sow", 1)
        add_p("Bed 5", "Red Burgundy",              0, 2, 1, 1, date(2026, 4, 3), date(2026, 6,  7), "in_progress", "direct_sow", 9)
        add_p("Bed 5", "Rosa Bianca Eggplant",      3, 2, 1, 1, date(2026, 4, 3), date(2026, 6, 22), "in_progress", "transplant", 1)
        add_p("Bed 5", "Oregano",                   4, 2, 1, 1, date(2026, 4, 3), date(2026, 7,  2), "in_progress", "direct_sow", 1)
        add_p("Bed 5", "Chives",                    0, 3, 1, 1, date(2026, 4, 3), date(2026, 7,  2), "in_progress", "direct_sow", 9)
        add_p("Bed 5", "Ping Tung Eggplant",        1, 3, 1, 1, date(2026, 4, 3), date(2026, 6, 22), "in_progress", "direct_sow", 1)
        add_p("Bed 5", "French Red Cherry Marigold", 2, 3, 1, 1, date(2026, 4, 3), date(2026, 6,  2), "in_progress", "direct_sow", 1)
        add_p("Bed 5", "Midnight Bean",             3, 3, 1, 1, date(2026, 4, 3), date(2026, 6,  7), "in_progress", "direct_sow", 9)
        add_p("Bed 5", "Warrior",                   4, 3, 1, 1, date(2026, 4, 4), date(2026, 6, 12), "in_progress", "direct_sow", 9)
        add_p("Bed 5", "Butterfly Pea",             0, 4, 1, 1, date(2026, 4, 4), date(2026, 7,  2), "in_progress", "direct_sow", 3)
        add_p("Bed 5", "Red Everglades Tomato",     1, 4, 1, 1, date(2026, 4, 3), date(2026, 6, 17), "in_progress", "direct_sow", 1)
        add_p("Bed 5", "Silver-line Melon",         2, 4, 1, 1, date(2026, 4, 3), date(2026, 6, 27), "in_progress", "direct_sow", 1)
        add_p("Bed 5", "Seminole Pumpkin",          3, 4, 1, 1, date(2026, 4, 3), date(2026, 7, 12), "in_progress", "direct_sow", 1)
        add_p("Bed 5", "Loofah",                    4, 4, 1, 1, date(2026, 4, 3), date(2026, 8,  1), "in_progress", "direct_sow", 1)

        # ── BED 6 (5×5, Back yard west) — mixed methods 2026-04-03 ───────────
        add_p("Bed 6", "Red Everglades Tomato",   0, 0, 1, 1, date(2026, 4, 3), date(2026, 6, 17), "in_progress", "direct_sow", 1)
        add_p("Bed 6", "Silver-line Melon",         1, 0, 1, 1, date(2026, 4, 3), date(2026, 6, 27), "in_progress", "direct_sow", 1)
        add_p("Bed 6", "PR Black Bean (vining)",    2, 0, 1, 1, date(2026, 4, 4), date(2026, 6, 27), "in_progress", "direct_sow", 1)
        add_p("Bed 6", "Seminole Pumpkin",          3, 0, 1, 1, date(2026, 4, 3), date(2026, 7, 12), "in_progress", "direct_sow", 1)
        add_p("Bed 6", "Butterfly Pea",             4, 0, 1, 1, date(2026, 4, 4), date(2026, 7,  2), "in_progress", "direct_sow", 3)
        add_p("Bed 6", "Lisbon Bunching Onion",     0, 1, 1, 1, date(2026, 4, 3), date(2026, 6, 12), "in_progress", "direct_sow", 9)
        add_p("Bed 6", "Cranberry Hibiscus",        1, 1, 2, 2, date(2026, 4, 4), date(2026, 8,  1), "in_progress", "direct_sow", 1)  # B2/B3/C2/C3
        add_p("Bed 6", "Clemson Spineless 80",      3, 1, 1, 1, date(2026, 4, 4), date(2026, 6,  7), "in_progress", "direct_sow", 1)
        add_p("Bed 6", "Parsley",                   4, 1, 1, 1, date(2026, 4, 4), date(2026, 7,  2), "in_progress", "direct_sow", 9)
        add_p("Bed 6", "Little Fingers Eggplant",   0, 2, 1, 1, date(2026, 4, 3), date(2026, 6, 22), "in_progress", "transplant", 1)
        add_p("Bed 6", "Naughty Marietta Marigold", 3, 2, 1, 1, date(2026, 4, 3), date(2026, 6,  2), "in_progress", "direct_sow", 1)
        add_p("Bed 6", "Midnight Bean",             4, 2, 1, 1, date(2026, 4, 3), date(2026, 6,  7), "in_progress", "direct_sow", 9)
        add_p("Bed 6", "Purple Basil",              0, 3, 1, 1, date(2026, 4, 4), date(2026, 6,  2), "in_progress", "direct_sow", 4)
        add_p("Bed 6", "Red Burgundy",            1, 3, 1, 1, date(2026, 4, 3), date(2026, 6,  7), "in_progress", "direct_sow", 1)
        add_p("Bed 6", "Sweet Banana Pepper",       2, 3, 1, 1, date(2026, 4, 3), date(2026, 6, 17), "in_progress", "transplant", 1)
        add_p("Bed 6", "Ping Tung Eggplant",        3, 3, 1, 1, date(2026, 4, 3), date(2026, 6, 22), "in_progress", "direct_sow", 1)
        add_p("Bed 6", "French Red Cherry Marigold", 4, 3, 1, 1, date(2026, 4, 3), date(2026, 6,  2), "in_progress", "direct_sow", 1)
        add_p("Bed 6", "Butterfly Pea",             0, 4, 1, 1, date(2026, 4, 4), date(2026, 7,  2), "in_progress", "direct_sow", 3)
        add_p("Bed 6", "Red Everglades Tomato",     1, 4, 1, 1, date(2026, 4, 3), date(2026, 6, 17), "in_progress", "direct_sow", 1)
        add_p("Bed 6", "Loofah",                    2, 4, 1, 1, date(2026, 4, 3), date(2026, 8,  1), "in_progress", "direct_sow", 1)
        add_p("Bed 6", "White Everglades Tomato",   3, 4, 1, 1, date(2026, 4, 3), date(2026, 6, 17), "in_progress", "direct_sow", 1)
        add_p("Bed 6", "PR Black Bean (vining)",    4, 4, 1, 1, date(2026, 4, 4), date(2026, 6, 27), "in_progress", "direct_sow", 1)

        # ── Flush all bed plantings ───────────────────────────────────────────
        for p in all_plantings:
            session.add(p)
        await session.flush()

        # ── TOWER (7 levels × 6 pockets) — seeded 2026-03-25 ─────────────────
        # tower_level is 0-indexed (0 = top / Level 1 in UI)
        # square_x is pocket index (0-indexed, 0 = Pocket 1 … 5 = Pocket 6)
        tower_levels = [
            (0, "Naughty Marietta Marigold",         date(2026, 3, 25), date(2026, 5, 24)),  # Level 1 (top)
            (1, "Nasturtium (Jewel Mixed Colors)",   date(2026, 3, 25), date(2026, 6,  3)),  # Level 2
            (2, "Marigold (French Double Dwarf)",    date(2026, 3, 25), date(2026, 5, 24)),  # Level 3
            (3, "Zinnia (Pinwheel Mixed Colors)",    date(2026, 3, 25), date(2026, 6,  8)),  # Level 4
            (4, "French Red Cherry Marigold",        date(2026, 3, 25), date(2026, 5, 24)),  # Level 5
            (5, "Naughty Marietta Marigold",         date(2026, 3, 25), date(2026, 5, 24)),  # Level 6
            (6, "Nasturtium (Jewel Mixed Colors)",   date(2026, 3, 25), date(2026, 6,  3)),  # Level 7 (bottom)
        ]
        tower_plantings: list[Planting] = []
        for level_idx, var_name, start_d, end_d in tower_levels:
            variety = var_map[var_name]
            for pocket in range(6):
                p = Planting(
                    user_id=user.id,
                    container_id=cont_map["Tower"].id,
                    variety_id=variety.id,
                    square_x=pocket, square_y=0, square_width=1, square_height=1,
                    tower_level=level_idx,
                    start_date=start_d,
                    end_date=end_d,
                    status="in_progress",
                    planting_method=variety.planting_method,
                    quantity=1,
                )
                session.add(p)
                tower_plantings.append(p)
        await session.flush()
        print(f"  Created {len(all_plantings) + len(tower_plantings)} plantings"
              f" ({len(all_plantings)} bed/rolling, {len(tower_plantings)} tower)")

        # ── Events ────────────────────────────────────────────────────────────
        event_count = 0

        # Planting events for all bed plantings
        for p in all_plantings:
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
        for p in tower_plantings:
            session.add(Event(
                user_id=user.id,
                container_id=p.container_id,
                planting_id=p.id,
                variety_id=p.variety_id,
                event_type="planting",
                date=p.start_date,
                quantity=1,
                square_x=p.square_x,
                square_y=0,
                tower_level=p.tower_level,
                notes=f"Seeded level {p.tower_level + 1} pocket {p.square_x + 1} via {p.planting_method}",
            ))
            event_count += 1

        await session.flush()
        print(f"  Created {event_count} events")

        # ── Journal notes ─────────────────────────────────────────────────────
        session.add(JournalNote(
            user_id=user.id,
            container_id=cont_map["Bed 1"].id,
            content="Tomatoes and peppers looking healthy. Golden Jubilee putting out new growth. Eggplant and basil are settling in nicely.",
            date=date(2026, 3, 20),
        ))
        session.add(JournalNote(
            user_id=user.id,
            container_id=cont_map["Bed 2"].id,
            content="Cucumbers are climbing well. Squash starting to spread — may need to train them. Picklers looking more vigorous than slicers.",
            date=date(2026, 3, 22),
        ))
        session.add(JournalNote(
            user_id=user.id,
            container_id=cont_map["Tower"].id,
            content="Seeded all 7 tower levels with flowers on March 25. Marigolds, nasturtiums, and zinnias. Should look beautiful once they fill in.",
            date=date(2026, 3, 25),
        ))
        session.add(JournalNote(
            user_id=user.id,
            content="Direct sowed Beds 4, 5, and 6 (new 5×5 beds, back yard west). Lots of tropical/heat-tolerant varieties for the season. Trellis rows for climbers.",
            date=date(2026, 4, 3),
        ))
        await session.flush()
        print("  Created 4 journal notes")

        await session.commit()
        print("\nProduction seed complete!")


async def main():
    """Run the production seed script."""
    print("Seeding Tendril production database...")
    await seed_database()


if __name__ == "__main__":
    asyncio.run(main())
