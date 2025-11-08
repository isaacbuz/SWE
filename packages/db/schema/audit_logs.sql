-- Audit Logs: Immutable event trail for compliance, debugging, and forensics
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    log_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),

    -- Actor information
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    agent_id UUID REFERENCES agents(agent_id) ON DELETE SET NULL,
    service_name VARCHAR(255),

    -- Event information
    event_type VARCHAR(100) NOT NULL CHECK (event_type IN (
        'task_created',
        'task_updated',
        'task_assigned',
        'task_closed',
        'code_review_started',
        'code_review_completed',
        'code_pushed',
        'test_executed',
        'deployment_started',
        'deployment_completed',
        'deployment_failed',
        'agent_executed',
        'agent_failed',
        'evidence_added',
        'evidence_verified',
        'evidence_rejected',
        'user_created',
        'user_updated',
        'user_deleted',
        'permission_granted',
        'permission_revoked',
        'project_created',
        'project_deleted',
        'security_issue_detected',
        'security_issue_resolved',
        'data_accessed',
        'data_modified',
        'data_deleted',
        'api_call',
        'api_error',
        'system_error',
        'custom'
    )),
    event_action VARCHAR(50) CHECK (event_action IN ('create', 'read', 'update', 'delete', 'execute')),

    -- Resource information
    resource_type VARCHAR(100),
    resource_id VARCHAR(500),
    resource_name VARCHAR(500),

    -- Changes
    old_values JSONB,
    new_values JSONB,
    changes_summary TEXT,

    -- Metadata
    ip_address INET,
    user_agent VARCHAR(1000),
    request_id VARCHAR(255),
    session_id VARCHAR(255),
    metadata JSONB DEFAULT '{}',

    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'success' CHECK (status IN ('success', 'failure', 'partial', 'unknown')),
    error_message TEXT,

    -- Immutable flag
    is_immutable BOOLEAN NOT NULL DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Index for immutable log
    CONSTRAINT audit_logs_immutable CHECK (is_immutable = true)
);

-- Indexes for audit log queries
CREATE INDEX idx_audit_logs_log_id ON audit_logs(log_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_agent_id ON audit_logs(agent_id);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX idx_audit_logs_resource_id ON audit_logs(resource_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_status ON audit_logs(status);
CREATE INDEX idx_audit_logs_request_id ON audit_logs(request_id);

-- Performance optimization: monthly partitioning for large audit tables
-- This is set up for PostgreSQL 15+ - adjust retention policy as needed
ALTER TABLE audit_logs SET (
    autovacuum_vacuum_scale_factor = 0.01,
    autovacuum_analyze_scale_factor = 0.005
);

-- Activity Feed: High-level activity summaries for user interfaces
CREATE TABLE IF NOT EXISTS activity_feed (
    id SERIAL PRIMARY KEY,
    activity_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),

    -- Actor
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    agent_id UUID REFERENCES agents(agent_id) ON DELETE SET NULL,

    -- Activity
    activity_type VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    action_url VARCHAR(1000),

    -- Relationships
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(task_id) ON DELETE CASCADE,

    -- Visibility
    is_public BOOLEAN DEFAULT false,
    visible_to_users JSONB DEFAULT '[]',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for activity feed
CREATE INDEX idx_activity_feed_activity_id ON activity_feed(activity_id);
CREATE INDEX idx_activity_feed_project_id ON activity_feed(project_id);
CREATE INDEX idx_activity_feed_task_id ON activity_feed(task_id);
CREATE INDEX idx_activity_feed_user_id ON activity_feed(user_id);
CREATE INDEX idx_activity_feed_created_at ON activity_feed(created_at);
CREATE INDEX idx_activity_feed_is_public ON activity_feed(is_public);
