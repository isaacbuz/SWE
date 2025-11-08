-- Skills Database Schema
-- Manages Claude Skills marketplace, execution, and analytics

-- Skills table - Core skill definitions
CREATE TABLE IF NOT EXISTS skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL, -- URL-friendly identifier
    description TEXT NOT NULL,
    detailed_description TEXT, -- Markdown documentation
    version VARCHAR(50) NOT NULL, -- Semantic versioning: major.minor.patch

    -- Author information
    author_id UUID REFERENCES users(id) ON DELETE SET NULL,
    author_name VARCHAR(255),
    author_email VARCHAR(255),
    organization VARCHAR(255),

    -- Categorization
    category VARCHAR(50) NOT NULL, -- CODE_GENERATION, TESTING, SECURITY, etc.
    tags TEXT[], -- Searchable tags

    -- Execution configuration
    prompt_template TEXT NOT NULL, -- Jinja2 template
    input_schema JSONB NOT NULL, -- JSON Schema for inputs
    output_schema JSONB NOT NULL, -- JSON Schema for outputs
    examples JSONB, -- Usage examples array

    -- Model preferences
    model_preferences JSONB DEFAULT '{
        "preferred_models": ["claude-sonnet-4"],
        "min_quality": 0.8,
        "max_cost": null,
        "temperature": 0.7
    }'::jsonb,

    -- Dependencies
    dependencies JSONB DEFAULT '{
        "skills": [],
        "tools": [],
        "integrations": []
    }'::jsonb,

    -- Quality & validation
    validation_rules JSONB, -- Array of validation rules
    test_cases JSONB, -- Array of test cases
    quality_score DECIMAL(3,2) CHECK (quality_score >= 0 AND quality_score <= 1),

    -- Marketplace
    visibility VARCHAR(20) DEFAULT 'public' CHECK (visibility IN ('public', 'private', 'unlisted')),
    license VARCHAR(50) DEFAULT 'MIT',
    pricing_model VARCHAR(20) DEFAULT 'free' CHECK (pricing_model IN ('free', 'paid', 'freemium')),
    price_per_execution DECIMAL(10,4), -- USD per execution

    -- Stats
    download_count INTEGER DEFAULT 0,
    installation_count INTEGER DEFAULT 0,
    execution_count INTEGER DEFAULT 0,
    avg_rating DECIMAL(3,2) DEFAULT 0 CHECK (avg_rating >= 0 AND avg_rating <= 5),
    review_count INTEGER DEFAULT 0,

    -- Status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('draft', 'active', 'deprecated', 'archived')),
    deprecated_reason TEXT,
    replacement_skill_id UUID REFERENCES skills(id),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP WITH TIME ZONE,
    deprecated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for skills
CREATE INDEX idx_skills_slug ON skills(slug);
CREATE INDEX idx_skills_category ON skills(category);
CREATE INDEX idx_skills_author_id ON skills(author_id);
CREATE INDEX idx_skills_visibility ON skills(visibility);
CREATE INDEX idx_skills_status ON skills(status);
CREATE INDEX idx_skills_tags ON skills USING GIN(tags);
CREATE INDEX idx_skills_avg_rating ON skills(avg_rating DESC);
CREATE INDEX idx_skills_download_count ON skills(download_count DESC);
CREATE INDEX idx_skills_updated_at ON skills(updated_at DESC);

-- Skill versions table - Track version history
CREATE TABLE IF NOT EXISTS skill_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,

    -- Version-specific data (snapshot)
    prompt_template TEXT NOT NULL,
    input_schema JSONB NOT NULL,
    output_schema JSONB NOT NULL,
    model_preferences JSONB,
    validation_rules JSONB,

    -- Changelog
    changelog TEXT, -- Markdown changelog
    breaking_changes BOOLEAN DEFAULT FALSE,
    migration_guide TEXT, -- How to migrate from previous version

    -- Status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'deprecated', 'yanked')),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(skill_id, version)
);

CREATE INDEX idx_skill_versions_skill_id ON skill_versions(skill_id);
CREATE INDEX idx_skill_versions_created_at ON skill_versions(created_at DESC);

-- Skill installations - Track who has installed which Skills
CREATE TABLE IF NOT EXISTS skill_installations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,

    -- Settings
    auto_update BOOLEAN DEFAULT TRUE, -- Auto-update minor/patch versions
    enabled BOOLEAN DEFAULT TRUE,
    custom_config JSONB, -- User-specific configuration overrides

    installed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE,
    use_count INTEGER DEFAULT 0,

    UNIQUE(skill_id, user_id)
);

CREATE INDEX idx_skill_installations_user_id ON skill_installations(user_id);
CREATE INDEX idx_skill_installations_skill_id ON skill_installations(skill_id);
CREATE INDEX idx_skill_installations_last_used_at ON skill_installations(last_used_at DESC);

