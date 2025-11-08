-- Issues/Tasks table: Track issues, tasks, and pull requests
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

-- Indexes for common queries
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

-- Task comments and activity
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

-- Indexes for task comments
CREATE INDEX idx_task_comments_comment_id ON task_comments(comment_id);
CREATE INDEX idx_task_comments_task_id ON task_comments(task_id);
CREATE INDEX idx_task_comments_author_id ON task_comments(author_id);
CREATE INDEX idx_task_comments_created_at ON task_comments(created_at);

-- Task attachments and evidence
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

-- Indexes for attachments
CREATE INDEX idx_task_attachments_attachment_id ON task_attachments(attachment_id);
CREATE INDEX idx_task_attachments_task_id ON task_attachments(task_id);
CREATE INDEX idx_task_attachments_is_evidence ON task_attachments(is_evidence);
