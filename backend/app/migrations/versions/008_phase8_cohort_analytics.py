"""Phase 8 - Advanced Cohort Analytics

Revision ID: 008
Revises: 007
Create Date: 2026-02-06

This migration creates the Phase 8 advanced cohort analytics system with:
- 9 data models for cohort analysis, retention, LTV, customer journey, churn, feature adoption, interventions, custom metrics
- 4 ENUM types for cohort types, metric types, journey stages, intervention status
- 23+ strategic database indexes for query optimization
- JSON fields for flexible data storage
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types
    cohort_type_enum = postgresql.ENUM(
        'signup_month', 'signup_quarter', 'signup_year', 'first_purchase_month',
        'first_feature_month', 'product_tier', 'geographic', 'custom',
        name='cohort_type', schema='public'
    )
    cohort_type_enum.create(op.get_bind(), checkfirst=True)
    
    metric_type_enum = postgresql.ENUM(
        'count', 'sum', 'average', 'percentage', 'ratio', 'custom_formula',
        name='metric_type', schema='public'
    )
    metric_type_enum.create(op.get_bind(), checkfirst=True)
    
    journey_stage_enum = postgresql.ENUM(
        'awareness', 'consideration', 'activation', 'retention', 'revenue', 'advocacy', 'churn',
        name='journey_stage', schema='public'
    )
    journey_stage_enum.create(op.get_bind(), checkfirst=True)
    
    intervention_status_enum = postgresql.ENUM(
        'suggested', 'scheduled', 'in_progress', 'completed', 'failed',
        name='intervention_status', schema='public'
    )
    intervention_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create cohort_analysis table
    op.create_table(
        'cohort_analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('cohort_type', postgresql.ENUM('signup_month', 'signup_quarter', 'signup_year', 'first_purchase_month', 'first_feature_month', 'product_tier', 'geographic', 'custom', name='cohort_type'), nullable=False),
        sa.Column('cohort_name', sa.String(255), nullable=False),
        sa.Column('cohort_date', sa.DateTime(), nullable=False),
        sa.Column('size', sa.Integer(), server_default='0'),
        sa.Column('active_count', sa.Integer(), server_default='0'),
        sa.Column('retention_rate', sa.Float(), server_default='0.0'),
        sa.Column('avg_engagement_score', sa.Float(), server_default='0.0'),
        sa.Column('avg_api_calls', sa.Float(), server_default='0.0'),
        sa.Column('avg_revenue_per_user', sa.Float(), server_default='0.0'),
        sa.Column('churn_rate', sa.Float(), server_default='0.0'),
        sa.Column('days_to_churn_avg', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['customer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_cohort_customer', 'cohort_analysis', ['customer_id'])
    op.create_index('idx_cohort_type_date', 'cohort_analysis', ['cohort_type', 'cohort_date'])
    op.create_index('idx_cohort_name', 'cohort_analysis', ['cohort_name'])
    op.create_index('idx_cohort_retention_rate', 'cohort_analysis', ['retention_rate'])
    
    # Create retention_curve table
    op.create_table(
        'retention_curve',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cohort_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('days_since_cohort', sa.Integer(), nullable=False),
        sa.Column('period_label', sa.String(50), nullable=False),
        sa.Column('retained_count', sa.Integer(), server_default='0'),
        sa.Column('retention_percentage', sa.Float(), server_default='0.0'),
        sa.Column('active_in_period', sa.Integer(), server_default='0'),
        sa.Column('api_calls_in_period', sa.Integer(), server_default='0'),
        sa.Column('revenue_in_period', sa.Float(), server_default='0.0'),
        sa.Column('features_used', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['cohort_id'], ['cohort_analysis.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_retention_cohort_period', 'retention_curve', ['cohort_id', 'days_since_cohort'])
    op.create_index('idx_retention_customer_period', 'retention_curve', ['customer_id', 'days_since_cohort'])
    op.create_index('idx_retention_percentage', 'retention_curve', ['retention_percentage'])
    
    # Create lifetime_value table
    op.create_table(
        'lifetime_value',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('historical_ltv', sa.Float(), server_default='0.0'),
        sa.Column('months_active', sa.Integer(), server_default='0'),
        sa.Column('arpu', sa.Float(), server_default='0.0'),
        sa.Column('projected_ltv', sa.Float(), server_default='0.0'),
        sa.Column('projection_confidence', sa.Float(), server_default='0.5'),
        sa.Column('ltv_tier', sa.String(50), server_default='Medium'),
        sa.Column('ltv_percentile', sa.Float(), server_default='50.0'),
        sa.Column('ltv_if_retained_12mo', sa.Float(), nullable=True),
        sa.Column('ltv_if_churn_today', sa.Float(), nullable=True),
        sa.Column('ltv_if_upsell', sa.Float(), nullable=True),
        sa.Column('retention_probability_12mo', sa.Float(), server_default='0.5'),
        sa.Column('churn_risk_score', sa.Float(), server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['customer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_id')
    )
    op.create_index('idx_ltv_customer', 'lifetime_value', ['customer_id'])
    op.create_index('idx_ltv_historical', 'lifetime_value', ['historical_ltv'])
    op.create_index('idx_ltv_projected', 'lifetime_value', ['projected_ltv'])
    op.create_index('idx_ltv_tier', 'lifetime_value', ['ltv_tier'])
    op.create_index('idx_ltv_percentile', 'lifetime_value', ['ltv_percentile'])
    
    # Create customer_journey table
    op.create_table(
        'customer_journey',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('current_stage', postgresql.ENUM('awareness', 'consideration', 'activation', 'retention', 'revenue', 'advocacy', 'churn', name='journey_stage'), nullable=False),
        sa.Column('stage_entry_date', sa.DateTime(), nullable=False),
        sa.Column('days_in_stage', sa.Integer(), server_default='0'),
        sa.Column('features_adopted', sa.Integer(), server_default='0'),
        sa.Column('integration_count', sa.Integer(), server_default='0'),
        sa.Column('team_size', sa.Integer(), server_default='1'),
        sa.Column('engagement_trajectory', sa.String(50), server_default='stable'),
        sa.Column('momentum_score', sa.Float(), server_default='0.0'),
        sa.Column('at_risk', sa.Boolean(), server_default='false'),
        sa.Column('risk_factors', sa.JSON(), nullable=True),
        sa.Column('awareness_date', sa.DateTime(), nullable=True),
        sa.Column('consideration_date', sa.DateTime(), nullable=True),
        sa.Column('activation_date', sa.DateTime(), nullable=True),
        sa.Column('retention_date', sa.DateTime(), nullable=True),
        sa.Column('revenue_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['customer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_id')
    )
    op.create_index('idx_journey_customer', 'customer_journey', ['customer_id'])
    op.create_index('idx_journey_stage', 'customer_journey', ['current_stage'])
    op.create_index('idx_journey_momentum', 'customer_journey', ['momentum_score'])
    op.create_index('idx_journey_at_risk', 'customer_journey', ['at_risk'])
    
    # Create churn_flow table
    op.create_table(
        'churn_flow',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('churn_probability', sa.Float(), server_default='0.0'),
        sa.Column('risk_level', sa.String(50), server_default='low'),
        sa.Column('days_to_churn_predicted', sa.Integer(), nullable=True),
        sa.Column('activity_decline', sa.Boolean(), server_default='false'),
        sa.Column('feature_usage_drop', sa.Boolean(), server_default='false'),
        sa.Column('api_call_decrease', sa.Boolean(), server_default='false'),
        sa.Column('engagement_score_drop', sa.Boolean(), server_default='false'),
        sa.Column('support_tickets_increase', sa.Boolean(), server_default='false'),
        sa.Column('intervention_offered', sa.Boolean(), server_default='false'),
        sa.Column('intervention_type', sa.String(100), nullable=True),
        sa.Column('intervention_date', sa.DateTime(), nullable=True),
        sa.Column('intervention_accepted', sa.Boolean(), server_default='false'),
        sa.Column('churned', sa.Boolean(), server_default='false'),
        sa.Column('churn_date', sa.DateTime(), nullable=True),
        sa.Column('save_successful', sa.Boolean(), nullable=True),
        sa.Column('signals_detected', sa.Integer(), server_default='0'),
        sa.Column('signal_names', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['customer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_id')
    )
    op.create_index('idx_churn_customer', 'churn_flow', ['customer_id'])
    op.create_index('idx_churn_probability', 'churn_flow', ['churn_probability'])
    op.create_index('idx_churn_risk_level', 'churn_flow', ['risk_level'])
    op.create_index('idx_churn_churned', 'churn_flow', ['churned'])
    op.create_index('idx_churn_intervention', 'churn_flow', ['intervention_offered'])
    
    # Create feature_adoption table
    op.create_table(
        'feature_adoption',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('feature_name', sa.String(255), nullable=False),
        sa.Column('feature_category', sa.String(100), server_default='api'),
        sa.Column('first_used_at', sa.DateTime(), nullable=False),
        sa.Column('days_to_adopt', sa.Integer(), nullable=False),
        sa.Column('usage_count', sa.Integer(), server_default='1'),
        sa.Column('usage_frequency', sa.String(50), server_default='once'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('impact_on_retention', sa.Float(), nullable=True),
        sa.Column('correlated_with_upgrade', sa.Boolean(), server_default='false'),
        sa.Column('cohort_adoption_rate', sa.Float(), nullable=True),
        sa.Column('early_adopter', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['customer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_feature_customer_name', 'feature_adoption', ['customer_id', 'feature_name'])
    op.create_index('idx_feature_days_to_adopt', 'feature_adoption', ['days_to_adopt'])
    op.create_index('idx_feature_frequency', 'feature_adoption', ['usage_frequency'])
    op.create_index('idx_feature_impact', 'feature_adoption', ['impact_on_retention'])
    
    # Create retention_intervention table
    op.create_table(
        'retention_intervention',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('intervention_type', sa.String(100), nullable=False),
        sa.Column('intervention_name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('offered_at', sa.DateTime(), nullable=True),
        sa.Column('offered_by', sa.String(255), nullable=True),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('status', postgresql.ENUM('suggested', 'scheduled', 'in_progress', 'completed', 'failed', name='intervention_status'), server_default='suggested'),
        sa.Column('revenue_impact', sa.Float(), server_default='0.0'),
        sa.Column('churn_prevented', sa.Boolean(), server_default='false'),
        sa.Column('retention_extension', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('roi', sa.Float(), nullable=True),
        sa.Column('created_at_ts', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['customer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_intervention_customer', 'retention_intervention', ['customer_id'])
    op.create_index('idx_intervention_type', 'retention_intervention', ['intervention_type'])
    op.create_index('idx_intervention_status', 'retention_intervention', ['status'])
    op.create_index('idx_intervention_accepted', 'retention_intervention', ['accepted_at'])
    op.create_index('idx_intervention_success', 'retention_intervention', ['success'])
    
    # Create custom_metric table
    op.create_table(
        'custom_metric',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metric_type', postgresql.ENUM('count', 'sum', 'average', 'percentage', 'ratio', 'custom_formula', name='metric_type'), nullable=False),
        sa.Column('formula', sa.Text(), nullable=True),
        sa.Column('source_table', sa.String(255), nullable=True),
        sa.Column('source_fields', sa.JSON(), nullable=True),
        sa.Column('time_period', sa.String(50), server_default='daily'),
        sa.Column('aggregation', sa.String(50), server_default='sum'),
        sa.Column('last_calculated', sa.DateTime(), nullable=True),
        sa.Column('current_value', sa.Float(), nullable=True),
        sa.Column('previous_value', sa.Float(), nullable=True),
        sa.Column('change_percentage', sa.Float(), nullable=True),
        sa.Column('trend_direction', sa.String(50), server_default='flat'),
        sa.Column('threshold_warning', sa.Float(), nullable=True),
        sa.Column('threshold_critical', sa.Float(), nullable=True),
        sa.Column('is_public', sa.Boolean(), server_default='false'),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['customer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_id', 'name')
    )
    op.create_index('idx_metric_customer', 'custom_metric', ['customer_id'])
    op.create_index('idx_metric_name', 'custom_metric', ['name'])
    op.create_index('idx_metric_type', 'custom_metric', ['metric_type'])
    
    # Create metric_history table
    op.create_table(
        'metric_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('change_from_previous', sa.Float(), nullable=True),
        sa.Column('percent_change', sa.Float(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['metric_id'], ['custom_metric.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_history_metric_recorded', 'metric_history', ['metric_id', 'recorded_at'])
    op.create_index('idx_history_customer_recorded', 'metric_history', ['customer_id', 'recorded_at'])


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_table('metric_history')
    op.drop_table('custom_metric')
    op.drop_table('retention_intervention')
    op.drop_table('feature_adoption')
    op.drop_table('churn_flow')
    op.drop_table('customer_journey')
    op.drop_table('lifetime_value')
    op.drop_table('retention_curve')
    op.drop_table('cohort_analysis')
    
    # Drop ENUM types
    postgresql.ENUM('intervention_status', name='intervention_status').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM('journey_stage', name='journey_stage').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM('metric_type', name='metric_type').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM('cohort_type', name='cohort_type').drop(op.get_bind(), checkfirst=True)
