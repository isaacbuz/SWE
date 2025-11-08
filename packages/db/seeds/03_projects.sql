-- Seed data for projects table
-- Sample projects for development and testing

-- Note: Replace user_id with actual ID from users table if different
INSERT INTO projects (
    name, description, slug, repository_url, repository_provider, repository_owner, repository_name,
    status, is_public, owner_id, technology_stack, config, metadata
) VALUES
    (
        'AI Engineering Platform',
        'The core AI-First Software Engineering Platform',
        'ai-eng-platform',
        'https://github.com/ai-company/ai-eng-platform',
        'github',
        'ai-company',
        'ai-eng-platform',
        'active',
        true,
        1,
        '["python", "fastapi", "react", "typescript", "postgresql", "redis"]',
        '{"default_branch": "main", "require_pr_reviews": 2, "auto_merge_enabled": false}',
        '{"team_size": 12, "criticality": "high", "sla_uptime": "99.9"}'
    ),
    (
        'MoE Router Service',
        'Mixture of Experts routing intelligence for agent selection',
        'moe-router',
        'https://github.com/ai-company/moe-router',
        'github',
        'ai-company',
        'moe-router',
        'active',
        true,
        1,
        '["python", "fastapi", "numpy", "scikit-learn"]',
        '{"default_branch": "main", "require_pr_reviews": 2}',
        '{"team_size": 4, "criticality": "high"}'
    ),
    (
        'Frontend UI',
        'Next.js premium UI with shadcn/ui components',
        'frontend-ui',
        'https://github.com/ai-company/frontend-ui',
        'github',
        'ai-company',
        'frontend-ui',
        'active',
        true,
        1,
        '["typescript", "react", "next.js", "tailwind", "zustand"]',
        '{"default_branch": "main", "require_pr_reviews": 1}',
        '{"team_size": 5, "criticality": "high"}'
    ),
    (
        'Agent Library',
        'Specialized agent implementations and tools',
        'agent-library',
        'https://github.com/ai-company/agent-library',
        'github',
        'ai-company',
        'agent-library',
        'active',
        true,
        1,
        '["python", "pydantic", "anthropic", "openai"]',
        '{"default_branch": "main", "require_pr_reviews": 2}',
        '{"team_size": 8, "criticality": "high"}'
    ),
    (
        'Integration Hub',
        'External API integrations and connectors',
        'integration-hub',
        'https://github.com/ai-company/integration-hub',
        'github',
        'ai-company',
        'integration-hub',
        'active',
        false,
        1,
        '["python", "fastapi", "requests"]',
        '{"default_branch": "main", "require_pr_reviews": 1}',
        '{"team_size": 3, "criticality": "medium"}'
    )
ON CONFLICT (slug) DO NOTHING;
