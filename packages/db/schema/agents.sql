-- Agent Registry: Track all AI agents in the system with their capabilities and versions
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

-- Indexes for common queries
CREATE INDEX idx_agents_agent_id ON agents(agent_id);
CREATE INDEX idx_agents_name ON agents(name);
CREATE INDEX idx_agents_type ON agents(agent_type);
CREATE INDEX idx_agents_is_active ON agents(is_active);
CREATE INDEX idx_agents_model_provider ON agents(model_provider);
CREATE INDEX idx_agents_tags ON agents USING GIN(tags);
CREATE INDEX idx_agents_created_at ON agents(created_at);

-- Agent execution history for auditing and performance tracking
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

-- Indexes for execution tracking
CREATE INDEX idx_agent_executions_execution_id ON agent_executions(execution_id);
CREATE INDEX idx_agent_executions_agent_id ON agent_executions(agent_id);
CREATE INDEX idx_agent_executions_task_id ON agent_executions(task_id);
CREATE INDEX idx_agent_executions_project_id ON agent_executions(project_id);
CREATE INDEX idx_agent_executions_status ON agent_executions(status);
CREATE INDEX idx_agent_executions_created_at ON agent_executions(created_at);
