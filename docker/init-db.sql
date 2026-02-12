-- Initial Database Setup for OmniDev AI
-- This script initializes the database schema

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS public;
CREATE SCHEMA IF NOT EXISTS audit;

-- Set search path
SET search_path TO public, audit;

-- Create audit table for tracking changes
CREATE TABLE IF NOT EXISTS audit.audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(255) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    record_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    user_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET
);

CREATE INDEX idx_audit_table_name ON audit.audit_log(table_name);
CREATE INDEX idx_audit_timestamp ON audit.audit_log(timestamp);
CREATE INDEX idx_audit_user_id ON audit.audit_log(user_id);

-- Create index for full-text search
CREATE INDEX idx_audit_data_gin ON audit.audit_log USING GIN(new_values);

GRANT SELECT ON TABLE audit.audit_log TO omnidev_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA audit TO omnidev_user;

-- Create materialized view for recent changes
CREATE MATERIALIZED VIEW IF NOT EXISTS audit.recent_changes AS
SELECT 
    table_name,
    operation,
    COUNT(*) as change_count,
    MAX(timestamp) as last_changed
FROM audit.audit_log
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY table_name, operation;

CREATE INDEX idx_recent_changes_table ON audit.recent_changes(table_name);

-- Create connection monitoring table
CREATE TABLE IF NOT EXISTS public.connection_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET
);

CREATE INDEX idx_connection_log_user ON public.connection_log(user_id);
CREATE INDEX idx_connection_log_timestamp ON public.connection_log(timestamp);
CREATE INDEX idx_connection_log_endpoint ON public.connection_log(endpoint);

-- Create session management table
CREATE TABLE IF NOT EXISTS public.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL,
    token VARCHAR(500) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_sessions_user_id ON public.sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON public.sessions(expires_at);

-- Create feature flags table
CREATE TABLE IF NOT EXISTS public.feature_flags (
    id SERIAL PRIMARY KEY,
    flag_name VARCHAR(100) UNIQUE NOT NULL,
    enabled BOOLEAN DEFAULT FALSE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_feature_flags_name ON public.feature_flags(flag_name);

-- Create default feature flags
INSERT INTO public.feature_flags (flag_name, enabled, description) VALUES
    ('multi_agent_orchestration', true, 'Enable multi-agent collaboration features'),
    ('rag_search', true, 'Enable Retrieval-Augmented Generation'),
    ('real_time_collaboration', true, 'Enable WebSocket real-time features'),
    ('advanced_analytics', true, 'Enable advanced analytics dashboard'),
    ('background_jobs', true, 'Enable background job processing'),
    ('email_notifications', true, 'Enable email notifications')
ON CONFLICT (flag_name) DO NOTHING;

-- Create cache management table
CREATE TABLE IF NOT EXISTS public.cache_metadata (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(500) UNIQUE NOT NULL,
    cache_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    hit_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP
);

CREATE INDEX idx_cache_metadata_expires ON public.cache_metadata(expires_at);
CREATE INDEX idx_cache_metadata_key ON public.cache_metadata(cache_key);

-- Create rate limiting table
CREATE TABLE IF NOT EXISTS public.rate_limits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    endpoint VARCHAR(255),
    request_count INTEGER DEFAULT 0,
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    UNIQUE(user_id, endpoint, window_start)
);

CREATE INDEX idx_rate_limits_user ON public.rate_limits(user_id);
CREATE INDEX idx_rate_limits_endpoint ON public.rate_limits(endpoint);
CREATE INDEX idx_rate_limits_window ON public.rate_limits(window_start, window_end);

-- Create system metrics table
CREATE TABLE IF NOT EXISTS public.system_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    server_id VARCHAR(100),
    tags JSONB
);

CREATE INDEX idx_system_metrics_name ON public.system_metrics(metric_name);
CREATE INDEX idx_system_metrics_timestamp ON public.system_metrics(timestamp);
CREATE INDEX idx_system_metrics_tags ON public.system_metrics USING GIN(tags);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function for audit logging
CREATE OR REPLACE FUNCTION audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit.audit_log (table_name, operation, record_id, new_values, timestamp)
        VALUES (TG_TABLE_NAME, TG_OP, NEW.id, row_to_json(NEW), CURRENT_TIMESTAMP);
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit.audit_log (table_name, operation, record_id, old_values, new_values, timestamp)
        VALUES (TG_TABLE_NAME, TG_OP, NEW.id, row_to_json(OLD), row_to_json(NEW), CURRENT_TIMESTAMP);
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit.audit_log (table_name, operation, record_id, old_values, timestamp)
        VALUES (TG_TABLE_NAME, TG_OP, OLD.id, row_to_json(OLD), CURRENT_TIMESTAMP);
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Function for session cleanup
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS integer AS $$
DECLARE
    deleted_count integer;
BEGIN
    DELETE FROM public.sessions WHERE expires_at < CURRENT_TIMESTAMP;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function for cache cleanup
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS integer AS $$
DECLARE
    deleted_count integer;
BEGIN
    DELETE FROM public.cache_metadata WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO omnidev_user;
GRANT USAGE ON SCHEMA audit TO omnidev_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO omnidev_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO omnidev_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO omnidev_user;

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_connection_log_recent 
ON public.connection_log(timestamp DESC) 
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days';

-- Create partitions for connection log (if table is large)
-- These would be created separately based on time periods

-- Refresh materialized view
REFRESH MATERIALIZED VIEW CONCURRENTLY audit.recent_changes;

-- Create comment for audit log
COMMENT ON TABLE audit.audit_log IS 'Audit log for tracking all database changes';
COMMENT ON TABLE public.sessions IS 'User session management';
COMMENT ON TABLE public.feature_flags IS 'Feature flag management for gradual rollouts';

-- Done
COMMIT;
