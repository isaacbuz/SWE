#!/bin/bash
# Script to close completed GitHub issues
# Usage: ./scripts/close-issues.sh [issue_numbers...]
# Example: ./scripts/close-issues.sh 16 17 18

set -e

REPO="isaacbuz/SWE"
ISSUES=("$@")

if [ ${#ISSUES[@]} -eq 0 ]; then
    echo "Usage: $0 [issue_numbers...]"
    echo "Example: $0 16 17 18"
    exit 1
fi

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed."
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub CLI."
    echo "Run: gh auth login"
    exit 1
fi

# Close each issue
for issue_num in "${ISSUES[@]}"; do
    echo "Closing Issue #$issue_num..."
    
    # Determine closure comment based on issue number
    case $issue_num in
        16)
            comment="✅ Completed: Provider Performance Tracking implemented. See ISSUE_16_17_CLOSURE_SUMMARY.md for details."
            ;;
        17)
            comment="✅ Completed: Tool Calling Pipeline implemented. See ISSUE_16_17_CLOSURE_SUMMARY.md for details."
            ;;
        18)
            comment="✅ Completed: Sample Pipeline - Spec to GitHub Issues implemented. See ISSUE_18_CLOSURE_SUMMARY.md for details."
            ;;
        23)
            comment="✅ Completed: All API routers implemented. See ISSUE_23_CLOSURE_SUMMARY.md for details."
            ;;
        *)
            comment="✅ Completed: Implementation complete. See closure summary documents for details."
            ;;
    esac
    
    # Add comment and close
    gh issue comment "$issue_num" --repo "$REPO" --body "$comment"
    gh issue close "$issue_num" --repo "$REPO" --comment "$comment"
    
    echo "✅ Issue #$issue_num closed"
done

echo ""
echo "All issues closed successfully!"

