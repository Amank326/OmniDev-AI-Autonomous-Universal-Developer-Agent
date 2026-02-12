"""Create payment and subscription tables

Revision ID: 005_payment_integration
Revises: 004_phase4_websockets
Create Date: 2025-02-06 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_payment_integration'
down_revision = '004_phase4_websockets'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create StripeCustomer table
    op.create_table(
        'stripe_customers',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('stripe_customer_id', sa.String(255), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('ix_stripe_customers_user_id', 'stripe_customers', ['user_id'])
    op.create_index('ix_stripe_customers_stripe_customer_id', 'stripe_customers', ['stripe_customer_id'])

    # Create PricingPlan table
    op.create_table(
        'pricing_plans',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('tier', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price_monthly', sa.Integer(), nullable=True),
        sa.Column('price_annual', sa.Integer(), nullable=True),
        sa.Column('stripe_product_id', sa.String(255), nullable=True),
        sa.Column('stripe_price_monthly_id', sa.String(255), nullable=True),
        sa.Column('stripe_price_annual_id', sa.String(255), nullable=True),
        sa.Column('features', sa.JSON(), nullable=True),
        sa.Column('limits', sa.JSON(), nullable=True),
        sa.Column('trial_days', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pricing_plans_tier', 'pricing_plans', ['tier'])
    op.create_index('ix_pricing_plans_is_active', 'pricing_plans', ['is_active'])

    # Create Subscription table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('customer_id', sa.String(36), nullable=False),
        sa.Column('plan_id', sa.String(36), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=False, unique=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('tier', sa.String(50), nullable=False),
        sa.Column('billing_cycle', sa.String(20), nullable=False),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('trial_end', sa.DateTime(), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), default=False),
        sa.Column('canceled_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['stripe_customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plan_id'], ['pricing_plans.id'], ondelete='SET NULL')
    )
    op.create_index('ix_subscriptions_customer_id', 'subscriptions', ['customer_id'])
    op.create_index('ix_subscriptions_stripe_subscription_id', 'subscriptions', ['stripe_subscription_id'])
    op.create_index('ix_subscriptions_status', 'subscriptions', ['status'])

    # Create Invoice table
    op.create_table(
        'invoices',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('customer_id', sa.String(36), nullable=False),
        sa.Column('subscription_id', sa.String(36), nullable=True),
        sa.Column('stripe_invoice_id', sa.String(255), nullable=False, unique=True),
        sa.Column('invoice_number', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('amount_subtotal', sa.Integer(), nullable=False),
        sa.Column('amount_tax', sa.Integer(), nullable=False),
        sa.Column('amount_total', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(3), default='usd'),
        sa.Column('date_created', sa.DateTime(), nullable=False),
        sa.Column('date_paid', sa.DateTime(), nullable=True),
        sa.Column('pdf_url', sa.String(500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['stripe_customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='SET NULL')
    )
    op.create_index('ix_invoices_customer_id', 'invoices', ['customer_id'])
    op.create_index('ix_invoices_stripe_invoice_id', 'invoices', ['stripe_invoice_id'])
    op.create_index('ix_invoices_status', 'invoices', ['status'])

    # Create PaymentMethod table
    op.create_table(
        'payment_methods',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('customer_id', sa.String(36), nullable=False),
        sa.Column('stripe_payment_method_id', sa.String(255), nullable=False, unique=True),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('card_brand', sa.String(50), nullable=True),
        sa.Column('card_last4', sa.String(4), nullable=True),
        sa.Column('card_exp_month', sa.Integer(), nullable=True),
        sa.Column('card_exp_year', sa.Integer(), nullable=True),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['stripe_customers.id'], ondelete='CASCADE')
    )
    op.create_index('ix_payment_methods_customer_id', 'payment_methods', ['customer_id'])
    op.create_index('ix_payment_methods_stripe_payment_method_id', 'payment_methods', ['stripe_payment_method_id'])

    # Create PaymentTransaction table
    op.create_table(
        'payment_transactions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('customer_id', sa.String(36), nullable=False),
        sa.Column('stripe_payment_intent_id', sa.String(255), nullable=True, unique=True),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(3), default='usd'),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['stripe_customers.id'], ondelete='CASCADE')
    )
    op.create_index('ix_payment_transactions_customer_id', 'payment_transactions', ['customer_id'])
    op.create_index('ix_payment_transactions_status', 'payment_transactions', ['status'])

    # Create UsageRecord table
    op.create_table(
        'usage_records',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('subscription_id', sa.String(36), nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE')
    )
    op.create_index('ix_usage_records_subscription_id', 'usage_records', ['subscription_id'])
    op.create_index('ix_usage_records_metric_name', 'usage_records', ['metric_name'])

    # Create Coupon table
    op.create_table(
        'coupons',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('code', sa.String(100), nullable=False, unique=True),
        sa.Column('stripe_coupon_id', sa.String(255), nullable=True, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('discount_percent', sa.Integer(), nullable=True),
        sa.Column('discount_amount', sa.Integer(), nullable=True),
        sa.Column('duration', sa.String(50), nullable=True),
        sa.Column('duration_in_months', sa.Integer(), nullable=True),
        sa.Column('max_redemptions', sa.Integer(), nullable=True),
        sa.Column('redeemed_count', sa.Integer(), default=0),
        sa.Column('valid_from', sa.DateTime(), nullable=True),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('ix_coupons_code', 'coupons', ['code'])
    op.create_index('ix_coupons_is_active', 'coupons', ['is_active'])


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign key dependencies)
    op.drop_table('coupons')
    op.drop_table('usage_records')
    op.drop_table('payment_transactions')
    op.drop_table('payment_methods')
    op.drop_table('invoices')
    op.drop_table('subscriptions')
    op.drop_table('pricing_plans')
    op.drop_table('stripe_customers')
