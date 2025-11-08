-- Initial Schema Migration for AI-First Software Engineering Platform
-- PostgreSQL 15+
-- Created: 2025-11-08

-- ============================================================================
-- PART 1: USERS TABLE - System users and service accounts
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'manager', 'user', 'service')),
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_service_account BOOLEAN NOT NULL DEFAULT false,

    -- OAuth/SSO integration
    github_username VARCHAR(255),
    github_user_id BIGINT UNIQUE,
    github_access_token VARCHAR(500),
    github_token_expires_at TIMESTAMP WITH TIME ZONE,

    -- User metadata
    metadata JSONB DEFAULT '{}',
    preferences JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_user_id ON users(user_id);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_github_username ON users(github_username);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);

-- ============================================================================
-- PART 2: PROJECTS TABLE - Software projects
-- ============================================================================

CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    project_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    slug VARCHAR(255) NOT NULL UNIQUE,

    -- Repository information
    repository_url VARCHAR(500),
    repository_provider VARCHAR(50) CHECK (repository_provider IN ('github', 'gitlab', 'bitbucket')),
    repository_owner VARCHAR(255),
    repository_name VARCHAR(255),
    default_branch VARCHAR(100) DEFAULT 'main',

    -- Project configuration
    config JSONB DEFAULT '{}',
    technology_stack JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',

    -- Status & visibility
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
    is_public BOOLEAN NOT NULL DEFAULT false,
    is_template BOOLEAN NOT NULL DEFAULT false,

    -- Team & ownership
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_members JSONB DEFAULT '[]',

    -- Performance metrics
    average_review_time_minutes INTEGER,
    average_merge_time_minutes INTEGER,
    pr_merge_rate NUMERIC(5, 2),
    test_coverage_percent NUMERIC(5, 2),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP WITH TIME ZONE,
    archived_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_projects_project_id ON projects(project_id);
