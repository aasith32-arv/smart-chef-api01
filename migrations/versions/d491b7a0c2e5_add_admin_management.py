"""add admin management

Revision ID: d491b7a0c2e5
Revises: a67f92d2b4c1
Create Date: 2026-08-09 22:15:00
"""

from alembic import op
import sqlalchemy as sa


revision = "d491b7a0c2e5"
down_revision = "a67f92d2b4c1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "role", sa.String(length=20), nullable=False, server_default="user"
            )
        )
        batch_op.add_column(
            sa.Column(
                "is_active", sa.Boolean(), nullable=False, server_default=sa.true()
            )
        )
        batch_op.create_index("ix_users_role", ["role"], unique=False)
        batch_op.create_index("ix_users_is_active", ["is_active"], unique=False)

    with op.batch_alter_table("recipes", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "publication_status",
                sa.String(length=20),
                nullable=False,
                server_default="published",
            )
        )
        batch_op.add_column(
            sa.Column(
                "managed_by_admin",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.create_index(
            "ix_recipes_publication_status", ["publication_status"], unique=False
        )

    with op.batch_alter_table("dish_families", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "managed_by_admin",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )

    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("admin_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("target_type", sa.String(length=40), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "admin_user_id",
        "action",
        "target_type",
        "target_id",
        "created_at",
    ):
        op.create_index(
            f"ix_admin_audit_logs_{column}",
            "admin_audit_logs",
            [column],
            unique=False,
        )


def downgrade():
    for column in (
        "created_at",
        "target_id",
        "target_type",
        "action",
        "admin_user_id",
    ):
        op.drop_index(
            f"ix_admin_audit_logs_{column}", table_name="admin_audit_logs"
        )
    op.drop_table("admin_audit_logs")

    with op.batch_alter_table("dish_families", schema=None) as batch_op:
        batch_op.drop_column("managed_by_admin")

    with op.batch_alter_table("recipes", schema=None) as batch_op:
        batch_op.drop_index("ix_recipes_publication_status")
        batch_op.drop_column("managed_by_admin")
        batch_op.drop_column("publication_status")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index("ix_users_is_active")
        batch_op.drop_index("ix_users_role")
        batch_op.drop_column("is_active")
        batch_op.drop_column("role")
