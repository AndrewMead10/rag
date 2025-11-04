"""replace stripe billing with polar

Revision ID: 0003_replace_stripe_with_polar
Revises: 0002_account_plan_structures
Create Date: 2025-11-04 15:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0003_replace_stripe_with_polar"
down_revision = "0002_account_plan_structures"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("plans") as batch_op:
        batch_op.add_column(sa.Column("polar_product_id", sa.String(), nullable=True))
        batch_op.drop_column("stripe_price_id")

    with op.batch_alter_table("account_subscriptions") as batch_op:
        batch_op.add_column(sa.Column("polar_customer_id", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("polar_subscription_id", sa.String(), nullable=True))
        batch_op.drop_column("stripe_customer_id")
        batch_op.drop_column("stripe_subscription_id")

    with op.batch_alter_table("vector_top_ups") as batch_op:
        batch_op.add_column(sa.Column("polar_order_id", sa.String(), nullable=True))
        batch_op.drop_column("stripe_payment_intent_id")


def downgrade() -> None:
    with op.batch_alter_table("vector_top_ups") as batch_op:
        batch_op.add_column(sa.Column("stripe_payment_intent_id", sa.String(), nullable=True))
        batch_op.drop_column("polar_order_id")

    with op.batch_alter_table("account_subscriptions") as batch_op:
        batch_op.add_column(sa.Column("stripe_customer_id", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("stripe_subscription_id", sa.String(), nullable=True))
        batch_op.drop_column("polar_customer_id")
        batch_op.drop_column("polar_subscription_id")

    with op.batch_alter_table("plans") as batch_op:
        batch_op.add_column(sa.Column("stripe_price_id", sa.String(), nullable=True))
        batch_op.drop_column("polar_product_id")
