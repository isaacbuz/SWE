# Database Schema Documentation

Complete schema reference for the AI-First Software Engineering Platform database.

## Entity-Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USERS (Human & Service)                         │
├─────────────────────────────────────────────────────────────────────────┤
│ user_id: UUID PK                                                        │
│ username: VARCHAR(255) UNIQUE                                           │
│ email: VARCHAR(255) UNIQUE                                              │
│ role: admin|manager|user|service                                        │
│ github_*: OAuth/SSO fields                                              │
│ metadata, preferences: JSONB                                            │
│ created_at, updated_at: TIMESTAMP                                       │
└─────────────────────────────────────────────────────────────────────────┘
           │
           ├─────────────┬──────────────┬──────────────┐
           │             │              │              │
           ▼             ▼              ▼              ▼
      ┌────────┐  ┌──────────┐  ┌────────────┐  ┌──────────────┐
      │PROJECTS│  │  AGENTS  │  │AGENT_EXECS │  │ AUDIT_LOGS   │
      └────────┘  └──────────┘  └────────────┘  └──────────────┘
           │           │             │
           ├───────────┴─────────────┤
           │                         │
           ▼                         ▼
      ┌────────┐             ┌──────────────┐
      │ TASKS  │             │  EVIDENCE    │
      └────────┘             └──────────────┘
           │                         │
           ├─────────────────────────┤
           │                         │
           ▼                         ▼
      ┌──────────────┐       ┌───────────────┐
      │TASK_COMMENTS │       │TASK_ATTACHMENTS
      └──────────────┘       └───────────────┘
