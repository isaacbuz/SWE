"""
Technical Director Agent

Oversees technical execution, makes tie-breaking decisions, and ensures deliverable quality.
Acts as technical leadership for the agent team.
"""
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

import sys
sys.path.append(str(Path(__file__).parent.parent))
from base import BaseAgent, Task, Context, AgentResult, TaskType, Tool, Evidence


class TechnicalDirectorAgent(BaseAgent):
    """
    Technical Director - Technical Leadership and Governance

    Responsibilities:
    - Review and approve major technical decisions
    - Resolve conflicts between agents or approaches
    - Ensure code quality and consistency
    - Make tie-breaking decisions on architecture choices
    - Oversee technical deliverable integrity
    - Coordinate cross-cutting concerns
    - Set and enforce technical standards
    """

    def __init__(self, **kwargs):
        tools = [
            Tool(
                name="review_decision",
                description="Review a technical decision or approach",
                input_schema={
                    "type": "object",
                    "properties": {
                        "decision_id": {"type": "string"},
                        "decision_type": {"type": "string"},
                        "recommendation": {"type": "string", "enum": ["approve", "reject", "revise"]},
                        "rationale": {"type": "string"},
                        "modifications": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["decision_id", "recommendation", "rationale"]
                }
            ),
            Tool(
                name="set_standard",
                description="Set or update a technical standard",
                input_schema={
                    "type": "object",
                    "properties": {
                        "standard_name": {"type": "string"},
                        "category": {"type": "string"},
                        "description": {"type": "string"},
                        "rules": {"type": "array", "items": {"type": "string"}},
                        "enforcement_level": {"type": "string", "enum": ["required", "recommended", "optional"]}
                    },
                    "required": ["standard_name", "category", "description", "rules"]
                }
            )
        ]

        super().__init__(
            task_type=TaskType.CODE_REVIEW,
            tools=tools,
            quality_requirement=0.95,  # Highest quality for leadership
            **kwargs
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for Technical Director"""
        return """You are the Technical Director, providing technical leadership and governance for the development team.

# Your Responsibilities

## 1. Decision Review and Approval
Review major technical decisions for:
- **Alignment**: Does it align with overall architecture and goals?
- **Quality**: Is it well-reasoned with proper tradeoff analysis?
- **Risk**: What are the risks and how are they mitigated?
- **Maintainability**: Will this be sustainable long-term?

## 2. Conflict Resolution
When agents or approaches conflict:
- **Understand**: Gather context from all perspectives
- **Analyze**: Evaluate tradeoffs objectively
- **Decide**: Make clear, well-reasoned decisions
- **Document**: Record rationale for future reference

## 3. Technical Standards
Set and enforce standards for:
- Code quality and style
- Architecture patterns
- Security practices
- Testing requirements
- Documentation standards
- Performance requirements

## 4. Quality Assurance
Ensure deliverables meet quality bar:
- Code is clean, maintainable, and well-tested
- Architecture is sound and evolvable
- Documentation is complete and accurate
- Security requirements are met
- Performance targets are achieved

## 5. Cross-Cutting Concerns
Coordinate on cross-cutting concerns:
- Logging and monitoring
- Error handling
- Security
- Performance
- Accessibility
- Internationalization

## 6. Risk Management
Identify and mitigate technical risks:
- Technical debt
- Scalability concerns
- Security vulnerabilities
- Integration challenges
- Resource constraints

# Decision-Making Principles
1. **Data-Driven**: Base decisions on evidence and analysis
2. **Pragmatic**: Balance ideal with practical constraints
3. **Transparent**: Document rationale clearly
4. **Consistent**: Apply standards consistently
5. **Collaborative**: Seek input but make decisive calls
6. **Long-Term**: Consider long-term maintainability

# Review Criteria
When reviewing decisions or deliverables, assess:
- Technical soundness
- Alignment with architecture
- Code quality and testability
- Security and performance
- Documentation completeness
- Maintainability and evolvability

Always provide clear, actionable feedback with rationale."""

    async def execute(self, task: Task, context: Context) -> AgentResult:
        """Execute technical review task"""
        evidence = []
        artifacts = []
        output = {}

        try:
            review_type = task.input_data.get("review_type", "decision")
            items_to_review = task.input_data.get("items", [])

            evidence.append(self.create_evidence(
                "review_initiated",
                f"Reviewing {len(items_to_review)} {review_type} items",
                weight=1.0
            ))

            # Build review prompt
            prompt = self._build_review_prompt(review_type, items_to_review)

            # Invoke model for review
            response = await self.invoke_model(
                prompt=prompt,
                task=task,
                context=context,
                requires_tools=True,
                max_tokens=4096
            )

            # Process response
            review_doc = response["content"]
            tool_calls = response.get("tool_calls", [])

            output["review_document"] = review_doc
            output["model_used"] = response["model_used"]

            # Process tool calls
            reviews = []
            standards = []

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_input = tool_call["input"]

                if tool_name == "review_decision":
                    review = self._process_review(tool_input)
                    reviews.append(review)
                    evidence.append(self.create_evidence(
                        "decision_reviewed",
                        f"{tool_input['recommendation'].upper()}: {tool_input['decision_id']}",
                        weight=0.95
                    ))

                elif tool_name == "set_standard":
                    standard = self._process_standard(tool_input)
                    standards.append(standard)
                    evidence.append(self.create_evidence(
                        "standard_set",
                        f"Set standard: {tool_input['standard_name']}",
                        weight=0.9
                    ))

            # Save review results
            if reviews:
                review_path = self._save_reviews(context.project_path, reviews, review_doc)
                artifacts.append(review_path)

            if standards:
                standards_path = self._save_standards(context.project_path, standards)
                artifacts.append(standards_path)

            output["reviews"] = reviews
            output["standards"] = standards

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
                    "reviews_count": len(reviews),
                    "standards_count": len(standards),
                    "approved": len([r for r in reviews if r["recommendation"] == "approve"]),
                    "rejected": len([r for r in reviews if r["recommendation"] == "reject"])
                }
            )

        except Exception as e:
            self.logger.error(f"Technical review failed: {e}")
            return AgentResult(
                success=False,
                output=output,
                evidence=evidence,
                artifacts=artifacts,
                error=str(e)
            )

    def _build_review_prompt(self, review_type: str, items: List[Dict]) -> str:
        """Build review prompt"""
        items_str = json.dumps(items, indent=2)

        prompt = f"""# Technical Review Task

## Review Type
{review_type}

## Items to Review
{items_str}

## Your Task
As Technical Director, review these items and provide:

1. **Assessment** for each item:
   - Technical soundness
   - Alignment with architecture and standards
   - Risk analysis
   - Quality assessment

2. **Recommendation** for each:
   - Approve: Good to proceed as-is
   - Reject: Significant issues, cannot proceed
   - Revise: Good direction but needs modifications

3. **Rationale**: Clear explanation of your decision

4. **Modifications** (if revise): Specific changes needed

5. **Standards** (if applicable): Any new standards to set based on this review

Use the tools to record your decisions and set standards. Provide a comprehensive review document with clear, actionable feedback."""

        return prompt

    def _process_review(self, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process review decision"""
        return {
            "decision_id": review_data["decision_id"],
            "decision_type": review_data.get("decision_type", ""),
            "recommendation": review_data["recommendation"],
            "rationale": review_data["rationale"],
            "modifications": review_data.get("modifications", []),
            "reviewed_at": datetime.now().isoformat(),
            "reviewed_by": "technical_director_agent"
        }

    def _process_standard(self, standard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process standard definition"""
        return {
            "standard_name": standard_data["standard_name"],
            "category": standard_data["category"],
            "description": standard_data["description"],
            "rules": standard_data["rules"],
            "enforcement_level": standard_data.get("enforcement_level", "recommended"),
            "created_at": datetime.now().isoformat(),
            "created_by": "technical_director_agent"
        }

    def _save_reviews(
        self,
        project_path: str,
        reviews: List[Dict],
        review_doc: str
    ) -> str:
        """Save review results"""
        review_dir = Path(project_path) / "docs" / "reviews"
        review_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filepath = review_dir / f"technical-review-{timestamp}.md"

        content = f"""# Technical Review

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Reviewer: Technical Director Agent

## Overview
{review_doc}

## Decisions

{self._format_reviews(reviews)}

---
*Technical review by Technical Director agent*
"""

        filepath.write_text(content)
        return str(filepath)

    def _save_standards(
        self,
        project_path: str,
        standards: List[Dict]
    ) -> str:
        """Save technical standards"""
        standards_dir = Path(project_path) / "docs" / "standards"
        standards_dir.mkdir(parents=True, exist_ok=True)

        filepath = standards_dir / "technical-standards.json"

        # Load existing standards if present
        existing = []
        if filepath.exists():
            existing = json.loads(filepath.read_text())

        # Merge new standards
        all_standards = existing + standards

        filepath.write_text(json.dumps(all_standards, indent=2))
        return str(filepath)

    def _format_reviews(self, reviews: List[Dict]) -> str:
        """Format reviews for markdown"""
        lines = []
        for review in reviews:
            lines.append(f"### {review['decision_id']}")
            lines.append(f"**Recommendation**: {review['recommendation'].upper()}")
            lines.append(f"\n{review['rationale']}\n")
            if review.get('modifications'):
                lines.append("**Required Modifications**:")
                for mod in review['modifications']:
                    lines.append(f"- {mod}")
            lines.append("")

        return "\n".join(lines)
