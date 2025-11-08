-- Projects table: Core entity representing a software project
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

-- Indexes for common queries
CREATE INDEX idx_projects_project_id ON projects(project_id);
CREATE INDEX idx_projects_slug ON projects(slug);
CREATE INDEX idx_projects_owner_id ON projects(owner_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_created_at ON projects(created_at);
CREATE INDEX idx_projects_repository_url ON projects(repository_url);
CREATE INDEX idx_projects_is_public ON projects(is_public);
