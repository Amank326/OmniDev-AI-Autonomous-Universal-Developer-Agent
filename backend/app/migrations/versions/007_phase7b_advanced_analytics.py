"""Phase 7B: Advanced Analytics - Activity Tracking & Engagement System

Revision ID: 007
Revises: 006_analytics_integration
Create Date: 2026-02-06 14:30:00.000000

This migration creates the complete analytics and activity tracking system including:
- User activity logging (20+ activity types)
- Engagement metrics (0-100 scoring)
- Churn prediction models
- Customer segmentation (ML clustering)
- Anomaly detection
- Predictive alerts
- Recommendation engine
- Audit logging
- Project and system metrics
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # Create ENUM types for Phase 7B
    activity_type_enum = postgresql.ENUM(
        'login', 'logout', 'api_call', 'feature_usage', 'project_created',
        'project_updated', 'project_deleted', 'subscription_created',
        'subscription_updated', 'subscription_cancelled', 'payment_success',
        'payment_failed', 'report_generated', 'alert_triggered',
        'collaboration_started', 'collaboration_ended', 'file_uploaded',
        'file_downloaded', 'settings_changed', 'integration_added',
        name='activitytype',
        create_type=False
    )
    activity_type_enum.create(op.get_bind(), checkfirst=True)

    audit_action_enum = postgresql.ENUM(
        'create', 'read', 'update', 'delete', 'export', 'archive',
        'restore', 'approve', 'reject', 'escalate',
        name='auditaction',
        create_type=False
    )
    audit_action_enum.create(op.get_bind(), checkfirst=True)

    anomaly_type_enum = postgresql.ENUM(
        'engagement_drop', 'api_spike', 'error_rate_surge', 'latency_spike',
        'subscription_decline', 'revenue_anomaly', 'usage_anomaly',
        name='anomalytype',
        create_type=False
    )
    anomaly_type_enum.create(op.get_bind(), checkfirst=True)

    health_score_enum = postgresql.ENUM(
        'excellent', 'good', 'fair', 'poor', 'critical',
        name='healthscore',
        create_type=False
    )
    health_score_enum.create(op.get_bind(), checkfirst=True)

    # 1. UserActivity table - Track all user actions
    op.create_table(
        'user_activity',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('activity_type', postgresql.ENUM('login', 'logout', 'api_call', 'feature_usage', 'project_created',
            'project_updated', 'project_deleted', 'subscription_created',
            'subscription_updated', 'subscription_cancelled', 'payment_success',
            'payment_failed', 'report_generated', 'alert_triggered',
            'collaboration_started', 'collaboration_ended', 'file_uploaded',
            'file_downloaded', 'settings_changed', 'integration_added', name='activitytype'), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('metadata', postgresql.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['stripe_customers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_activity_customer_created', 'user_activity', ['customer_id', 'created_at'])
    op.create_index('idx_user_activity_type', 'user_activity', ['activity_type'])
    op.create_index('idx_user_activity_created', 'user_activity', ['created_at'])

    # 2. EngagementMetrics table - 0-100 engagement scores
    op.create_table(
        'engagement_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('engagement_score', sa.Float(), nullable=False),
        sa.Column('login_frequency_score', sa.Float(), nullable=False),
        sa.Column('feature_usage_score', sa.Float(), nullable=False),
        sa.Column('api_usage_score', sa.Float(), nullable=False),
        sa.Column('retention_score', sa.Float(), nullable=False),
        sa.Column('trend', sa.String(10), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(), nullable=True),
        sa.Column('calculated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['stripe_customers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_id', name='uq_engagement_per_customer')
    )
    op.create_index('idx_engagement_score', 'engagement_metrics', ['engagement_score'])
    op.create_index('idx_engagement_customer', 'engagement_metrics', ['customer_id'])
    op.create_index('idx_engagement_calculated', 'engagement_metrics', ['calculated_at'])

    # 3. ProjectMetrics table - Per-project performance
    op.create_table(
        'project_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('project_name', sa.String(255), nullable=False),
        sa.Column('api_call_volume', sa.Integer(), nullable=False),
        sa.Column('error_rate', sa.Float(), nullable=False),
        sa.Column('response_time_ms', sa.Float(), nullable=False),
        sa.Column('uptime_percentage', sa.Float(), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['stripe_customers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_project_metrics_customer', 'project_metrics', ['customer_id'])
    op.create_index('idx_project_metrics_updated', 'project_metrics', ['updated_at'])

    # 4. SystemMetrics table - Platform-wide metrics
    op.create_table(
        'system_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('metadata', postgresql.JSON(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_system_metrics_name_recorded', 'system_metrics', ['metric_name', 'recorded_at'])

    # 5. AuditLog table - Compliance audit trail
    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('actor', sa.String(100), nullable=False),
        sa.Column('action', postgresql.ENUM('create', 'read', 'update', 'delete', 'export', 'archive',
            'restore', 'approve', 'reject', 'escalate', name='auditaction'), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('changes', postgresql.JSON(), nullable=True),
        sa.Column('reason', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['stripe_customers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_customer_action_created', 'audit_log', ['customer_id', 'action', 'created_at'])
    op.create_index('idx_audit_resource', 'audit_log', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_created', 'audit_log', ['created_at'])

    # 6. AnomalyDetection table - Statistical anomalies
    op.create_table(
        'anomaly_detection',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('anomaly_type', postgresql.ENUM('engagement_drop', 'api_spike', 'error_rate_surge', 'latency_spike',
            'subscription_decline', 'revenue_anomaly', 'usage_anomaly', name='anomalytype'), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('expected_value', sa.Float(), nullable=False),
        sa.Column('actual_value', sa.Float(), nullable=False),
        sa.Column('deviation_percentage', sa.Float(), nullable=False),
        sa.Column('z_score', sa.Float(), nullable=False),
        sa.Column('is_acknowledged', sa.Boolean(), default=False, nullable=False),
        sa.Column('detected_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['stripe_customers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_anomaly_customer_severity_detected', 'anomaly_detection', ['customer_id', 'severity', 'detected_at'])
    op.create_index('idx_anomaly_type', 'anomaly_detection', ['anomaly_type'])

    # 7. ChurnPrediction table - ML churn probabilities
    op.create_table(
        'churn_prediction',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('churn_probability', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(20), nullable=False),
        sa.Column('engagement_score', sa.Float(), nullable=False),
        sa.Column('days_inactive', sa.Integer(), nullable=False),
        sa.Column('subscription_health', sa.String(20), nullable=False),
        sa.Column('predicted_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['stripe_customers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_id', name='uq_churn_per_customer')
    )
    op.create_index('idx_churn_probability', 'churn_prediction', ['churn_probability'])
    op.create_index('idx_churn_customer', 'churn_prediction', ['customer_id'])
    op.create_index('idx_churn_risk_level', 'churn_prediction', ['risk_level'])

    # 8. CustomerSegment table - K-means clustering results
    op.create_table(
        'customer_segment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('segment_name', sa.String(50), nullable=False),
        sa.Column('segment_value', sa.Integer(), nullable=False),
        sa.Column('ltv_score', sa.Float(), nullable=False),
        sa.Column('engagement_level', sa.String(20), nullable=False),
        sa.Column('characteristics', postgresql.JSON(), nullable=True),
        sa.Column('segmented_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['stripe_customers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_id', name='uq_segment_per_customer')
    )
    op.create_index('idx_segment_customer', 'customer_segment', ['customer_id'])
    op.create_index('idx_segment_name', 'customer_segment', ['segment_name'])

    # 9. PredictiveAlert table - AI-generated alerts
    op.create_table(
        'predictive_alert',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('recommended_action', sa.Text(), nullable=True),
        sa.Column('is_acknowledged', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['stripe_customers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_alert_customer_severity_created', 'predictive_alert', ['customer_id', 'severity', 'created_at'])
    op.create_index('idx_alert_type', 'predictive_alert', ['alert_type'])

    # 10. RecommendationEngine table - AI recommendations
    op.create_table(
        'recommendation_engine',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('recommendation_type', sa.String(50), nullable=False),
        sa.Column('recommendation_text', sa.Text(), nullable=False),
        sa.Column('priority_score', sa.Float(), nullable=False),
        sa.Column('expected_impact', sa.String(50), nullable=False),
        sa.Column('is_implemented', sa.Boolean(), default=False, nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('implemented_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['stripe_customers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_recommendation_customer_type', 'recommendation_engine', ['customer_id', 'recommendation_type'])
    op.create_index('idx_recommendation_priority', 'recommendation_engine', ['priority_score'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_recommendation_priority')
    op.drop_index('idx_recommendation_customer_type')
    op.drop_index('idx_alert_type')
    op.drop_index('idx_alert_customer_severity_created')
    op.drop_index('idx_segment_name')
    op.drop_index('idx_segment_customer')
    op.drop_index('idx_churn_risk_level')
    op.drop_index('idx_churn_customer')
    op.drop_index('idx_churn_probability')
    op.drop_index('idx_anomaly_type')
    op.drop_index('idx_anomaly_customer_severity_detected')
    op.drop_index('idx_audit_created')
    op.drop_index('idx_audit_resource')
    op.drop_index('idx_audit_customer_action_created')
    op.drop_index('idx_system_metrics_name_recorded')
    op.drop_index('idx_project_metrics_updated')
    op.drop_index('idx_project_metrics_customer')
    op.drop_index('idx_engagement_calculated')
    op.drop_index('idx_engagement_customer')
    op.drop_index('idx_engagement_score')
    op.drop_index('idx_user_activity_created')
    op.drop_index('idx_user_activity_type')
    op.drop_index('idx_user_activity_customer_created')

    # Drop tables
    op.drop_table('recommendation_engine')
    op.drop_table('predictive_alert')
    op.drop_table('customer_segment')
    op.drop_table('churn_prediction')
    op.drop_table('anomaly_detection')
    op.drop_table('audit_log')
    op.drop_table('system_metrics')
    op.drop_table('project_metrics')
    op.drop_table('engagement_metrics')
    op.drop_table('user_activity')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS activitytype')
    op.execute('DROP TYPE IF EXISTS auditaction')
    op.execute('DROP TYPE IF EXISTS anomalytype')
    op.execute('DROP TYPE IF EXISTS healthscore')
