-- PostgreSQL Initialization Script for AI-First SWE Company
-- This script is automatically executed when the postgres container starts
-- IMPORTANT: This is for development only. Production should use Alembic migrations.

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS agents;
CREATE SCHEMA IF NOT EXISTS workflows;
CREATE SCHEMA IF NOT EXISTS integrations;
CREATE SCHEMA IF NOT EXISTS audit;

-- ===== Auth Schema =====
CREATE TABLE IF NOT EXISTS auth.users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email VARCHAR(255) UNIQUE NOT NULL,
  username VARCHAR(100) UNIQUE NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  is_active BOOLEAN DEFAULT true,
  is_superuser BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS auth.api_keys (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  key_hash VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  last_used_at TIMESTAMP NULL,
  expires_at TIMESTAMP NULL,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===== Agents Schema =====
CREATE TABLE IF NOT EXISTS agents.agent_definitions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(255) UNIQUE NOT NULL,
  description TEXT,
  agent_type VARCHAR(100) NOT NULL,
  capabilities TEXT[] DEFAULT '{}',
  is_active BOOLEAN DEFAULT true,
  config JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agents.agent_executions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id UUID NOT NULL REFERENCES agents.agent_definitions(id),
  status VARCHAR(50) NOT NULL,
  input_data JSONB,
  output_data JSONB,
  error_message TEXT,
  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP NULL,
  execution_time_ms INTEGER
);

-- ===== Workflows Schema =====
CREATE TABLE IF NOT EXISTS workflows.workflow_definitions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(255) UNIQUE NOT NULL,
  description TEXT,
  version INTEGER DEFAULT 1,
  definition JSONB NOT NULL,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workflows.workflow_executions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workflow_id UUID NOT NULL REFERENCES workflows.workflow_definitions(id),
  workflow_name VARCHAR(255),
  status VARCHAR(50) NOT NULL,
  input_data JSONB,
  output_data JSONB,
  error_message TEXT,
  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP NULL,
  execution_time_ms INTEGER
);

-- ===== Integrations Schema =====
CREATE TABLE IF NOT EXISTS integrations.github_integrations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  repository VARCHAR(255) UNIQUE NOT NULL,
  app_id VARCHAR(100),
  webhook_secret_hash VARCHAR(255),
  is_active BOOLEAN DEFAULT true,
  config JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS integrations.integration_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  integration_id UUID NOT NULL REFERENCES integrations.github_integrations(id),
  event_type VARCHAR(100) NOT NULL,
  event_data JSONB NOT NULL,
  processed BOOLEAN DEFAULT false,
  processed_at TIMESTAMP NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===== Audit Schema =====
CREATE TABLE IF NOT EXISTS audit.audit_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  action VARCHAR(100) NOT NULL,
  resource_type VARCHAR(100) NOT NULL,
  resource_id VARCHAR(255),
  old_values JSONB,
  new_values JSONB,
  ip_address VARCHAR(45),
  user_agent TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===== Indexes for performance =====

-- Auth indexes
CREATE INDEX idx_users_email ON auth.users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_username ON auth.users(username) WHERE deleted_at IS NULL;
CREATE INDEX idx_api_keys_user_id ON auth.api_keys(user_id);
CREATE INDEX idx_api_keys_active ON auth.api_keys(is_active);

-- Agent indexes
CREATE INDEX idx_agent_executions_agent_id ON agents.agent_executions(agent_id);
CREATE INDEX idx_agent_executions_status ON agents.agent_executions(status);
CREATE INDEX idx_agent_executions_created_at ON agents.agent_executions(created_at);

-- Workflow indexes
CREATE INDEX idx_workflow_executions_workflow_id ON workflows.workflow_executions(workflow_id);
CREATE INDEX idx_workflow_executions_status ON workflows.workflow_executions(status);
CREATE INDEX idx_workflow_executions_created_at ON workflows.workflow_executions(created_at);

-- Integration indexes
CREATE INDEX idx_integration_events_integration_id ON integrations.integration_events(integration_id);
CREATE INDEX idx_integration_events_processed ON integrations.integration_events(processed);

-- Audit indexes
CREATE INDEX idx_audit_log_user_id ON audit.audit_log(user_id);
CREATE INDEX idx_audit_log_resource_type ON audit.audit_log(resource_type);
CREATE INDEX idx_audit_log_created_at ON audit.audit_log(created_at);

-- ===== Create default user for development =====
-- IMPORTANT: Change password in production!
INSERT INTO auth.users (email, username, hashed_password, is_superuser)
VALUES (
  'admin@ai-company.local',
  'admin',
  -- Password: 'admin' (use proper hashing in production!)
  crypt('admin', gen_salt('bf')),
  true
)
ON CONFLICT (email) DO NOTHING;

-- ===== Create sample agent definitions =====
INSERT INTO agents.agent_definitions (name, agent_type, description, capabilities)
VALUES
  ('Architect Agent', 'architect', 'Designs system architecture', ARRAY['design', 'planning', 'documentation']),
  ('Code Agent', 'codegen', 'Generates code', ARRAY['coding', 'implementation', 'refactoring']),
  ('Tester Agent', 'tester', 'Tests code', ARRAY['testing', 'coverage', 'quality']),
  ('Security Agent', 'security', 'Security scanning', ARRAY['scanning', 'audit', 'compliance'])
ON CONFLICT (name) DO NOTHING;

-- ===== Grant permissions =====
-- For app user (if different from postgres)
-- GRANT CONNECT ON DATABASE ai_company_db TO app_user;
-- GRANT USAGE ON SCHEMA auth, agents, workflows, integrations, audit TO app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA auth, agents, workflows, integrations, audit TO app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA auth, agents, workflows, integrations, audit TO app_user;

-- ===== Notes for production =====
-- 1. Use Alembic for schema migrations instead of this script
-- 2. Implement proper encryption for sensitive data
-- 3. Set up proper backup policies
-- 4. Use distinct database users with minimal required permissions
-- 5. Enable audit logging for all modifications
-- 6. Implement row-level security (RLS) policies
-- 7. Set up monitoring and alerting
-- 8. Regular maintenance (VACUUM, ANALYZE)
-- 9. Implement connection pooling
-- 10. Set up proper logging and monitoring
