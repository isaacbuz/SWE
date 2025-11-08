-- Evidence Registry: Track sources of truth for every AI decision with credibility scoring
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

-- Indexes for evidence queries
CREATE INDEX idx_evidence_evidence_id ON evidence(evidence_id);
CREATE INDEX idx_evidence_task_id ON evidence(task_id);
CREATE INDEX idx_evidence_project_id ON evidence(project_id);
CREATE INDEX idx_evidence_source_type ON evidence(source_type);
CREATE INDEX idx_evidence_credibility_score ON evidence(credibility_score);
CREATE INDEX idx_evidence_is_verified ON evidence(is_verified);
CREATE INDEX idx_evidence_created_at ON evidence(created_at);
CREATE INDEX idx_evidence_tags ON evidence USING GIN(tags);

-- Evidence credibility history for tracking changes over time
CREATE TABLE IF NOT EXISTS evidence_credibility_history (
    id SERIAL PRIMARY KEY,
    evidence_id UUID NOT NULL REFERENCES evidence(evidence_id) ON DELETE CASCADE,
    previous_credibility_score NUMERIC(4, 3),
    new_credibility_score NUMERIC(4, 3) NOT NULL,
    reason VARCHAR(255),
    updated_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for credibility history
CREATE INDEX idx_evidence_credibility_history_evidence_id ON evidence_credibility_history(evidence_id);
CREATE INDEX idx_evidence_credibility_history_created_at ON evidence_credibility_history(created_at);

-- Evidence chains for tracing decision lineage
CREATE TABLE IF NOT EXISTS evidence_chains (
    id SERIAL PRIMARY KEY,
    chain_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    primary_evidence_id UUID NOT NULL REFERENCES evidence(evidence_id) ON DELETE CASCADE,
    supporting_evidence JSONB NOT NULL DEFAULT '[]',
    decision_description TEXT,
    decision_confidence NUMERIC(4, 3),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for evidence chains
CREATE INDEX idx_evidence_chains_chain_id ON evidence_chains(chain_id);
CREATE INDEX idx_evidence_chains_primary_evidence ON evidence_chains(primary_evidence_id);
CREATE INDEX idx_evidence_chains_created_at ON evidence_chains(created_at);