CREATE INDEX idx_projects_slug ON projects(slug);
CREATE INDEX idx_projects_owner_id ON projects(owner_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_created_at ON projects(created_at);
CREATE INDEX idx_projects_repository_url ON projects(repository_url);
CREATE INDEX idx_projects_is_public ON projects(is_public);

-- ============================================================================
-- PART 3: AGENTS TABLE - AI agent registry
-- ============================================================================

CREATE TABLE IF NOT EXISTS agents (
    id SERIAL PRIMARY KEY,
    agent_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    agent_type VARCHAR(100) NOT NULL CHECK (agent_type IN (
        'orchestrator',
        'architect',
        'planner',
        'codegen',
        'reviewer',
        'tester',
        'deployer',
        'security',
        'debugger',
        'documentation',
        'refactoring',
        'optimization',
        'infrastructure',
        'analytics',
        'custom'
    )),

    -- Model information
    model_provider VARCHAR(50) NOT NULL CHECK (model_provider IN ('anthropic', 'openai', 'google', 'ibm', 'qwen', 'local')),
    model_name VARCHAR(255) NOT NULL,
    model_version VARCHAR(100),

    -- Capabilities & configuration
    capabilities JSONB NOT NULL DEFAULT '{}',
    configuration JSONB NOT NULL DEFAULT '{}',
    required_tools JSONB DEFAULT '[]',
    max_tokens INTEGER DEFAULT 4096,
    temperature NUMERIC(3, 2) DEFAULT 0.7,
    top_p NUMERIC(3, 2) DEFAULT 0.9,

    -- Performance & monitoring
    success_rate NUMERIC(5, 2) DEFAULT 0.0,
    avg_execution_time_ms INTEGER DEFAULT 0,
    total_executions BIGINT DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Status & versioning
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_experimental BOOLEAN NOT NULL DEFAULT false,
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    deprecated_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_agents_agent_id ON agents(agent_id);
CREATE INDEX idx_agents_name ON agents(name);
CREATE INDEX idx_agents_type ON agents(agent_type);
CREATE INDEX idx_agents_is_active ON agents(is_active);
CREATE INDEX idx_agents_model_provider ON agents(model_provider);
CREATE INDEX idx_agents_tags ON agents USING GIN(tags);
CREATE INDEX idx_agents_created_at ON agents(created_at);

-- ============================================================================
-- PART 4: EVIDENCE TABLE - Decision sources with credibility scoring
-- ============================================================================

CREATE TABLE IF NOT EXISTS evidence (
    id SERIAL PRIMARY KEY,
    evidence_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(task_id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,

    -- Evidence source
    source_type VARCHAR(100) NOT NULL CHECK (source_type IN (
        'code_analysis',
        'test_result',
        'ai_model_output',
        'documentation',
        'code_review',
        'security_scan',
        'performance_profile',
        'coverage_report',
        'static_analysis',
        'dependency_check',
        'user_feedback',
        'metrics',
        'external_api',
        'github_action',
        'custom'
    )),
    source_name VARCHAR(255) NOT NULL,
    source_url VARCHAR(1000),

    -- Evidence content
    title VARCHAR(500) NOT NULL,
    description TEXT,
    content TEXT,
    raw_data JSONB DEFAULT '{}',

    -- Credibility scoring
    credibility_score NUMERIC(4, 3) NOT NULL DEFAULT 0.5 CHECK (credibility_score >= 0 AND credibility_score <= 1.0),
    confidence_level VARCHAR(20) CHECK (confidence_level IN ('very_high', 'high', 'medium', 'low', 'very_low')),
    credibility_factors JSONB DEFAULT '{}',
    historical_accuracy NUMERIC(5, 2),

    -- Attestation & validation
    is_verified BOOLEAN DEFAULT false,
    verified_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    verified_at TIMESTAMP WITH TIME ZONE,
    validation_notes TEXT,

    -- Relationships
    related_evidence JSONB DEFAULT '[]',
    contradicting_evidence JSONB DEFAULT '[]',

    -- Metadata
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_evidence_evidence_id ON evidence(evidence_id);
CREATE INDEX idx_evidence_project_id ON evidence(project_id);
CREATE INDEX idx_evidence_source_type ON evidence(source_type);
CREATE INDEX idx_evidence_credibility_score ON evidence(credibility_score);
CREATE INDEX idx_evidence_is_verified ON evidence(is_verified);
CREATE INDEX idx_evidence_created_at ON evidence(created_at);
CREATE INDEX idx_evidence_tags ON evidence USING GIN(tags);

-- ============================================================================
-- PART 5: TASKS TABLE - Issues, PRs, and tasks
-- ============================================================================

CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    task_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,

    -- GitHub Integration
    github_issue_number INTEGER,
    github_pr_number INTEGER,
    github_node_id VARCHAR(255),
    github_url VARCHAR(500),

    -- Task information
    title VARCHAR(500) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL CHECK (type IN ('bug', 'feature', 'refactor', 'test', 'documentation', 'task', 'chore')),

    -- Status and workflow
    status VARCHAR(50) NOT NULL DEFAULT 'open' CHECK (status IN (
        'open', 'in_progress', 'in_review', 'blocked', 'closed', 'draft'
    )),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('critical', 'high', 'medium', 'low')),

    -- Assignment & ownership
    assigned_to_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    assigned_to_agent_id UUID REFERENCES agents(agent_id) ON DELETE SET NULL,
    created_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Relationships
    parent_task_id UUID REFERENCES tasks(task_id) ON DELETE SET NULL,
    related_tasks JSONB DEFAULT '[]',

    -- Metrics
    estimated_hours NUMERIC(6, 2),
    actual_hours NUMERIC(6, 2),
    complexity_score INTEGER CHECK (complexity_score IS NULL OR (complexity_score >= 1 AND complexity_score <= 13)),

    -- Code change metrics
    files_changed INTEGER,
    lines_added INTEGER,
    lines_deleted INTEGER,

    -- AI processing
    ai_analysis JSONB DEFAULT '{}',
    ai_suggestions JSONB DEFAULT '[]',

    -- Labels and metadata
    labels JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    due_date TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_tasks_task_id ON tasks(task_id);
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_type ON tasks(type);
CREATE INDEX idx_tasks_assigned_to_user ON tasks(assigned_to_user_id);
CREATE INDEX idx_tasks_assigned_to_agent ON tasks(assigned_to_agent_id);
CREATE INDEX idx_tasks_github_issue ON tasks(github_issue_number);
CREATE INDEX idx_tasks_github_pr ON tasks(github_pr_number);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_tasks_parent_task ON tasks(parent_task_id);
CREATE INDEX idx_tasks_labels ON tasks USING GIN(labels);

-- Add foreign key for evidence task_id
ALTER TABLE evidence ADD CONSTRAINT fk_evidence_tasks
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE;

-- ============================================================================
-- PART 6: AGENT EXECUTIONS - Audit trail for agent runs
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_executions (
    id SERIAL PRIMARY KEY,
    execution_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(task_id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,

    -- Execution details
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    execution_time_ms INTEGER,
    cost_usd NUMERIC(10, 4),

    -- Result
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'running', 'success', 'failure', 'timeout')),
    result JSONB,
    error_message TEXT,

    -- Evidence tracking
    evidence_id UUID REFERENCES evidence(evidence_id) ON DELETE SET NULL,
    parent_execution_id UUID REFERENCES agent_executions(execution_id) ON DELETE SET NULL,

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agent_executions_execution_id ON agent_executions(execution_id);
CREATE INDEX idx_agent_executions_agent_id ON agent_executions(agent_id);
CREATE INDEX idx_agent_executions_task_id ON agent_executions(task_id);
CREATE INDEX idx_agent_executions_project_id ON agent_executions(project_id);
CREATE INDEX idx_agent_executions_status ON agent_executions(status);
CREATE INDEX idx_agent_executions_created_at ON agent_executions(created_at);

-- ============================================================================
-- PART 7: TASK COMMENTS - Comments on tasks/PRs
-- ============================================================================

CREATE TABLE IF NOT EXISTS task_comments (
    id SERIAL PRIMARY KEY,
    comment_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,

    author_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    agent_id UUID REFERENCES agents(agent_id) ON DELETE SET NULL,

    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'markdown' CHECK (content_type IN ('markdown', 'plain', 'html')),

    -- GitHub integration
    github_comment_id BIGINT UNIQUE,

    -- AI metadata
    is_ai_generated BOOLEAN DEFAULT false,
    ai_metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_task_comments_comment_id ON task_comments(comment_id);
CREATE INDEX idx_task_comments_task_id ON task_comments(task_id);
CREATE INDEX idx_task_comments_author_id ON task_comments(author_id);
CREATE INDEX idx_task_comments_created_at ON task_comments(created_at);

-- ============================================================================
-- PART 8: TASK ATTACHMENTS - Files and evidence links
-- ============================================================================

CREATE TABLE IF NOT EXISTS task_attachments (
    id SERIAL PRIMARY KEY,
    attachment_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,

    file_name VARCHAR(500) NOT NULL,
    file_type VARCHAR(100),
    file_size_bytes BIGINT,
    storage_path VARCHAR(1000) NOT NULL,

    is_evidence BOOLEAN DEFAULT false,
    evidence_id UUID REFERENCES evidence(evidence_id) ON DELETE SET NULL,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_task_attachments_attachment_id ON task_attachments(attachment_id);
CREATE INDEX idx_task_attachments_task_id ON task_attachments(task_id);
CREATE INDEX idx_task_attachments_is_evidence ON task_attachments(is_evidence);

-- ============================================================================
-- PART 9: AUDIT LOGS - Immutable event trail
-- ============================================================================

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

CREATE INDEX idx_audit_logs_log_id ON audit_logs(log_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_agent_id ON audit_logs(agent_id);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX idx_audit_logs_resource_id ON audit_logs(resource_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_status ON audit_logs(status);
CREATE INDEX idx_audit_logs_request_id ON audit_logs(request_id);

-- ============================================================================
-- PART 10: ACTIVITY FEED - High-level activity summaries
-- ============================================================================

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

CREATE INDEX idx_activity_feed_activity_id ON activity_feed(activity_id);
CREATE INDEX idx_activity_feed_project_id ON activity_feed(project_id);
CREATE INDEX idx_activity_feed_task_id ON activity_feed(task_id);
CREATE INDEX idx_activity_feed_user_id ON activity_feed(user_id);
CREATE INDEX idx_activity_feed_created_at ON activity_feed(created_at);
CREATE INDEX idx_activity_feed_is_public ON activity_feed(is_public);

-- ============================================================================
-- MIGRATION METADATA
-- ============================================================================

-- Create migrations table to track applied migrations
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255) NOT NULL,
    installed_on TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER
);

-- Record this migration
INSERT INTO schema_migrations (version, description) VALUES
    ('001', 'Initial schema: Users, Projects, Agents, Evidence, Tasks, Audit Logs')
ON CONFLICT (version) DO NOTHING;
