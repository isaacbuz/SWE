#!/usr/bin/env python3
"""
Create Sub-Agent Configurations for GitHub Issues
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class SubAgentGenerator:
    """Generate sub-agent configurations for GitHub issues"""
    
    def __init__(self, issues_data: Dict[str, Any], base_dir: Path):
        self.issues_data = issues_data
        self.base_dir = base_dir
        self.agents_dir = base_dir / ".agents" / "sub-agents"
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        
    def analyze_issues(self) -> List[Dict[str, Any]]:
        """Analyze issues and group by epic/dependency"""
        issues = self.issues_data.get("issues", [])
        
        # Group by labels/epic
        epics = {}
        for issue in issues:
            labels = [l.get("name", "") if isinstance(l, dict) else l for l in issue.get("labels", [])]
            epic_label = next((l for l in labels if "epic" in l.lower()), "unassigned")
            
            if epic_label not in epics:
                epics[epic_label] = []
            epics[epic_label].append(issue)
        
        return issues
    
    def create_agent_config(self, issue: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Create configuration for a sub-agent"""
        issue_num = issue.get("number", 0)
        title = issue.get("title", "")
        body = issue.get("body", "")
        labels = [l.get("name", "") if isinstance(l, dict) else l for l in issue.get("labels", [])]
        state = issue.get("state", "open")
        
        # Determine agent type based on labels
        agent_type = "codegen"
        if any("frontend" in l.lower() for l in labels):
            agent_type = "frontend"
        elif any("backend" in l.lower() or "api" in l.lower() for l in labels):
            agent_type = "backend"
        elif any("infrastructure" in l.lower() or "devops" in l.lower() for l in labels):
            agent_type = "infrastructure"
        elif any("test" in l.lower() for l in labels):
            agent_type = "tester"
        elif any("security" in l.lower() for l in labels):
            agent_type = "security"
        
        return {
            "agent_id": agent_id,
            "issue_number": issue_num,
            "issue_title": title,
            "issue_state": state,
            "agent_type": agent_type,
            "labels": labels,
            "description": body[:500] if body else "",
            "worktree_branch": f"agent-{agent_id}-issue-{issue_num}",
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "dependencies": self._extract_dependencies(body),
            "estimated_effort": self._estimate_effort(labels, body),
            "priority": self._determine_priority(labels)
        }
    
    def _extract_dependencies(self, body: str) -> List[int]:
        """Extract issue dependencies from body"""
        import re
        deps = []
        # Look for patterns like "depends on #123" or "blocks #456"
        patterns = [
            r"depends?\s+on\s+#(\d+)",
            r"blocks?\s+#(\d+)",
            r"related\s+to\s+#(\d+)",
            r"#(\d+)"
        ]
        for pattern in patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            deps.extend([int(m) for m in matches])
        return sorted(set(deps))
    
    def _estimate_effort(self, labels: List[str], body: str) -> str:
        """Estimate effort based on labels and description"""
        size_labels = [l for l in labels if "size:" in l.lower()]
        if size_labels:
            return size_labels[0].split(":")[-1].upper()
        
        # Estimate from body length and keywords
        body_lower = body.lower()
        if any(kw in body_lower for kw in ["simple", "quick", "small"]):
            return "XS"
        elif any(kw in body_lower for kw in ["complex", "major", "large"]):
            return "XL"
        else:
            return "M"
    
    def _determine_priority(self, labels: List[str]) -> str:
        """Determine priority from labels"""
        priority_labels = [l for l in labels if "priority:" in l.lower()]
        if priority_labels:
            return priority_labels[0].split(":")[-1].upper()
        return "MEDIUM"
    
    def generate_all_agents(self) -> List[Dict[str, Any]]:
        """Generate configurations for all issues"""
        issues = self.analyze_issues()
        agents = []
        
        for idx, issue in enumerate(issues, 1):
            agent_id = f"SUB-{idx:02d}"
            config = self.create_agent_config(issue, agent_id)
            agents.append(config)
            
            # Write individual agent file
            agent_file = self.agents_dir / f"{agent_id}-ISSUE-{issue.get('number', 0)}.md"
            self.write_agent_file(agent_file, config, issue)
        
        # Write master index
        self.write_master_index(agents)
        
        return agents
    
    def write_agent_file(self, filepath: Path, config: Dict[str, Any], issue: Dict[str, Any]):
        """Write individual agent configuration file"""
        content = f"""# 🤖 {config['agent_id']}: {config['issue_title']}

**Issue**: #{config['issue_number']}  
**Status**: {config['status'].upper()}  
**Priority**: {config['priority']}  
**Effort**: {config['estimated_effort']}  
**Agent Type**: {config['agent_type']}  
**Worktree Branch**: `{config['worktree_branch']}`

---

## MISSION

{issue.get('body', 'No description provided')}

## DEPENDENCIES

{', '.join([f'#{d}' for d in config['dependencies']]) if config['dependencies'] else 'None'}

## ACCEPTANCE CRITERIA

[To be extracted from issue body]

## IMPLEMENTATION PLAN

1. Create worktree: `git worktree add ../worktrees/{config['worktree_branch']} {config['worktree_branch']}`
2. Checkout branch: `git checkout -b {config['worktree_branch']}`
3. Implement changes
4. Run tests
5. Commit and push
6. Create PR
7. Update issue status

## STATUS TRACKING

- [ ] Worktree created
- [ ] Branch checked out
- [ ] Implementation started
- [ ] Tests written
- [ ] Code committed
- [ ] PR created
- [ ] Issue updated

---
**Created**: {config['created_at']}
"""
        filepath.write_text(content)
    
    def write_master_index(self, agents: List[Dict[str, Any]]):
        """Write master index of all agents"""
        index_file = self.agents_dir / "AGENT-INDEX.json"
        index_file.write_text(json.dumps({
            "total_agents": len(agents),
            "generated_at": datetime.now().isoformat(),
            "agents": agents
        }, indent=2))
        
        # Also create markdown index
        md_file = self.agents_dir / "AGENT-INDEX.md"
        md_content = f"""# 🤖 Sub-Agent Index

**Total Agents**: {len(agents)}  
**Generated**: {datetime.now().isoformat()}

---

## Agent List

| Agent ID | Issue # | Title | Status | Priority | Effort | Type |
|----------|---------|-------|--------|----------|--------|------|
"""
        for agent in agents:
            md_content += f"| {agent['agent_id']} | #{agent['issue_number']} | {agent['issue_title'][:50]} | {agent['status']} | {agent['priority']} | {agent['estimated_effort']} | {agent['agent_type']} |\n"
        
        md_file.write_text(md_content)


def main():
    """Main entry point"""
    base_dir = Path(__file__).parent.parent
    issues_file = base_dir / ".github" / "issues-data.json"
    
    if not issues_file.exists():
        print(f"❌ Issues data file not found: {issues_file}")
        print("Run scripts/fetch-github-issues.py first")
        return 1
    
    with open(issues_file) as f:
        issues_data = json.load(f)
    
    generator = SubAgentGenerator(issues_data, base_dir)
    agents = generator.generate_all_agents()
    
    print(f"✅ Generated {len(agents)} sub-agent configurations")
    print(f"📁 Files written to: {generator.agents_dir}")
    
    return 0


if __name__ == "__main__":
    exit(main())

