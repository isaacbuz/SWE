-- Seed data for users table
-- Development and testing user accounts

INSERT INTO users (
    username, email, display_name, password_hash, role, is_active, is_service_account, github_username, metadata, preferences
) VALUES
    (
        'admin',
        'admin@example.com',
        'Admin User',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUExMgJa', -- password: 'admin' (hashed)
        'admin',
        true,
        false,
        'admin-github',
        '{"organization": "ai-company", "role": "founder"}',
        '{"theme": "dark", "notifications_enabled": true}'
    ),
    (
        'orchestrator-bot',
        'orchestrator@ai-company.com',
        'Orchestrator Bot',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUExMgJa',
        'service',
        true,
        true,
        'ai-orchestrator-bot',
        '{"service": "orchestrator", "version": "1.0.0"}',
        '{"auto_assign_tasks": true}'
    ),
    (
        'engineer-1',
        'engineer1@example.com',
        'Senior Engineer',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUExMgJa',
        'user',
        true,
        false,
        'engineer1-github',
        '{"department": "engineering", "level": "senior"}',
        '{"theme": "light", "notifications_enabled": true}'
    ),
    (
        'engineer-2',
        'engineer2@example.com',
        'Staff Engineer',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUExMgJa',
        'user',
        true,
        false,
        'engineer2-github',
        '{"department": "engineering", "level": "staff"}',
        '{"theme": "dark", "notifications_enabled": true}'
    ),
    (
        'manager-1',
        'manager@example.com',
        'Engineering Manager',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUExMgJa',
        'manager',
        true,
        false,
        'manager-github',
        '{"department": "management", "reports": 5}',
        '{"theme": "light", "daily_digest": true}'
    )
ON CONFLICT (username) DO NOTHING;
