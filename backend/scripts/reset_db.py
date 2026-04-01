"""Database reset and reseed script.

Run with: docker compose exec backend python -m scripts.reset_db
"""

import asyncio

from sqlalchemy import text

from app.database import engine
from scripts.seed_data import seed_database


async def reset_database():
    """Drop all tables, run migrations, and reseed."""
    print("Resetting Tendril database...")

    # Drop all tables
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO tendril"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
    print("  Dropped all tables")

    # Run migrations
    import subprocess
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  Migration failed: {result.stderr}")
        return
    print("  Ran migrations")

    # Seed data
    await seed_database()
    print("\nDatabase reset complete!")


if __name__ == "__main__":
    asyncio.run(reset_database())
