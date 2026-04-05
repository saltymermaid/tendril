"""Dev environment seeder for Tendril.

Seeds a minimal but representative garden for local development and testing:
- 1 × 5×5 grid bed with trellis, cage, and stake supports
- 1 × tower (7 levels × 6 pockets)
- Successive plantings on the same square (completed → in_progress)
- One 2×2 multi-square planting
- A mix of statuses and planting methods

Run with: docker compose exec backend python -m scripts.seed_dev
"""

import asyncio
from datetime import date, timedelta

from app.database import async_session
from app.models import Container, Event, JournalNote, Planting, SquareSupport
from scripts.seed_reference import seed_reference

TODAY = date.today()


async def seed_database():
    """Seed the dev database with reference data and sample garden data."""
    async with async_session() as session:
        print("Seeding reference data...")
        user, cat_map, var_map = await seed_reference(
            session,
            email="dev@tendril.garden",
            name="Dev User",
        )

        # ── Containers ────────────────────────────────────────────────────────
        bed = Container(
            user_id=user.id,
            name="Test Bed",
            type="grid_bed",
            location_description="Back yard",
            width=5,
            height=5,
            irrigation_type="drip",
            irrigation_duration_minutes=30,
            irrigation_frequency="daily",
        )
        session.add(bed)

        tower = Container(
            user_id=user.id,
            name="Test Tower",
            type="tower",
            location_description="Patio",
            levels=7,
            pockets_per_level=6,
            irrigation_type="drip",
            irrigation_duration_minutes=15,
            irrigation_frequency="2x_daily",
        )
        session.add(tower)
        await session.flush()
        print("  Created 2 containers (Test Bed 5×5, Test Tower 7×6)")

        # ── Support structures ────────────────────────────────────────────────
        # Grid convention: Row A=y=0 … E=y=4 / Col 1=x=0 … 5=x=4
        # Trellis on the entire E row (south side, y=4)
        supports = [
            (0, 4, "trellis"),
            (1, 4, "trellis"),
            (2, 4, "trellis"),
            (3, 4, "trellis"),
            (4, 4, "trellis"),
            # Cage at B2 (x=1, y=1)
            (1, 1, "cage"),
            # Stake at D3 (x=2, y=3)
            (2, 3, "stake"),
        ]
        for sx, sy, stype in supports:
            session.add(SquareSupport(
                container_id=bed.id,
                square_x=sx, square_y=sy, support_type=stype,
            ))
        await session.flush()
        print(f"  Created {len(supports)} support structures")

        # ── Helper ────────────────────────────────────────────────────────────
        def planting(cont_id, var_name, x, y, w, h,
                     start_date, end_date, status, method, qty,
                     tower_level=None, removal_reason=None):
            return Planting(
                user_id=user.id,
                container_id=cont_id,
                variety_id=var_map[var_name].id,
                square_x=x, square_y=y,
                square_width=w, square_height=h,
                tower_level=tower_level,
                start_date=start_date,
                end_date=end_date,
                status=status,
                planting_method=method,
                quantity=qty,
                removal_reason=removal_reason,
            )

        planting_list: list[Planting] = []

        # ── BED plantings ─────────────────────────────────────────────────────
        #
        # A1: Succession — completed Watermelon Radish, then current Chives
        #   (demonstrates successive plantings on the same square)
        p_radish = planting(
            bed.id, "Watermelon Radish", 0, 0, 1, 1,
            start_date=TODAY - timedelta(days=70),
            end_date=TODAY - timedelta(days=10),
            status="complete",
            method="direct_sow",
            qty=9,
        )
        planting_list.append(p_radish)

        p_chives = planting(
            bed.id, "Chives", 0, 0, 1, 1,
            start_date=TODAY - timedelta(days=9),
            end_date=TODAY + timedelta(days=81),
            status="in_progress",
            method="direct_sow",
            qty=9,
        )
        planting_list.append(p_chives)

        # A2: Single in-progress tomato
        p_tomato = planting(
            bed.id, "Golden Jubilee", 1, 0, 1, 1,
            start_date=TODAY - timedelta(days=30),
            end_date=TODAY + timedelta(days=50),
            status="in_progress",
            method="transplant",
            qty=1,
        )
        planting_list.append(p_tomato)

        # A3: Planned (not started) jalapeño
        p_pepper = planting(
            bed.id, "Jalapeño", 2, 0, 1, 1,
            start_date=TODAY + timedelta(days=7),
            end_date=TODAY + timedelta(days=87),
            status="not_started",
            method="transplant",
            qty=1,
        )
        planting_list.append(p_pepper)

        # A4: In-progress marigold (cage square)
        p_marigold_a4 = planting(
            bed.id, "Marigold", 3, 0, 1, 1,
            start_date=TODAY - timedelta(days=20),
            end_date=TODAY + timedelta(days=40),
            status="in_progress",
            method="direct_sow",
            qty=3,
        )
        planting_list.append(p_marigold_a4)

        # A5: Basil
        p_basil = planting(
            bed.id, "Italian Large Leaf Basil", 4, 0, 1, 1,
            start_date=TODAY - timedelta(days=15),
            end_date=TODAY + timedelta(days=45),
            status="in_progress",
            method="transplant",
            qty=2,
        )
        planting_list.append(p_basil)

        # B2: 2×2 multi-square Thai Red Roselle (occupies B2/B3/C2/C3 → x=1,y=1,w=2,h=2)
        p_roselle = planting(
            bed.id, "Thai Red Roselle", 1, 1, 2, 2,
            start_date=TODAY - timedelta(days=10),
            end_date=TODAY + timedelta(days=140),
            status="in_progress",
            method="direct_sow",
            qty=1,
        )
        planting_list.append(p_roselle)

        # B1: Beans (will succeed after completion — currently planned)
        p_beans = planting(
            bed.id, "Royal Burgundy Bush", 0, 1, 1, 1,
            start_date=TODAY - timedelta(days=14),
            end_date=TODAY + timedelta(days=46),
            status="in_progress",
            method="direct_sow",
            qty=9,
        )
        planting_list.append(p_beans)

        # D1: Parsley (stake square)
        p_parsley = planting(
            bed.id, "Parsley", 0, 3, 1, 1,
            start_date=TODAY - timedelta(days=25),
            end_date=TODAY + timedelta(days=65),
            status="in_progress",
            method="direct_sow",
            qty=6,
        )
        planting_list.append(p_parsley)

        # D3: Sweet Banana Pepper at the stake square
        p_pepper_stake = planting(
            bed.id, "Sweet Banana Pepper", 2, 3, 1, 1,
            start_date=TODAY - timedelta(days=22),
            end_date=TODAY + timedelta(days=53),
            status="in_progress",
            method="transplant",
            qty=1,
        )
        planting_list.append(p_pepper_stake)

        # E row (trellis): climbing varieties
        trellis_plantings = [
            ("Seminole Pumpkin",       0, 4),
            ("PR Black Bean (vining)", 1, 4),
            ("Butterfly Pea",          2, 4),
            ("Loofah",                 3, 4),
            ("Silver-line Melon",      4, 4),
        ]
        for var_name, x, y in trellis_plantings:
            planting_list.append(planting(
                bed.id, var_name, x, y, 1, 1,
                start_date=TODAY - timedelta(days=5),
                end_date=TODAY + timedelta(days=95),
                status="in_progress",
                method="direct_sow",
                qty=1,
            ))

        # ── Add all bed plantings ─────────────────────────────────────────────
        for p in planting_list:
            session.add(p)
        await session.flush()

        # ── TOWER plantings ───────────────────────────────────────────────────
        # tower_level is 0-indexed (0 = top / Level 1 in UI)
        # square_x is pocket index (0-indexed)
        tower_date = TODAY - timedelta(days=7)
        tower_levels = [
            (0, "Naughty Marietta Marigold"),        # Level 1 (top)
            (1, "Nasturtium (Jewel Mixed Colors)"),  # Level 2
            (2, "Marigold (French Double Dwarf)"),   # Level 3
            (3, "Zinnia (Pinwheel Mixed Colors)"),   # Level 4
            (4, "French Red Cherry Marigold"),       # Level 5
            (5, "Naughty Marietta Marigold"),        # Level 6
            (6, "Nasturtium (Jewel Mixed Colors)"),  # Level 7 (bottom)
        ]
        tower_plantings: list[Planting] = []
        for level_idx, var_name in tower_levels:
            variety = var_map[var_name]
            end_days = variety.days_to_harvest_max or 60
            for pocket in range(6):
                p = Planting(
                    user_id=user.id,
                    container_id=tower.id,
                    variety_id=variety.id,
                    square_x=pocket, square_y=0, square_width=1, square_height=1,
                    tower_level=level_idx,
                    start_date=tower_date,
                    end_date=tower_date + timedelta(days=end_days),
                    status="in_progress",
                    planting_method=variety.planting_method,
                    quantity=1,
                )
                session.add(p)
                tower_plantings.append(p)
        await session.flush()
        print(f"  Created {len(planting_list) + len(tower_plantings)} plantings"
              f" ({len(planting_list)} bed, {len(tower_plantings)} tower)")

        # ── Events ────────────────────────────────────────────────────────────
        event_count = 0
        # Planting events for in-progress and complete bed plantings
        for p in planting_list:
            if p.status == "not_started":
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

        # Harvest event for the completed radish
        session.add(Event(
            user_id=user.id,
            container_id=bed.id,
            planting_id=p_radish.id,
            variety_id=p_radish.variety_id,
            event_type="harvest",
            date=p_radish.end_date,
            quantity=9,
            square_x=0, square_y=0,
            notes="Full harvest of Watermelon Radish",
        ))
        event_count += 1

        # Tower planting events
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
                notes=f"Seeded level {p.tower_level + 1} pocket {p.square_x + 1}",
            ))
            event_count += 1

        await session.flush()
        print(f"  Created {event_count} events")

        # ── Journal notes ─────────────────────────────────────────────────────
        session.add(JournalNote(
            user_id=user.id,
            container_id=bed.id,
            content="Test Bed looking good. Roselle taking up the 2×2 in the B/C center. Trellis row planted with climbers. Radishes finished and chives are in.",
            date=TODAY - timedelta(days=5),
        ))
        session.add(JournalNote(
            user_id=user.id,
            container_id=tower.id,
            content="Seeded all 7 tower levels with flowers. Marigolds, nasturtiums, and zinnias alternating. Should fill in nicely.",
            date=tower_date,
        ))
        await session.flush()
        print("  Created 2 journal notes")

        await session.commit()
        print("\nDev seed complete!")


async def main():
    """Run the dev seed script."""
    print("Seeding Tendril dev database...")
    await seed_database()


if __name__ == "__main__":
    asyncio.run(main())