```

## Core Tables

### 1. users

**Purpose**: User accounts (human operators and service bots)

| Column                  | Type                     | Constraints                       | Notes                         |
| ----------------------- | ------------------------ | --------------------------------- | ----------------------------- |
| id                      | SERIAL                   | PRIMARY KEY                       | Internal ID                   |
| user_id                 | UUID                     | UNIQUE, DEFAULT gen_random_uuid() | External ID                   |
| username                | VARCHAR(255)             | UNIQUE, NOT NULL                  | Login name                    |
| email                   | VARCHAR(255)             | UNIQUE, NOT NULL                  | Contact                       |
| display_name            | VARCHAR(255)             |                                   | Full name                     |
| password_hash           | VARCHAR(255)             | NOT NULL                          | Bcrypt hash                   |
| role                    | VARCHAR(50)              | CHECK, DEFAULT 'user'             | admin, manager, user, service |
| is_active               | BOOLEAN                  | DEFAULT true                      | Account status                |
| is_service_account      | BOOLEAN                  | DEFAULT false                     | Bot flag                      |
| github_username         | VARCHAR(255)             |                                   | GitHub handle                 |
| github_user_id          | BIGINT                   | UNIQUE                            | GitHub ID                     |
| github_access_token     | VARCHAR(500)             |                                   | OAuth token                   |
| github_token_expires_at | TIMESTAMP WITH TIME ZONE |                                   | Token expiry                  |
| metadata                | JSONB                    | DEFAULT '{}'                      | Flexible data                 |
| preferences             | JSONB                    | DEFAULT '{}'                      | User preferences              |
| created_at              | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                     |                               |
| updated_at              | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                     |                               |
| last_login_at           | TIMESTAMP WITH TIME ZONE |                                   |                               |
| deleted_at              | TIMESTAMP WITH TIME ZONE |                                   | Soft delete                   |

**Indexes**: user_id, username, email, github_username, is_active, created_at

**Usage**: Authentication, authorization, activity tracking

---

### 2. projects

**Purpose**: Software projects managed by the platform

| Column                      | Type                     | Constraints                       | Notes                     |
| --------------------------- | ------------------------ | --------------------------------- | ------------------------- |
| id                          | SERIAL                   | PRIMARY KEY                       | Internal ID               |
| project_id                  | UUID                     | UNIQUE, DEFAULT gen_random_uuid() | External ID               |
| name                        | VARCHAR(255)             | NOT NULL                          | Project name              |
| description                 | TEXT                     |                                   | Project description       |
| slug                        | VARCHAR(255)             | UNIQUE, NOT NULL                  | URL-friendly ID           |
| repository_url              | VARCHAR(500)             |                                   | GitHub/GitLab URL         |
| repository_provider         | VARCHAR(50)              | CHECK                             | github, gitlab, bitbucket |
| repository_owner            | VARCHAR(255)             |                                   | Owner name                |
| repository_name             | VARCHAR(255)             |                                   | Repo name                 |
| default_branch              | VARCHAR(100)             | DEFAULT 'main'                    | Default branch            |
| config                      | JSONB                    | DEFAULT '{}'                      | Project config            |
| technology_stack            | JSONB                    | DEFAULT '[]'                      | Tech array                |
| metadata                    | JSONB                    | DEFAULT '{}'                      | Flexible data             |
| status                      | VARCHAR(50)              | CHECK, DEFAULT 'active'           | active, archived, deleted |
| is_public                   | BOOLEAN                  | DEFAULT false                     | Visibility                |
| is_template                 | BOOLEAN                  | DEFAULT false                     | Template flag             |
| owner_id                    | INTEGER                  | FK(users), NOT NULL               | Project owner             |
| team_members                | JSONB                    | DEFAULT '[]'                      | Team array                |
| average_review_time_minutes | INTEGER                  |                                   | Metric                    |
| average_merge_time_minutes  | INTEGER                  |                                   | Metric                    |
| pr_merge_rate               | NUMERIC(5,2)             |                                   | 0-100%                    |
| test_coverage_percent       | NUMERIC(5,2)             |                                   | 0-100%                    |
| created_at                  | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                     |                           |
| updated_at                  | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                     |                           |
| last_activity_at            | TIMESTAMP WITH TIME ZONE |                                   |                           |
| archived_at                 | TIMESTAMP WITH TIME ZONE |                                   |                           |

**Indexes**: project_id, slug, owner_id, status, created_at, repository_url, is_public

**Usage**: Project management, team assignment, metrics tracking

---

### 3. agents

**Purpose**: AI agent registry with capabilities and performance metrics

| Column                | Type                     | Constraints                       | Notes                                       |
| --------------------- | ------------------------ | --------------------------------- | ------------------------------------------- |
| id                    | SERIAL                   | PRIMARY KEY                       | Internal ID                                 |
| agent_id              | UUID                     | UNIQUE, DEFAULT gen_random_uuid() | External ID                                 |
| name                  | VARCHAR(255)             | UNIQUE, NOT NULL                  | System name                                 |
| display_name          | VARCHAR(255)             | NOT NULL                          | Human name                                  |
| description           | TEXT                     |                                   | Agent description                           |
| agent_type            | VARCHAR(100)             | CHECK, NOT NULL                   | orchestrator, architect, codegen, etc.      |
| model_provider        | VARCHAR(50)              | CHECK, NOT NULL                   | anthropic, openai, google, ibm, qwen, local |
| model_name            | VARCHAR(255)             | NOT NULL                          | claude-opus, gpt-4, etc.                    |
| model_version         | VARCHAR(100)             |                                   | Version string                              |
| capabilities          | JSONB                    | DEFAULT '{}'                      | Feature flags                               |
| configuration         | JSONB                    | DEFAULT '{}'                      | Agent config                                |
| required_tools        | JSONB                    | DEFAULT '[]'                      | Tool dependencies                           |
| max_tokens            | INTEGER                  | DEFAULT 4096                      | Context window                              |
| temperature           | NUMERIC(3,2)             | DEFAULT 0.7                       | Sampling parameter                          |
| top_p                 | NUMERIC(3,2)             | DEFAULT 0.9                       | Nucleus sampling                            |
| success_rate          | NUMERIC(5,2)             | DEFAULT 0.0                       | Percentage                                  |
| avg_execution_time_ms | INTEGER                  | DEFAULT 0                         | Performance metric                          |
| total_executions      | BIGINT                   | DEFAULT 0                         | Run count                                   |
| last_used_at          | TIMESTAMP WITH TIME ZONE |                                   | Last execution                              |
| is_active             | BOOLEAN                  | DEFAULT true                      | Deployment status                           |
| is_experimental       | BOOLEAN                  | DEFAULT false                     | Beta flag                                   |
| version               | VARCHAR(20)              | DEFAULT '1.0.0'                   | Agent version                               |
| deprecated_at         | TIMESTAMP WITH TIME ZONE |                                   | Deprecation date                            |
| tags                  | JSONB                    | DEFAULT '[]'                      | Search tags                                 |
| metadata              | JSONB                    | DEFAULT '{}'                      | Flexible data                               |
| created_at            | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                     |                                             |
| updated_at            | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                     |                                             |
| created_by            | INTEGER                  | FK(users)                         | Creator                                     |

**Indexes**: agent_id, name, type, is_active, model_provider, tags, created_at

**Usage**: Agent selection, capability matching, performance monitoring

---

### 4. tasks

**Purpose**: Issues, pull requests, and work items

| Column               | Type                     | Constraints                       | Notes                                                |
| -------------------- | ------------------------ | --------------------------------- | ---------------------------------------------------- |
| id                   | SERIAL                   | PRIMARY KEY                       | Internal ID                                          |
| task_id              | UUID                     | UNIQUE, DEFAULT gen_random_uuid() | External ID                                          |
| project_id           | UUID                     | FK(projects), NOT NULL            | Parent project                                       |
| github_issue_number  | INTEGER                  |                                   | GitHub issue #                                       |
| github_pr_number     | INTEGER                  |                                   | GitHub PR #                                          |
| github_node_id       | VARCHAR(255)             |                                   | GitHub GraphQL ID                                    |
| github_url           | VARCHAR(500)             |                                   | GitHub URL                                           |
| title                | VARCHAR(500)             | NOT NULL                          | Task title                                           |
| description          | TEXT                     |                                   | Full description                                     |
| type                 | VARCHAR(50)              | CHECK, NOT NULL                   | bug, feature, refactor, test, docs, task, chore      |
| status               | VARCHAR(50)              | CHECK, DEFAULT 'open'             | open, in_progress, in_review, blocked, closed, draft |
| priority             | VARCHAR(20)              | CHECK, DEFAULT 'medium'           | critical, high, medium, low                          |
| assigned_to_user_id  | INTEGER                  | FK(users)                         | Human assignee                                       |
| assigned_to_agent_id | UUID                     | FK(agents)                        | Agent assignee                                       |
| created_by_user_id   | INTEGER                  | FK(users)                         | Creator                                              |
| parent_task_id       | UUID                     | FK(tasks)                         | Parent/epic                                          |
| related_tasks        | JSONB                    | DEFAULT '[]'                      | Related IDs                                          |
| estimated_hours      | NUMERIC(6,2)             |                                   | Estimate                                             |
| actual_hours         | NUMERIC(6,2)             |                                   | Actual time                                          |
| complexity_score     | INTEGER                  | CHECK                             | 1-13 (Fibonacci)                                     |
| files_changed        | INTEGER                  |                                   | File count                                           |
| lines_added          | INTEGER                  |                                   | Line count                                           |
| lines_deleted        | INTEGER                  |                                   | Line count                                           |
| ai_analysis          | JSONB                    | DEFAULT '{}'                      | AI results                                           |
| ai_suggestions       | JSONB                    | DEFAULT '[]'                      | Suggestions                                          |
| labels               | JSONB                    | DEFAULT '[]'                      | Tag array                                            |
| metadata             | JSONB                    | DEFAULT '{}'                      | Flexible data                                        |
| created_at           | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                     |                                                      |
| updated_at           | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                     |                                                      |
| started_at           | TIMESTAMP WITH TIME ZONE |                                   |                                                      |
| completed_at         | TIMESTAMP WITH TIME ZONE |                                   |                                                      |
| due_date             | TIMESTAMP WITH TIME ZONE |                                   |                                                      |

**Indexes**: task_id, project_id, status, priority, type, assigned_to_user, assigned_to_agent, github_issue, github_pr, created_at, parent_task, labels

**Usage**: Workflow management, AI assignments, GitHub integration

---

### 5. evidence

**Purpose**: Evidence registry with credibility scoring for decision traceability

| Column                 | Type                     | Constraints                       | Notes                                             |
| ---------------------- | ------------------------ | --------------------------------- | ------------------------------------------------- |
| id                     | SERIAL                   | PRIMARY KEY                       | Internal ID                                       |
| evidence_id            | UUID                     | UNIQUE, DEFAULT gen_random_uuid() | External ID                                       |
| task_id                | UUID                     | FK(tasks)                         | Related task                                      |
| project_id             | UUID                     | FK(projects)                      | Related project                                   |
| source_type            | VARCHAR(100)             | CHECK, NOT NULL                   | code_analysis, test_result, ai_model_output, etc. |
| source_name            | VARCHAR(255)             | NOT NULL                          | Source identifier                                 |
| source_url             | VARCHAR(1000)            |                                   | Link to source                                    |
| title                  | VARCHAR(500)             | NOT NULL                          | Evidence title                                    |
| description            | TEXT                     |                                   | Details                                           |
| content                | TEXT                     |                                   | Full content                                      |
| raw_data               | JSONB                    | DEFAULT '{}'                      | Structured data                                   |
| credibility_score      | NUMERIC(4,3)             | CHECK, DEFAULT 0.5                | 0.0-1.0 confidence                                |
| confidence_level       | VARCHAR(20)              | CHECK                             | very_high, high, medium, low, very_low            |
| credibility_factors    | JSONB                    | DEFAULT '{}'                      | Scoring details                                   |
| historical_accuracy    | NUMERIC(5,2)             |                                   | Percentage                                        |
| is_verified            | BOOLEAN                  | DEFAULT false                     | Attestation flag                                  |
| verified_by_user_id    | INTEGER                  | FK(users)                         | Verifier                                          |
| verified_at            | TIMESTAMP WITH TIME ZONE |                                   | Verification time                                 |
| validation_notes       | TEXT                     |                                   | Notes                                             |
| related_evidence       | JSONB                    | DEFAULT '[]'                      | Related IDs                                       |
| contradicting_evidence | JSONB                    | DEFAULT '[]'                      | Conflicting IDs                                   |
| tags                   | JSONB                    | DEFAULT '[]'                      | Search tags                                       |
| metadata               | JSONB                    | DEFAULT '{}'                      | Flexible data                                     |
| created_at             | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                     |                                                   |
| updated_at             | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                     |                                                   |
| expires_at             | TIMESTAMP WITH TIME ZONE |                                   | Expiration                                        |

**Indexes**: evidence_id, task_id, project_id, source_type, credibility_score, is_verified, created_at, tags

**Usage**: Decision traceability, credibility assessment, audit trails

---

### 6. agent_executions

**Purpose**: Detailed audit trail for AI agent executions

| Column              | Type                     | Constraints                       | Notes                                       |
| ------------------- | ------------------------ | --------------------------------- | ------------------------------------------- |
| id                  | SERIAL                   | PRIMARY KEY                       | Internal ID                                 |
| execution_id        | UUID                     | UNIQUE, DEFAULT gen_random_uuid() | External ID                                 |
| agent_id            | UUID                     | FK(agents), NOT NULL              | Agent executed                              |
| task_id             | UUID                     | FK(tasks)                         | Associated task                             |
| project_id          | UUID                     | FK(projects)                      | Associated project                          |
| input_tokens        | INTEGER                  |                                   | Prompt tokens                               |
| output_tokens       | INTEGER                  |                                   | Completion tokens                           |
| total_tokens        | INTEGER                  |                                   | Total consumption                           |
| execution_time_ms   | INTEGER                  |                                   | Duration                                    |
| cost_usd            | NUMERIC(10,4)            |                                   | Billing cost                                |
| status              | VARCHAR(50)              | CHECK, NOT NULL                   | pending, running, success, failure, timeout |
| result              | JSONB                    |                                   | Output data                                 |
| error_message       | TEXT                     |                                   | Error details                               |
| evidence_id         | UUID                     | FK(evidence)                      | Supporting evidence                         |
| parent_execution_id | UUID                     | FK(agent_executions)              | Parent execution                            |
| started_at          | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                     |                                             |
| completed_at        | TIMESTAMP WITH TIME ZONE |                                   |                                             |
| created_at          | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                     |                                             |

**Indexes**: execution_id, agent_id, task_id, project_id, status, created_at

**Usage**: Cost tracking, performance monitoring, agent auditing

---

### 7. task_comments

**Purpose**: Comments on tasks/PRs with AI authorship tracking

| Column            | Type                     | Constraints                       | Notes                 |
| ----------------- | ------------------------ | --------------------------------- | --------------------- |
| id                | SERIAL                   | PRIMARY KEY                       | Internal ID           |
| comment_id        | UUID                     | UNIQUE, DEFAULT gen_random_uuid() | External ID           |
| task_id           | UUID                     | FK(tasks), NOT NULL               | Parent task           |
| author_id         | INTEGER                  | FK(users)                         | Human author          |
| agent_id          | UUID                     | FK(agents)                        | AI author             |
| content           | TEXT                     | NOT NULL                          | Comment text          |
| content_type      | VARCHAR(50)              | DEFAULT 'markdown'                | markdown, plain, html |
| github_comment_id | BIGINT                   | UNIQUE                            | GitHub integration    |
| is_ai_generated   | BOOLEAN                  | DEFAULT false                     | AI flag               |
| ai_metadata       | JSONB                    | DEFAULT '{}'                      | Generation details    |
| created_at        | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                     |                       |
| updated_at        | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                     |                       |
| deleted_at        | TIMESTAMP WITH TIME ZONE |                                   | Soft delete           |

**Indexes**: comment_id, task_id, author_id, created_at

**Usage**: Discussion history, AI transparency

---

### 8. task_attachments

**Purpose**: File attachments and evidence linking

| Column             | Type                     | Constraints                       | Notes         |
| ------------------ | ------------------------ | --------------------------------- | ------------- |
| id                 | SERIAL                   | PRIMARY KEY                       | Internal ID   |
| attachment_id      | UUID                     | UNIQUE, DEFAULT gen_random_uuid() | External ID   |
| task_id            | UUID                     | FK(tasks), NOT NULL               | Parent task   |
| file_name          | VARCHAR(500)             | NOT NULL                          | Original name |
| file_type          | VARCHAR(100)             |                                   | MIME type     |
| file_size_bytes    | BIGINT                   |                                   | File size     |
| storage_path       | VARCHAR(1000)            | NOT NULL                          | S3/GCS path   |
| is_evidence        | BOOLEAN                  | DEFAULT false                     | Evidence flag |
| evidence_id        | UUID                     | FK(evidence)                      | Evidence link |
| metadata           | JSONB                    | DEFAULT '{}'                      | Flexible data |
| created_at         | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                     |               |
| updated_by_user_id | INTEGER                  | FK(users)                         | Uploader      |

**Indexes**: attachment_id, task_id, is_evidence

**Usage**: File storage, evidence tracking

---

### 9. audit_logs

**Purpose**: Immutable event log for compliance and forensics

| Column          | Type                     | Constraints                       | Notes                                 |
| --------------- | ------------------------ | --------------------------------- | ------------------------------------- |
| id              | BIGSERIAL                | PRIMARY KEY                       | Internal ID                           |
| log_id          | UUID                     | UNIQUE, DEFAULT gen_random_uuid() | External ID                           |
| user_id         | INTEGER                  | FK(users)                         | Human actor                           |
| agent_id        | UUID                     | FK(agents)                        | AI actor                              |
| service_name    | VARCHAR(255)             |                                   | System service                        |
| event_type      | VARCHAR(100)             | CHECK, NOT NULL                   | 35+ event types                       |
| event_action    | VARCHAR(50)              | CHECK                             | create, read, update, delete, execute |
| resource_type   | VARCHAR(100)             |                                   | Entity type                           |
| resource_id     | VARCHAR(500)             |                                   | Entity ID                             |
| resource_name   | VARCHAR(500)             |                                   | Entity name                           |
| old_values      | JSONB                    |                                   | Previous state                        |
| new_values      | JSONB                    |                                   | New state                             |
| changes_summary | TEXT                     |                                   | Human summary                         |
| ip_address      | INET                     |                                   | Source IP                             |
| user_agent      | VARCHAR(1000)            |                                   | Browser/client                        |
| request_id      | VARCHAR(255)             |                                   | Correlation ID                        |
| session_id      | VARCHAR(255)             |                                   | Session ID                            |
| metadata        | JSONB                    | DEFAULT '{}'                      | Additional context                    |
| status          | VARCHAR(50)              | CHECK, DEFAULT 'success'          | success, failure, partial, unknown    |
| error_message   | TEXT                     |                                   | Error details                         |
| is_immutable    | BOOLEAN                  | NOT NULL, DEFAULT true            | Immutability constraint               |
| created_at      | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                     |                                       |

**Indexes**: log_id, user_id, agent_id, event_type, resource_type, resource_id, created_at, status, request_id

**Usage**: Compliance, forensics, debugging

---

### 10. activity_feed

**Purpose**: High-level activity summaries for user interface

| Column           | Type                     | Constraints                       | Notes       |
| ---------------- | ------------------------ | --------------------------------- | ----------- |
| id               | SERIAL                   | PRIMARY KEY                       | Internal ID |
| activity_id      | UUID                     | UNIQUE, DEFAULT gen_random_uuid() | External ID |
| user_id          | INTEGER                  | FK(users)                         | Human actor |
| agent_id         | UUID                     | FK(agents)                        | AI actor    |
| activity_type    | VARCHAR(100)             | NOT NULL                          | Category    |
| title            | VARCHAR(500)             | NOT NULL                          | Summary     |
| description      | TEXT                     |                                   | Details     |
| action_url       | VARCHAR(1000)            |                                   | Deep link   |
| project_id       | UUID                     | FK(projects)                      | Context     |
| task_id          | UUID                     | FK(tasks)                         | Context     |
| is_public        | BOOLEAN                  | DEFAULT false                     | Visibility  |
| visible_to_users | JSONB                    | DEFAULT '[]'                      | User list   |
| created_at       | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                     |             |

**Indexes**: activity_id, project_id, task_id, user_id, created_at, is_public

**Usage**: Dashboard, notifications, activity stream

---

## Indexing Strategy

### Primary Indexes (Always Used)

- All `*_id` columns (UUID lookups)
- Foreign keys for JOINs
- Status/state columns for filtering
- `created_at` for sorting/range queries

### JSONB Indexes (GIN)

- Used for array/object searches
- Examples: `tags`, `labels`, `labels`, `metadata`
- Trade-off: Larger index size for query speed

### Composite Indexes (Future)

- `(project_id, status)` - Common project queries
- `(agent_id, created_at DESC)` - Agent history
- `(task_id, created_at DESC)` - Task timeline

## Constraints and Validation

### CHECK Constraints

- Enum-like columns: role, status, priority, type
- Numeric ranges: complexity_score (1-13), credibility_score (0-1)
- Boolean immutability: `is_immutable = true` on audit_logs

### Foreign Keys

- Cascading deletes: Tasks deleted when project deleted
- Set null: Comments/attachments survive task deletion

### Unique Constraints

- Usernames and emails (case-sensitive)
- GitHub IDs (OAuth deduplication)
- Project slugs (URL safety)
- Agent names (system identification)

## Timestamp Conventions

### created_at

- Set automatically on insert
- Never updated
- Used for ordering, date range queries

### updated_at

- Set on insert and update
- Tracks last modification
- Useful for cache invalidation

### Other Timestamps

- `last_login_at`: User activity tracking
- `started_at`, `completed_at`: Workflow tracking
- `verified_at`: Evidence attestation
- `deprecated_at`: Agent lifecycle

## JSONB Fields

Used for extensibility without migrations:

| Table    | Column              | Purpose               | Example                                              |
| -------- | ------------------- | --------------------- | ---------------------------------------------------- |
| users    | metadata            | User attributes       | `{"department": "eng", "reports": 5}`                |
| projects | config              | Project settings      | `{"require_reviews": 2, "auto_merge": false}`        |
| agents   | capabilities        | Feature flags         | `{"routing": true, "cost_optimization": true}`       |
| tasks    | ai_analysis         | AI processing results | `{"sentiment": "positive", "complexity": 8}`         |
| evidence | credibility_factors | Scoring details       | `{"source_reliability": 0.9, "test_coverage": 0.85}` |

## Future Enhancements

1. **Materialized Views**: Pre-computed metrics
2. **Partitioning**: Yearly/monthly for large tables
3. **Time-Series**: Metrics extension
4. **Full-Text Search**: FTS on task descriptions
5. **Read Replicas**: Horizontal scaling

## Performance Characteristics

| Operation          | Complexity | Optimization                      |
| ------------------ | ---------- | --------------------------------- |
| Find user by ID    | O(1)       | UUID index                        |
| List project tasks | O(n log n) | Index on (project_id, created_at) |
| Search evidence    | O(log n)   | GIN index on tags                 |
| Agent history      | O(n log n) | Index on (agent_id, created_at)   |
| Audit log query    | O(n log n) | Partitioning recommended          |
