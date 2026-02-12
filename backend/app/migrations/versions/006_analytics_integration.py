"""Analytics Integration Migration for Phase 6

Revision ID: 006
Revises: 005
Create Date: 2026-02-06 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create analytics tables"""
    
    # Create analytics_events table
    op.create_table(
        'analytics_events',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('customer_id', sa.String(36), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_source', sa.String(50), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False, server_default='usd'),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['customer_id'], ['stripe_customers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_analytics_events_customer_id', 'analytics_events', ['customer_id'])
    op.create_index('ix_analytics_events_event_type', 'analytics_events', ['event_type'])
    op.create_index('ix_analytics_events_occurred_at', 'analytics_events', ['occurred_at'])

    # Create revenue_metrics table
    op.create_table(
        'revenue_metrics',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('metric_type', sa.String(50), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='usd'),
        sa.Column('period_date', sa.DateTime(), nullable=False),
        sa.Column('calculation_method', sa.String(100), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_revenue_metrics_type_date', 'revenue_metrics', ['metric_type', 'period_date'])
    op.create_index('ix_revenue_metrics_period_date', 'revenue_metrics', ['period_date'])

    # Create subscription_metrics table
    op.create_table(
        'subscription_metrics',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('metric_type', sa.String(50), nullable=False),
        sa.Column('value', sa.Integer(), nullable=False),
        sa.Column('tier', sa.String(50), nullable=True),
        sa.Column('period_date', sa.DateTime(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_subscription_metrics_type_date', 'subscription_metrics', ['metric_type', 'period_date'])
    op.create_index('ix_subscription_metrics_tier_date', 'subscription_metrics', ['tier', 'period_date'])

    # Create customer_metrics table
    op.create_table(
        'customer_metrics',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('customer_id', sa.String(36), nullable=False),
        sa.Column('total_revenue', sa.Float(), nullable=False, server_default='0'),
        sa.Column('payment_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_order_value', sa.Float(), nullable=False, server_default='0'),
        sa.Column('lifetime_value', sa.Float(), nullable=False, server_default='0'),
        sa.Column('health_score', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('churn_risk', sa.Float(), nullable=False, server_default='0'),
        sa.Column('days_since_last_payment', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_payment_date', sa.DateTime(), nullable=True),
        sa.Column('mrr_contribution', sa.Float(), nullable=False, server_default='0'),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['customer_id'], ['stripe_customers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_customer_metrics_customer_id', 'customer_metrics', ['customer_id'])
    op.create_index('ix_customer_metrics_churn_risk', 'customer_metrics', ['churn_risk'])
    op.create_index('ix_customer_metrics_health_score', 'customer_metrics', ['health_score'])

    # Create forecasted_metrics table
    op.create_table(
        'forecasted_metrics',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('metric_type', sa.String(50), nullable=False),
        sa.Column('forecast_date', sa.DateTime(), nullable=False),
        sa.Column('predicted_value', sa.Float(), nullable=False),
        sa.Column('confidence_level', sa.Float(), nullable=False),
        sa.Column('lower_bound', sa.Float(), nullable=True),
        sa.Column('upper_bound', sa.Float(), nullable=True),
        sa.Column('forecast_method', sa.String(50), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_forecasted_metrics_type_date', 'forecasted_metrics', ['metric_type', 'forecast_date'])

    # Create dashboard_widgets table
    op.create_table(
        'dashboard_widgets',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('customer_id', sa.String(36), nullable=False),
        sa.Column('widget_name', sa.String(100), nullable=False),
        sa.Column('widget_type', sa.String(50), nullable=False),
        sa.Column('chart_type', sa.String(50), nullable=True),
        sa.Column('metric_types', sa.JSON(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('size', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('refresh_interval_minutes', sa.Integer(), nullable=False, server_default='15'),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['customer_id'], ['stripe_customers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dashboard_widgets_customer_id', 'dashboard_widgets', ['customer_id'])

    # Create analytics_reports table
    op.create_table(
        'analytics_reports',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('customer_id', sa.String(36), nullable=False),
        sa.Column('report_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_format', sa.String(10), nullable=False, server_default='pdf'),
        sa.Column('metrics_included', sa.JSON(), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['customer_id'], ['stripe_customers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_analytics_reports_customer_id', 'analytics_reports', ['customer_id'])
    op.create_index('ix_analytics_reports_period', 'analytics_reports', ['period_start', 'period_end'])

    # Create analytics_alerts table
    op.create_table(
        'analytics_alerts',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('customer_id', sa.String(36), nullable=False),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('metric_type', sa.String(50), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=True),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False, server_default='warning'),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_acknowledged', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['customer_id'], ['stripe_customers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_analytics_alerts_customer_id', 'analytics_alerts', ['customer_id'])
    op.create_index('ix_analytics_alerts_type', 'analytics_alerts', ['alert_type'])


def downgrade() -> None:
    """Drop analytics tables"""
    op.drop_index('ix_analytics_alerts_type', table_name='analytics_alerts')
    op.drop_index('ix_analytics_alerts_customer_id', table_name='analytics_alerts')
    op.drop_table('analytics_alerts')
    
    op.drop_index('ix_analytics_reports_period', table_name='analytics_reports')
    op.drop_index('ix_analytics_reports_customer_id', table_name='analytics_reports')
    op.drop_table('analytics_reports')
    
    op.drop_index('ix_dashboard_widgets_customer_id', table_name='dashboard_widgets')
    op.drop_table('dashboard_widgets')
    
    op.drop_index('ix_forecasted_metrics_type_date', table_name='forecasted_metrics')
    op.drop_table('forecasted_metrics')
    
    op.drop_index('ix_customer_metrics_health_score', table_name='customer_metrics')
    op.drop_index('ix_customer_metrics_churn_risk', table_name='customer_metrics')
    op.drop_index('ix_customer_metrics_customer_id', table_name='customer_metrics')
    op.drop_table('customer_metrics')
    
    op.drop_index('ix_subscription_metrics_tier_date', table_name='subscription_metrics')
    op.drop_index('ix_subscription_metrics_type_date', table_name='subscription_metrics')
    op.drop_table('subscription_metrics')
    
    op.drop_index('ix_revenue_metrics_period_date', table_name='revenue_metrics')
    op.drop_index('ix_revenue_metrics_type_date', table_name='revenue_metrics')
    op.drop_table('revenue_metrics')
    
    op.drop_index('ix_analytics_events_occurred_at', table_name='analytics_events')
    op.drop_index('ix_analytics_events_event_type', table_name='analytics_events')
    op.drop_index('ix_analytics_events_customer_id', table_name='analytics_events')
    op.drop_table('analytics_events')
