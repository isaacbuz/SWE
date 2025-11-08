#!/bin/bash
# Run Skills system tests with coverage

set -e

echo "🧪 Running Skills System Tests"
echo "================================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Backend tests
echo -e "\n${BLUE}Backend Tests${NC}"
echo "-------------------"

echo "📦 Skills Engine Tests..."
cd packages/skills_engine
pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html || true
cd ../..

echo -e "\n📡 API Tests..."
cd apps/api
pytest tests/unit/test_skills.py -v || true
cd ../..

# Frontend tests
echo -e "\n${BLUE}Frontend Tests${NC}"
echo "-------------------"

echo "⚛️  React Hooks Tests..."
cd apps/web
npm test -- useSkills.test.ts --run || true
cd ../..

echo "🎨 Component Tests..."
cd apps/web
npm test -- SkillCard.test.tsx --run || true
cd ../..

echo -e "\n${GREEN}✅ Tests Complete${NC}"
echo "================================"
echo ""
echo "Coverage reports:"
echo "  - Backend: packages/skills_engine/htmlcov/index.html"
echo "  - Frontend: apps/web/coverage/index.html"

