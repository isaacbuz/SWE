#!/usr/bin/env python3
"""
Agent Coordinator - Orchestrates Sub-Agents Working on GitHub Issues
"""
import json
import os
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys


class AgentCoordinator:
    """Coordinates multiple sub-agents working on GitHub issues"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.agents_dir = base_dir / ".agents" / "sub-agents"
        self.worktrees_dir = base_dir.parent / "worktrees"
        self.agents_data = self._load_agents()
        
    def _load_agents(self) -> Dict[str, Any]:
        """Load agent index"""
        index_file = self.agents_dir / "AGENT-INDEX.json"
        if not index_file.exists():
            return {"agents": []}
        return json.loads(index_file.read_text())
    
    def get_ready_agents(self) -> List[Dict[str, Any]]:
        """Get agents that are ready to work (no blocking dependencies)"""
        agents = self.agents_data.get("agents", [])
        ready = []
        
        for agent in agents:
            deps = agent.get("dependencies", [])
            # Check if all dependencies are completed
            if not deps or all(self._is_dependency_complete(dep) for dep in deps):
                if agent.get("status") == "pending":
                    ready.append(agent)
        
        return sorted(ready, key=lambda a: (
            {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(a.get("priority", "MEDIUM"), 2),
            a.get("issue_number", 9999)
        ))
    
    def _is_dependency_complete(self, issue_num: int) -> bool:
        """Check if a dependency issue is complete"""
        for agent in self.agents_data.get("agents", []):
            if agent.get("issue_number") == issue_num:
                return agent.get("status") == "completed"
        return False  # Assume incomplete if not found
    
    def assign_agent(self, agent_id: str) -> bool:
        """Assign an agent to start working"""
        agent = next((a for a in self.agents_data["agents"] if a["agent_id"] == agent_id), None)
        if not agent:
            return False
        
        # Update status
        agent["status"] = "in_progress"
        agent["started_at"] = datetime.now().isoformat()
        
        # Save updated index
        self._save_agents()
        
        # Create worktree if needed
        self._ensure_worktree(agent)
        
        return True
    
    def complete_agent(self, agent_id: str, pr_url: Optional[str] = None) -> bool:
        """Mark an agent's work as complete"""
        agent = next((a for a in self.agents_data["agents"] if a["agent_id"] == agent_id), None)
        if not agent:
            return False
        
        agent["status"] = "completed"
        agent["completed_at"] = datetime.now().isoformat()
        if pr_url:
            agent["pr_url"] = pr_url
        
        self._save_agents()
        return True
    
    def _ensure_worktree(self, agent: Dict[str, Any]):
        """Ensure worktree exists for agent"""
        branch = agent["worktree_branch"]
        worktree_path = self.worktrees_dir / branch
        
        if worktree_path.exists():
            return
        
        # Create worktree
        subprocess.run([
            "git", "worktree", "add",
            str(worktree_path),
            branch
        ], cwd=self.base_dir, check=False)
    
    def _save_agents(self):
        """Save updated agent index"""
        index_file = self.agents_dir / "AGENT-INDEX.json"
        self.agents_data["updated_at"] = datetime.now().isoformat()
        index_file.write_text(json.dumps(self.agents_data, indent=2))
    
    def generate_work_plan(self) -> Dict[str, Any]:
        """Generate a work plan for all agents"""
        ready = self.get_ready_agents()
        in_progress = [a for a in self.agents_data["agents"] if a.get("status") == "in_progress"]
        completed = [a for a in self.agents_data["agents"] if a.get("status") == "completed"]
        
        return {
            "total_agents": len(self.agents_data["agents"]),
            "ready": len(ready),
            "in_progress": len(in_progress),
            "completed": len(completed),
            "ready_agents": ready[:10],  # Next 10 ready
            "in_progress_agents": in_progress,
            "completed_agents": completed
        }
    
    def print_status(self):
        """Print current status"""
        plan = self.generate_work_plan()
        
        print("=" * 80)
        print("🤖 AGENT COORDINATOR STATUS")
        print("=" * 80)
        print(f"Total Agents: {plan['total_agents']}")
        print(f"✅ Completed: {plan['completed']}")
        print(f"🔄 In Progress: {plan['in_progress']}")
        print(f"⏳ Ready: {plan['ready']}")
        print()
        
        if plan['ready_agents']:
            print("📋 Next Ready Agents:")
            for agent in plan['ready_agents']:
                print(f"  - {agent['agent_id']}: Issue #{agent['issue_number']} - {agent['issue_title'][:50]}")
            print()
        
        if plan['in_progress_agents']:
            print("🔄 Agents In Progress:")
            for agent in plan['in_progress_agents']:
                print(f"  - {agent['agent_id']}: Issue #{agent['issue_number']}")
            print()


def main():
    """Main entry point"""
    base_dir = Path(__file__).parent.parent
    coordinator = AgentCoordinator(base_dir)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "status":
            coordinator.print_status()
        elif command == "assign" and len(sys.argv) > 2:
            agent_id = sys.argv[2]
            if coordinator.assign_agent(agent_id):
                print(f"✅ Assigned agent {agent_id}")
            else:
                print(f"❌ Failed to assign agent {agent_id}")
        elif command == "complete" and len(sys.argv) > 2:
            agent_id = sys.argv[2]
            pr_url = sys.argv[3] if len(sys.argv) > 3 else None
            if coordinator.complete_agent(agent_id, pr_url):
                print(f"✅ Marked agent {agent_id} as complete")
            else:
                print(f"❌ Failed to complete agent {agent_id}")
        elif command == "ready":
            ready = coordinator.get_ready_agents()
            print(f"📋 {len(ready)} agents ready to work:")
            for agent in ready[:20]:
                print(f"  {agent['agent_id']}: Issue #{agent['issue_number']} - {agent['issue_title'][:60]}")
        else:
            print("Usage: python scripts/agent-coordinator.py [status|assign|complete|ready] [agent_id]")
    else:
        coordinator.print_status()


if __name__ == "__main__":
    main()

