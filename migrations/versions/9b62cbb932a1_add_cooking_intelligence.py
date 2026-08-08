"""add cooking intelligence

Revision ID: 9b62cbb932a1
Revises: 4c03d8ed4601
Create Date: 2026-08-08 10:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "9b62cbb932a1"
down_revision = "4c03d8ed4601"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cooking_steps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("minimum_duration", sa.Integer(), nullable=True),
        sa.Column("maximum_duration", sa.Integer(), nullable=True),
        sa.Column("heat_level", sa.String(length=30), nullable=True),
        sa.Column("temperature_min", sa.Integer(), nullable=True),
        sa.Column("temperature_max", sa.Integer(), nullable=True),
        sa.Column("visual_cue", sa.Text(), nullable=True),
        sa.Column("colour_stage", sa.String(length=120), nullable=True),
        sa.Column("texture_cue", sa.Text(), nullable=True),
        sa.Column("aroma_cue", sa.Text(), nullable=True),
        sa.Column("transformation_before", sa.Text(), nullable=True),
        sa.Column("transformation_process", sa.Text(), nullable=True),
        sa.Column("transformation_after", sa.Text(), nullable=True),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("benefits", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("common_mistakes", sa.JSON(), nullable=False),
        sa.Column("correction", sa.Text(), nullable=True),
        sa.Column("scientific_explanation", sa.Text(), nullable=True),
        sa.Column("critical", sa.Boolean(), nullable=False),
        sa.Column("source", sa.String(length=30), nullable=False),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recipe_id", "step_number", name="uq_recipe_cooking_step"),
    )
    with op.batch_alter_table("cooking_steps", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_cooking_steps_recipe_id"), ["recipe_id"], unique=False
        )

    op.create_table(
        "cooking_step_ingredients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cooking_step_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=True),
        sa.Column("ingredient_name", sa.String(length=120), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(length=20), nullable=True),
        sa.Column("addition_order", sa.Integer(), nullable=False),
        sa.Column("why_now", sa.Text(), nullable=True),
        sa.Column("contribution", sa.Text(), nullable=True),
        sa.Column("added_too_early", sa.Text(), nullable=True),
        sa.Column("added_too_late", sa.Text(), nullable=True),
        sa.Column("expected_transformation", sa.Text(), nullable=True),
        sa.Column("visual_cue", sa.Text(), nullable=True),
        sa.Column("aroma_cue", sa.Text(), nullable=True),
        sa.Column("texture_cue", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["cooking_step_id"], ["cooking_steps.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredients.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("cooking_step_ingredients", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_cooking_step_ingredients_cooking_step_id"),
            ["cooking_step_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_cooking_step_ingredients_ingredient_id"),
            ["ingredient_id"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("cooking_step_ingredients", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_cooking_step_ingredients_ingredient_id"))
        batch_op.drop_index(
            batch_op.f("ix_cooking_step_ingredients_cooking_step_id")
        )
    op.drop_table("cooking_step_ingredients")
    with op.batch_alter_table("cooking_steps", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_cooking_steps_recipe_id"))
    op.drop_table("cooking_steps")
