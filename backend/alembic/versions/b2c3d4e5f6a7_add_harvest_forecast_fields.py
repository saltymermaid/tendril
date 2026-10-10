"""add harvest forecast fields to categories and varieties

Categories carry the defaults (harvest_unit, plants_per_square); the matching variety
columns are overrides that inherit the category's value when null. Fills in defaults for
known categories and per-variety exceptions by name — names that don't exist are skipped.

Revision ID: b2c3d4e5f6a7
Revises: a4b5c6d7e8f9
Create Date: 2026-09-30 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a4b5c6d7e8f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Frozen copy of the values at the time of this migration (seed_reference.py may move on).
# (harvest_unit, plants_per_square). Unit is a singular noun and mostly matters for
# single-harvest crops ("2 heads"); continuous crops just read "continuous".
CATEGORY_DEFAULTS = {
    "Tomatoes":        (None,      1),
    "Peppers":         (None,      1),
    "Cucumbers":       (None,      1),
    "Squash":          (None,      1),
    "Beans":           (None,      9),
    "Sweet Potatoes":  ("plant",   1),
    "Bunching Onions": ("onion",  16),
    "Peas":            (None,      8),
    "Cabbage":         ("head",    1),
    "Melons":          ("plant",   1),
    "Radishes":        ("radish", 16),
    "Herbs":           (None,      1),
    "Flowers":         (None,      1),
    "Okra":            (None,      1),
    "Eggplant":        (None,      1),
    "Beets":           ("beet",    9),
    "Broccoli":        ("head",    1),
    "Carrots":         ("carrot", 16),
    "Cauliflower":     ("head",    1),
    "Corn":            ("plant",   4),
    "Kohlrabi":        ("bulb",    4),
    "Onions":          ("onion",   9),
    "Peanuts":         ("plant",   1),
    "Sunflowers":      ("head",    1),
}

VARIETY_OVERRIDES = {
    "Double Yield Pickling":          {"plants_per_square": 2},
    "Pole Blue Lake":                 {"plants_per_square": 8},
    "PR Black Bean (vining)":         {"plants_per_square": 8},
    "Dwarf Pak Choi":                 {"plants_per_square": 4},
    "Watermelon Radish":              {"plants_per_square": 9},
    "English Thyme":                  {"plants_per_square": 4},
    "French Thyme":                   {"plants_per_square": 4},
    "Slow-Bolt Cilantro":             {"plants_per_square": 9},
    "Italian Large Leaf Basil":       {"plants_per_square": 4},
    "Green Basil":                    {"plants_per_square": 4},
    "Purple Basil":                   {"plants_per_square": 4},
    "Common Chives":                  {"plants_per_square": 16},
    "Chives":                         {"plants_per_square": 16},
    "Parsley":                        {"plants_per_square": 4},
    "Queen Sophia Marigold":          {"harvest_type_override": "none", "plants_per_square": 4},
    "Naughty Marietta Marigold":      {"harvest_type_override": "none", "plants_per_square": 4},
    "French Red Cherry Marigold":     {"harvest_type_override": "none", "plants_per_square": 4},
    "Marigold (French Double Dwarf)": {"harvest_type_override": "none", "plants_per_square": 4},
    "Marigold":                       {"harvest_type_override": "none", "plants_per_square": 4},
    "Zinnia (Pinwheel Mixed Colors)": {"harvest_type_override": "none", "plants_per_square": 4},
}


def upgrade() -> None:
    op.add_column('categories', sa.Column('harvest_unit', sa.String(30), nullable=True))
    op.add_column('categories', sa.Column('plants_per_square', sa.Integer(), nullable=True))
    op.add_column('varieties', sa.Column('harvest_type_override', sa.String(20), nullable=True))
    op.add_column('varieties', sa.Column('harvest_unit', sa.String(30), nullable=True))
    op.add_column('varieties', sa.Column('plants_per_square', sa.Integer(), nullable=True))

    conn = op.get_bind()
    for name, (unit, pps) in CATEGORY_DEFAULTS.items():
        conn.execute(
            sa.text("UPDATE categories SET harvest_unit = :unit, plants_per_square = :pps WHERE name = :name"),
            {"unit": unit, "pps": pps, "name": name},
        )
    for name, fields in VARIETY_OVERRIDES.items():
        assignments = ", ".join(f"{col} = :{col}" for col in fields)
        conn.execute(sa.text(f"UPDATE varieties SET {assignments} WHERE name = :name"), {**fields, "name": name})


def downgrade() -> None:
    op.drop_column('varieties', 'plants_per_square')
    op.drop_column('varieties', 'harvest_unit')
    op.drop_column('varieties', 'harvest_type_override')
    op.drop_column('categories', 'plants_per_square')
    op.drop_column('categories', 'harvest_unit')
