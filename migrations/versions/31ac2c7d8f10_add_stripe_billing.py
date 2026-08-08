"""add stripe billing

Revision ID: 31ac2c7d8f10
Revises: 9b62cbb932a1
Create Date: 2026-08-08 12:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "31ac2c7d8f10"
down_revision = "9b62cbb932a1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "billing_customers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_billing_customers_user_id", "billing_customers", ["user_id"], unique=True)
    op.create_index(
        "ix_billing_customers_stripe_customer_id", "billing_customers", ["stripe_customer_id"], unique=True
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("stripe_subscription_id", sa.String(length=255), nullable=False),
        sa.Column("stripe_price_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("current_period_end", sa.DateTime(), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])
    op.create_index(
        "ix_subscriptions_stripe_subscription_id", "subscriptions", ["stripe_subscription_id"], unique=True
    )

    op.create_table(
        "advertising_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("stripe_checkout_session_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_payment_intent_id", sa.String(length=255), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("payment_status", sa.String(length=40), nullable=False),
        sa.Column("review_status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_payment_intent_id"),
    )
    op.create_index("ix_advertising_orders_user_id", "advertising_orders", ["user_id"])
    op.create_index("ix_advertising_orders_payment_status", "advertising_orders", ["payment_status"])
    op.create_index("ix_advertising_orders_review_status", "advertising_orders", ["review_status"])
    op.create_index(
        "ix_advertising_orders_stripe_checkout_session_id",
        "advertising_orders",
        ["stripe_checkout_session_id"],
        unique=True,
    )

    op.create_table(
        "stripe_webhook_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stripe_event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_stripe_webhook_events_stripe_event_id",
        "stripe_webhook_events",
        ["stripe_event_id"],
        unique=True,
    )


def downgrade():
    op.drop_index("ix_stripe_webhook_events_stripe_event_id", table_name="stripe_webhook_events")
    op.drop_table("stripe_webhook_events")
    op.drop_index("ix_advertising_orders_stripe_checkout_session_id", table_name="advertising_orders")
    op.drop_index("ix_advertising_orders_review_status", table_name="advertising_orders")
    op.drop_index("ix_advertising_orders_payment_status", table_name="advertising_orders")
    op.drop_index("ix_advertising_orders_user_id", table_name="advertising_orders")
    op.drop_table("advertising_orders")
    op.drop_index("ix_subscriptions_stripe_subscription_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_status", table_name="subscriptions")
    op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")
    op.drop_table("subscriptions")
    op.drop_index("ix_billing_customers_stripe_customer_id", table_name="billing_customers")
    op.drop_index("ix_billing_customers_user_id", table_name="billing_customers")
    op.drop_table("billing_customers")
