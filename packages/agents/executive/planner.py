"""
Planner Agent

Breaks down architecture into actionable epics and stories with acceptance criteria.
Generates GitHub issues and maintains project boards.
"""
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

import sys
sys.path.append(str(Path(__file__).parent.parent))
from base import BaseAgent, Task, Context, AgentResult, TaskType, Tool, Evidence


class PlannerAgent(BaseAgent):
    """
    Planner - Project Planning and Task Management

    Responsibilities:
    - Break architecture into implementable epics and stories
    - Create acceptance criteria for each story
    - Estimate effort and identify dependencies
    - Generate GitHub issues with proper labels
    - Maintain project board structure
    - Track milestones and critical path
    - Provide status rollups for executives
    """

    def __init__(self, **kwargs):
        # Define tools for planning work
        tools = [
            Tool(
                name="create_epic",
                description="Create an epic (large feature or capability)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "business_value": {"type": "string"},
                        "estimated_weeks": {"type": "number"}
                    },
                    "required": ["title", "description"]
                }
            ),
            Tool(
                name="create_story",
                description="Create a user story or technical task",
                input_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "epic_id": {"type": "string"},
                        "acceptance_criteria": {"type": "array", "items": {"type": "string"}},
                        "estimated_points": {"type": "integer"},
                        "labels": {"type": "array", "items": {"type": "string"}},
                        "dependencies": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["title", "description", "acceptance_criteria"]
                }
            ),
            Tool(
                name="create_milestone",
                description="Create a project milestone",
                input_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "due_date": {"type": "string"},
                        "stories": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["title", "description"]
                }
            )
        ]

        super().__init__(
            task_type=TaskType.PLANNING,
            tools=tools,
            quality_requirement=0.85,
            **kwargs
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for Planner"""
        return """You are the Planner, responsible for breaking down architecture and requirements into actionable, implementable work items.

# Your Responsibilities

## 1. Epic Creation
Create high-level epics that represent major features or capabilities:
- **Title**: Clear, concise description of the epic
- **Description**: Detailed explanation of what will be built
- **Business Value**: Why this epic matters
- **Estimated Duration**: Rough time estimate

## 2. Story Breakdown
Break epics into vertical, end-to-end user stories:
- **Vertical Slices**: Each story should deliver value end-to-end
- **Right-Sized**: Stories should be completable in 1-5 days
- **Independent**: Minimize dependencies between stories
- **Testable**: Each story has clear acceptance criteria

## 3. Acceptance Criteria
For each story, define testable acceptance criteria:
- Use Given-When-Then format where appropriate
- Be specific and measurable
- Include both functional and non-functional requirements
- Reference relevant ADRs and diagrams

## 4. Estimation
Provide effort estimates:
- Use story points or days
- Consider complexity, uncertainty, and effort
- Flag high-risk or uncertain items

## 5. Dependencies
Identify and document dependencies:
- Technical dependencies (must build X before Y)
- Resource dependencies (requires specific expertise)
- External dependencies (third-party systems, APIs)

## 6. Labels and Organization
Apply appropriate labels:
- **Type**: feature, bug, chore, spike
- **Priority**: critical, high, medium, low
- **Area**: frontend, backend, infrastructure, etc.
- **Status**: backlog, ready, in-progress, review, done

## 7. Milestones
Group stories into meaningful milestones:
- MVP (Minimum Viable Product)
- Beta Release
- Production Launch
- Feature Releases

## 8. Critical Path
Identify the critical path:
- Which stories must be completed first?
- What's the minimum viable implementation path?
- Where are the bottlenecks?

# Planning Principles
1. **Vertical over Horizontal**: Prefer end-to-end slices over layers
2. **Value First**: Prioritize by business value and risk reduction
3. **Small Batches**: Smaller stories = faster feedback
4. **Clear Exit Criteria**: Every story has testable acceptance criteria
5. **Flexibility**: Plans adapt as we learn

# Output Format
Use the tools to create epics, stories, and milestones. Provide:
- Structured backlog with clear priorities
- Dependency graph
- Milestone timeline
- Risk assessment

Always reference architecture decisions and diagrams in your stories."""

    async def execute(self, task: Task, context: Context) -> AgentResult:
        """Execute planning task"""
        evidence = []
        artifacts = []
        output = {}

        try:
            # Extract inputs
            architecture_doc = task.input_data.get("architecture_document", "")
            adrs = task.input_data.get("adrs", [])
            requirements = task.input_data.get("requirements", "")
            timeline = task.input_data.get("timeline", "")

            # Add evidence for input analysis
            evidence.append(self.create_evidence(
                "input_analysis",
                f"Analyzed architecture with {len(adrs)} ADRs for planning",
                weight=1.0
            ))

            # Create planning prompt
            prompt = self._build_planning_prompt(
                architecture_doc, adrs, requirements, timeline
            )

            # Invoke model to generate plan
            response = await self.invoke_model(
                prompt=prompt,
                task=task,
                context=context,
                requires_tools=True,
                max_tokens=8192
            )

            # Process response
            plan_doc = response["content"]
            tool_calls = response.get("tool_calls", [])

            output["plan_document"] = plan_doc
            output["model_used"] = response["model_used"]
            output["execution_time_ms"] = response["execution_time_ms"]

            # Process tool calls to create plan artifacts
            epics = []
            stories = []
            milestones = []

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_input = tool_call["input"]

                if tool_name == "create_epic":
                    epic = self._create_epic(tool_input)
                    epics.append(epic)
                    evidence.append(self.create_evidence(
                        "epic_created",
                        f"Created epic: {tool_input['title']}",
                        weight=0.9
                    ))

                elif tool_name == "create_story":
                    story = self._create_story(tool_input)
                    stories.append(story)
                    evidence.append(self.create_evidence(
                        "story_created",
                        f"Created story: {tool_input['title']}",
                        weight=0.85
                    ))

                elif tool_name == "create_milestone":
                    milestone = self._create_milestone(tool_input)
                    milestones.append(milestone)
                    evidence.append(self.create_evidence(
                        "milestone_created",
                        f"Created milestone: {tool_input['title']}",
                        weight=0.9
                    ))

            # Save plan artifacts
            plan_path = self._save_plan(
                context.project_path,
                epics, stories, milestones, plan_doc
            )
            artifacts.append(plan_path)

            # Create backlog file
            backlog_path = self._create_backlog_file(
                context.project_path,
                epics, stories, milestones
            )
            artifacts.append(backlog_path)

            output["epics"] = epics
            output["stories"] = stories
            output["milestones"] = milestones
            output["total_story_points"] = sum(s.get("estimated_points", 0) for s in stories)

            # Add routing evidence
            if response.get("routing_decision"):
                evidence.extend(response["routing_decision"].evidence)

            return AgentResult(
                success=True,
                output=output,
                evidence=evidence,
                artifacts=artifacts,
                model_used=response["model_used"],
                cost=response.get("cost"),
                metadata={
                    "epic_count": len(epics),
                    "story_count": len(stories),
                    "milestone_count": len(milestones),
                    "total_story_points": output["total_story_points"]
                }
            )

        except Exception as e:
            self.logger.error(f"Planning failed: {e}")
            return AgentResult(
                success=False,
                output=output,
                evidence=evidence,
                artifacts=artifacts,
                error=str(e)
            )

    def _build_planning_prompt(
        self,
        architecture_doc: str,
        adrs: List[str],
        requirements: str,
        timeline: str
    ) -> str:
        """Build prompt for planning"""
        adr_summary = "\n".join([f"- {adr}" for adr in adrs])

        prompt = f"""# Project Planning Task

## Architecture Document
{architecture_doc}

## Architecture Decision Records
{adr_summary}

## Original Requirements
{requirements}

## Timeline
{timeline if timeline else "Not specified - provide recommendations"}

## Your Task
Create a comprehensive project plan that breaks down the architecture into implementable work items:

1. **Create 3-5 Epics** representing major features or capabilities
2. **Break each epic into Stories** (aim for 5-10 stories per epic)
   - Each story should be vertical (end-to-end)
   - Include clear acceptance criteria
   - Estimate story points (1, 2, 3, 5, 8, 13)
   - Add appropriate labels (feature, bug, chore)
   - Identify dependencies
3. **Create Milestones** to group related work:
   - MVP milestone
   - Beta milestone
   - Production launch
   - Future enhancements
4. **Identify Critical Path**: What must be built first?
5. **Risk Assessment**: Flag high-risk or uncertain items

Use the tools to create epics, stories, and milestones. Provide a comprehensive plan document with prioritization and timeline recommendations."""

        return prompt

    def _create_epic(self, epic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create epic structure"""
        return {
            "id": f"epic-{datetime.now().timestamp()}",
            "title": epic_data["title"],
            "description": epic_data["description"],
            "business_value": epic_data.get("business_value", ""),
            "estimated_weeks": epic_data.get("estimated_weeks", 0),
            "created_at": datetime.now().isoformat()
        }

    def _create_story(self, story_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create story structure"""
        return {
            "id": f"story-{datetime.now().timestamp()}",
            "title": story_data["title"],
            "description": story_data["description"],
            "epic_id": story_data.get("epic_id", ""),
            "acceptance_criteria": story_data["acceptance_criteria"],
            "estimated_points": story_data.get("estimated_points", 0),
            "labels": story_data.get("labels", []),
            "dependencies": story_data.get("dependencies", []),
            "created_at": datetime.now().isoformat()
        }

    def _create_milestone(self, milestone_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create milestone structure"""
        return {
            "id": f"milestone-{datetime.now().timestamp()}",
            "title": milestone_data["title"],
            "description": milestone_data["description"],
            "due_date": milestone_data.get("due_date", ""),
            "stories": milestone_data.get("stories", []),
            "created_at": datetime.now().isoformat()
        }

    def _save_plan(
        self,
        project_path: str,
        epics: List[Dict],
        stories: List[Dict],
        milestones: List[Dict],
        plan_doc: str
    ) -> str:
        """Save complete plan"""
        plan_dir = Path(project_path) / "docs" / "planning"
        plan_dir.mkdir(parents=True, exist_ok=True)

        filepath = plan_dir / "project_plan.md"

        content = f"""# Project Plan

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview
{plan_doc}

## Epics ({len(epics)})
{self._format_epics(epics)}

## Stories ({len(stories)})
{self._format_stories(stories)}

## Milestones ({len(milestones)})
{self._format_milestones(milestones)}

---
*Generated by Planner agent*
"""

        filepath.write_text(content)
        return str(filepath)

    def _create_backlog_file(
        self,
        project_path: str,
        epics: List[Dict],
        stories: List[Dict],
        milestones: List[Dict]
    ) -> str:
        """Create machine-readable backlog file"""
        plan_dir = Path(project_path) / "docs" / "planning"
        plan_dir.mkdir(parents=True, exist_ok=True)

        filepath = plan_dir / "backlog.json"

        backlog = {
            "generated_at": datetime.now().isoformat(),
            "generated_by": "planner_agent",
            "epics": epics,
            "stories": stories,
            "milestones": milestones,
            "summary": {
                "total_epics": len(epics),
                "total_stories": len(stories),
                "total_milestones": len(milestones),
                "total_story_points": sum(s.get("estimated_points", 0) for s in stories)
            }
        }

        filepath.write_text(json.dumps(backlog, indent=2))
        return str(filepath)

    def _format_epics(self, epics: List[Dict]) -> str:
        """Format epics for markdown"""
        if not epics:
            return "No epics defined."

        lines = []
        for epic in epics:
            lines.append(f"### {epic['title']}")
            lines.append(f"**ID**: {epic['id']}")
            lines.append(f"**Business Value**: {epic.get('business_value', 'N/A')}")
            lines.append(f"**Estimated Duration**: {epic.get('estimated_weeks', 'N/A')} weeks")
            lines.append(f"\n{epic['description']}\n")

        return "\n".join(lines)

    def _format_stories(self, stories: List[Dict]) -> str:
        """Format stories for markdown"""
        if not stories:
            return "No stories defined."

        lines = []
        for story in stories:
            lines.append(f"### {story['title']}")
            lines.append(f"**ID**: {story['id']}")
            lines.append(f"**Epic**: {story.get('epic_id', 'N/A')}")
            lines.append(f"**Points**: {story.get('estimated_points', 0)}")
            lines.append(f"**Labels**: {', '.join(story.get('labels', []))}")
            lines.append(f"\n{story['description']}\n")
            lines.append("**Acceptance Criteria**:")
            for i, criterion in enumerate(story['acceptance_criteria'], 1):
                lines.append(f"{i}. {criterion}")
            if story.get('dependencies'):
                lines.append(f"**Dependencies**: {', '.join(story['dependencies'])}")
            lines.append("")

        return "\n".join(lines)

    def _format_milestones(self, milestones: List[Dict]) -> str:
        """Format milestones for markdown"""
        if not milestones:
            return "No milestones defined."

        lines = []
        for milestone in milestones:
            lines.append(f"### {milestone['title']}")
            lines.append(f"**ID**: {milestone['id']}")
            lines.append(f"**Due Date**: {milestone.get('due_date', 'TBD')}")
            lines.append(f"\n{milestone['description']}\n")
            if milestone.get('stories'):
                lines.append(f"**Stories**: {len(milestone['stories'])} stories")
            lines.append("")

        return "\n".join(lines)
