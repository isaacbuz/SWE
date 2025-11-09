#!/bin/bash
# Execute Agent Workflow - Start an agent working on an issue

set -e

AGENT_ID="${1:-SUB-20}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKTREES_DIR="$REPO_ROOT/../worktrees"
AGENTS_DIR="$REPO_ROOT/.agents/sub-agents"

if [ -z "$AGENT_ID" ]; then
    echo "Usage: $0 <AGENT_ID>"
    echo "Example: $0 SUB-20"
    exit 1
fi

# Find agent config
AGENT_FILE=$(find "$AGENTS_DIR" -name "${AGENT_ID}-*.md" | head -1)

if [ -z "$AGENT_FILE" ]; then
    echo "❌ Agent $AGENT_ID not found"
    exit 1
fi

# Extract issue number and branch name
ISSUE_NUM=$(grep "^\*\*Issue\*\*:" "$AGENT_FILE" | sed 's/.*#\([0-9]*\).*/\1/')
BRANCH_NAME="agent-${AGENT_ID}-issue-${ISSUE_NUM}"
WORKTREE_PATH="$WORKTREES_DIR/$BRANCH_NAME"

echo "🤖 Starting Agent: $AGENT_ID"
echo "📋 Issue: #$ISSUE_NUM"
echo "🌿 Branch: $BRANCH_NAME"
echo ""

# Create branch if it doesn't exist
cd "$REPO_ROOT"
if ! git show-ref --verify --quiet refs/heads/"$BRANCH_NAME"; then
    echo "🌿 Creating branch: $BRANCH_NAME"
    git checkout -b "$BRANCH_NAME" 2>/dev/null || git checkout "$BRANCH_NAME"
else
    echo "✅ Branch exists: $BRANCH_NAME"
    git checkout "$BRANCH_NAME"
fi

# Create worktree if it doesn't exist
if [ ! -d "$WORKTREE_PATH" ]; then
    echo "🌳 Creating worktree: $WORKTREE_PATH"
    git worktree add "$WORKTREE_PATH" "$BRANCH_NAME"
else
    echo "✅ Worktree exists: $WORKTREE_PATH"
fi

# Update agent status
python3 "$REPO_ROOT/scripts/agent-coordinator.py" assign "$AGENT_ID" || true

echo ""
echo "✅ Agent $AGENT_ID is ready to work!"
echo ""
echo "📁 Worktree location: $WORKTREE_PATH"
echo ""
echo "Next steps:"
echo "  1. cd $WORKTREE_PATH"
echo "  2. Review the issue: $AGENT_FILE"
echo "  3. Implement the changes"
echo "  4. Run tests"
echo "  5. Commit and push"
echo "  6. Create PR"
echo "  7. Run: python3 scripts/agent-coordinator.py complete $AGENT_ID [PR_URL]"

