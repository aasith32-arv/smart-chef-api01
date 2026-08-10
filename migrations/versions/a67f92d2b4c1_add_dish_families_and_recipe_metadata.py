"""add dish families and recipe variety metadata

Revision ID: a67f92d2b4c1
Revises: 31ac2c7d8f10
Create Date: 2026-08-09 20:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "a67f92d2b4c1"
down_revision = "31ac2c7d8f10"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "dish_families",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=140), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("image", sa.String(length=500), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("dish_families", schema=None) as batch_op:
        batch_op.create_index("ix_dish_families_category", ["category"], unique=False)
        batch_op.create_index("ix_dish_families_is_active", ["is_active"], unique=False)
        batch_op.create_index("ix_dish_families_name", ["name"], unique=True)
        batch_op.create_index("ix_dish_families_slug", ["slug"], unique=True)

    with op.batch_alter_table("recipes", schema=None) as batch_op:
        batch_op.add_column(sa.Column("slug", sa.String(length=180), nullable=True))
        batch_op.add_column(sa.Column("family_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("cuisine", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("region", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("protein", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("diet_type", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("difficulty", sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column("prep_time", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("cook_time", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("spice_level", sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column("tags", sa.JSON(), nullable=True))
        batch_op.create_foreign_key(
            "fk_recipes_family_id_dish_families",
            "dish_families",
            ["family_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_recipes_slug", ["slug"], unique=True)
        batch_op.create_index("ix_recipes_family_id", ["family_id"], unique=False)
        batch_op.create_index("ix_recipes_cuisine", ["cuisine"], unique=False)
        batch_op.create_index("ix_recipes_region", ["region"], unique=False)
        batch_op.create_index("ix_recipes_protein", ["protein"], unique=False)
        batch_op.create_index("ix_recipes_diet_type", ["diet_type"], unique=False)


def downgrade():
    with op.batch_alter_table("recipes", schema=None) as batch_op:
        batch_op.drop_index("ix_recipes_diet_type")
        batch_op.drop_index("ix_recipes_protein")
        batch_op.drop_index("ix_recipes_region")
        batch_op.drop_index("ix_recipes_cuisine")
        batch_op.drop_index("ix_recipes_family_id")
        batch_op.drop_index("ix_recipes_slug")
        batch_op.drop_constraint(
            "fk_recipes_family_id_dish_families", type_="foreignkey"
        )
        batch_op.drop_column("tags")
        batch_op.drop_column("spice_level")
        batch_op.drop_column("cook_time")
        batch_op.drop_column("prep_time")
        batch_op.drop_column("difficulty")
        batch_op.drop_column("diet_type")
        batch_op.drop_column("protein")
        batch_op.drop_column("region")
        batch_op.drop_column("cuisine")
        batch_op.drop_column("family_id")
        batch_op.drop_column("slug")

    with op.batch_alter_table("dish_families", schema=None) as batch_op:
        batch_op.drop_index("ix_dish_families_slug")
        batch_op.drop_index("ix_dish_families_name")
        batch_op.drop_index("ix_dish_families_is_active")
        batch_op.drop_index("ix_dish_families_category")
    op.drop_table("dish_families")
