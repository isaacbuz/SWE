#!/bin/bash
# Setup Git Worktrees for Parallel Agent Work

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKTREES_DIR="$REPO_ROOT/../worktrees"
AGENTS_DIR="$REPO_ROOT/.agents/sub-agents"

# Create worktrees directory
mkdir -p "$WORKTREES_DIR"

# Read agent index
if [ ! -f "$AGENTS_DIR/AGENT-INDEX.json" ]; then
    echo "❌ Agent index not found. Run scripts/create-sub-agents.py first"
    exit 1
fi

# Parse agent configurations
AGENTS=$(cat "$AGENTS_DIR/AGENT-INDEX.json" | jq -r '.agents[] | "\(.agent_id)|\(.worktree_branch)|\(.issue_number)"')

echo "🌳 Setting up worktrees for agents..."
echo ""

for agent_info in $AGENTS; do
    IFS='|' read -r agent_id branch_name issue_num <<< "$agent_info"
    
    worktree_path="$WORKTREES_DIR/$branch_name"
    
    # Check if worktree already exists
    if [ -d "$worktree_path" ]; then
        echo "⏭️  Skipping $agent_id - worktree already exists: $worktree_path"
        continue
    fi
    
    echo "🌿 Creating worktree for $agent_id (Issue #$issue_num)..."
    
    # Create branch if it doesn't exist
    cd "$REPO_ROOT"
    if ! git show-ref --verify --quiet refs/heads/"$branch_name"; then
        git checkout -b "$branch_name" 2>/dev/null || git checkout "$branch_name"
    fi
    
    # Create worktree
    git worktree add "$worktree_path" "$branch_name" 2>/dev/null || {
        echo "⚠️  Worktree might already exist, continuing..."
    }
    
    echo "✅ Created worktree: $worktree_path"
    echo ""
done

echo "✅ All worktrees created!"
echo ""
echo "📋 Worktrees location: $WORKTREES_DIR"
echo ""
echo "To work on an agent:"
echo "  cd $WORKTREES_DIR/agent-XXX-issue-YYY"
echo "  # Make your changes"
echo "  git add ."
echo "  git commit -m 'feat: implement issue #YYY'"
echo "  git push origin agent-XXX-issue-YYY"

