# Skills System - Quick Start Guide

**Get started with the Skills marketplace in 5 minutes!**

## Prerequisites

- PostgreSQL database running
- Redis running (optional, for caching)
- Python 3.11+
- Node.js 18+

## Step 1: Load Built-in Skills

```bash
# Set your database URL
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/swe_agent"

# Install Python dependencies
cd packages/skills_engine
pip install -r requirements.txt

# Install YAML parser
pip install pyyaml

# Run seed script
cd ../skills-library
python seed_skills.py
```

**Expected Output**:

```
Found 16 skill definitions
  ✅ Inserted typescript-api-endpoint
  ✅ Inserted react-component-generator
  ...
✅ Successfully inserted 16 skills
```

## Step 2: Start Backend API

```bash
cd apps/api

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn main:app --reload --port 8000
```

**Verify**: Visit `http://localhost:8000/api/v1/skills` to see Skills list

## Step 3: Start Frontend

```bash
cd apps/web

# Install dependencies
npm install

# Start dev server
npm run dev
```

**Verify**: Visit `http://localhost:3000/skills` to see marketplace

## Step 4: Execute Your First Skill

### Via API

```bash
# Get a skill ID first
curl http://localhost:8000/api/v1/skills | jq '.[0].id'

# Execute the skill
curl -X POST http://localhost:8000/api/v1/skills/{skill_id}/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "inputs": {
      "endpoint_path": "/api/users/:id",
      "http_method": "GET",
      "description": "Get user by ID",
      "request_schema": {"type": "object"},
      "response_schema": {"type": "object"}
    }
  }'
```

### Via UI

1. Navigate to `/skills`
2. Click on a Skill card
3. Go to "Playground" tab
4. Fill in inputs
5. Click "Execute Skill"
6. View results!

## Available Skills

### Code Generation (4)

- `typescript-api-endpoint` - Generate Express.js API endpoints
- `react-component-generator` - Generate React components
- `python-class-generator` - Generate Python classes
- `sql-query-generator` - Generate SQL queries

### Testing (3)

- `unit-test-generator` - Generate unit tests
- `integration-test-generator` - Generate integration tests
- `e2e-test-generator` - Generate E2E tests

### Code Review (3)

- `security-code-review` - Security-focused code review
- `performance-code-review` - Performance optimization review
- `best-practices-review` - Best practices review

### Documentation (3)

- `api-documentation-generator` - Generate OpenAPI docs
- `readme-generator` - Generate README files
- `code-comments-generator` - Add code comments

### Architecture (3)

- `architecture-decision-record` - Generate ADRs
- `system-design-diagram` - Generate diagrams
- `database-schema-designer` - Design database schemas

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
pg_isready

# Test connection
psql -h localhost -U postgres -d swe_agent -c "SELECT 1"
```

### Redis Connection Issues

```bash
# Check Redis is running
redis-cli ping

# Should return: PONG
```

### API Not Responding

```bash
# Check if API is running
curl http://localhost:8000/health

# Check logs
tail -f apps/api/logs/app.log
```

### Frontend Not Loading

```bash
# Check if dev server is running
curl http://localhost:3000

# Check browser console for errors
# Verify API_URL is set correctly
```

## Next Steps

1. **Browse Skills**: Explore the marketplace
2. **Install Skills**: Click "Install" on Skills you want
3. **Test Skills**: Use the Playground to test execution
4. **Create Skills**: Use the API to create custom Skills
5. **Integrate**: Use Skills in your agents and workflows

## Documentation

- [Skills Architecture](./docs/architecture/CLAUDE_SKILLS.md)
- [API Reference](./apps/api/README.md)
- [Implementation Summary](./SKILLS_SYSTEM_COMPLETION_REPORT.md)

## Support

For issues or questions:

- Check [Troubleshooting](#troubleshooting) section
- Review [Implementation Status](./IMPLEMENTATION_STATUS.md)
- See [GitHub Issues](./GITHUB_ISSUES.md)

---

**Happy Skill Building! 🚀**