-- Skill executions - Track every skill execution
CREATE TABLE IF NOT EXISTS skill_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    skill_version VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Execution details
    inputs JSONB NOT NULL,
    outputs JSONB,
    rendered_prompt TEXT, -- Final prompt sent to model

    -- Model used
    model_id VARCHAR(100),
    model_provider VARCHAR(50),

    -- Results
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'failed', 'timeout', 'canceled')),
    error_message TEXT,
    validation_passed BOOLEAN,
    validation_results JSONB,

    -- Performance
    latency_ms INTEGER, -- Execution time in milliseconds
    tokens_input INTEGER,
    tokens_output INTEGER,
    cost_usd DECIMAL(10,6),

    -- Context
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    workflow_id VARCHAR(255), -- Temporal workflow ID
    parent_execution_id UUID REFERENCES skill_executions(id), -- For chained Skills

    -- Caching
    cache_hit BOOLEAN DEFAULT FALSE,
    cache_key VARCHAR(255),

    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_skill_executions_skill_id ON skill_executions(skill_id);
CREATE INDEX idx_skill_executions_user_id ON skill_executions(user_id);
CREATE INDEX idx_skill_executions_status ON skill_executions(status);
CREATE INDEX idx_skill_executions_executed_at ON skill_executions(executed_at DESC);
CREATE INDEX idx_skill_executions_agent_id ON skill_executions(agent_id);
CREATE INDEX idx_skill_executions_cache_key ON skill_executions(cache_key);

-- Skill reviews - User ratings and reviews
CREATE TABLE IF NOT EXISTS skill_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(255),
    review_text TEXT,

    -- Helpful votes
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0,

    -- Verification
    verified_purchase BOOLEAN DEFAULT FALSE, -- User has executed this Skill

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(skill_id, user_id)
);

CREATE INDEX idx_skill_reviews_skill_id ON skill_reviews(skill_id);
CREATE INDEX idx_skill_reviews_user_id ON skill_reviews(user_id);
CREATE INDEX idx_skill_reviews_rating ON skill_reviews(rating DESC);
CREATE INDEX idx_skill_reviews_created_at ON skill_reviews(created_at DESC);

-- Skill favorites - User favorites
CREATE TABLE IF NOT EXISTS skill_favorites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(skill_id, user_id)
);

CREATE INDEX idx_skill_favorites_user_id ON skill_favorites(user_id);
CREATE INDEX idx_skill_favorites_skill_id ON skill_favorites(skill_id);

-- Skill analytics - Aggregate daily analytics
CREATE TABLE IF NOT EXISTS skill_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    date DATE NOT NULL,

    -- Execution metrics
    executions_total INTEGER DEFAULT 0,
    executions_success INTEGER DEFAULT 0,
    executions_failed INTEGER DEFAULT 0,

    -- Performance metrics
    avg_latency_ms INTEGER,
    p50_latency_ms INTEGER,
    p95_latency_ms INTEGER,
    p99_latency_ms INTEGER,

    -- Cost metrics
    total_cost_usd DECIMAL(10,2) DEFAULT 0,
    avg_cost_per_execution DECIMAL(10,6),

    -- Engagement metrics
    unique_users INTEGER DEFAULT 0,
    new_installations INTEGER DEFAULT 0,
    new_reviews INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(skill_id, date)
);

CREATE INDEX idx_skill_analytics_skill_id ON skill_analytics(skill_id);
CREATE INDEX idx_skill_analytics_date ON skill_analytics(date DESC);

-- Functions for updating aggregates
CREATE OR REPLACE FUNCTION update_skill_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Update execution count
    IF TG_OP = 'INSERT' AND TG_TABLE_NAME = 'skill_executions' THEN
        UPDATE skills
        SET execution_count = execution_count + 1
        WHERE id = NEW.skill_id;
    END IF;

    -- Update installation count
    IF TG_OP = 'INSERT' AND TG_TABLE_NAME = 'skill_installations' THEN
        UPDATE skills
        SET installation_count = installation_count + 1
        WHERE id = NEW.skill_id;
    END IF;

    -- Update rating
    IF TG_OP IN ('INSERT', 'UPDATE', 'DELETE') AND TG_TABLE_NAME = 'skill_reviews' THEN
        UPDATE skills
        SET
            avg_rating = (SELECT AVG(rating) FROM skill_reviews WHERE skill_id = COALESCE(NEW.skill_id, OLD.skill_id)),
            review_count = (SELECT COUNT(*) FROM skill_reviews WHERE skill_id = COALESCE(NEW.skill_id, OLD.skill_id))
        WHERE id = COALESCE(NEW.skill_id, OLD.skill_id);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for auto-updating stats
CREATE TRIGGER trigger_skill_execution_stats
AFTER INSERT ON skill_executions
FOR EACH ROW
EXECUTE FUNCTION update_skill_stats();

CREATE TRIGGER trigger_skill_installation_stats
AFTER INSERT ON skill_installations
FOR EACH ROW
EXECUTE FUNCTION update_skill_stats();

CREATE TRIGGER trigger_skill_review_stats
AFTER INSERT OR UPDATE OR DELETE ON skill_reviews
FOR EACH ROW
EXECUTE FUNCTION update_skill_stats();

-- Comments for documentation
COMMENT ON TABLE skills IS 'Core skills definitions in the marketplace';
COMMENT ON TABLE skill_versions IS 'Version history for skills with semantic versioning';
COMMENT ON TABLE skill_installations IS 'Tracks which users have installed which skills';
COMMENT ON TABLE skill_executions IS 'Audit log of all skill executions with performance metrics';
COMMENT ON TABLE skill_reviews IS 'User ratings and reviews for skills';
COMMENT ON TABLE skill_favorites IS 'User favorites for quick access';
COMMENT ON TABLE skill_analytics IS 'Daily aggregate analytics per skill';
