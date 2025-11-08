"""
Refactor Agent

Identifies code smells, proposes refactoring plans, and executes safe refactorings
while maintaining test coverage and documenting changes.
"""
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

import sys
sys.path.append(str(Path(__file__).parent.parent))
from base import BaseAgent, Task, Context, AgentResult, TaskType, Tool, Evidence


class RefactorAgent(BaseAgent):
    """
    Refactor Agent - Code Quality Improvement Specialist

    Responsibilities:
    - Identify code smells and technical debt
    - Propose refactoring plans with risk assessment
    - Execute safe, incremental refactorings
    - Maintain or improve test coverage during refactoring
    - Document refactoring decisions and changes
    - Verify behavior preservation after refactoring
    """

    def __init__(self, **kwargs):
        tools = [
            Tool(
                name="identify_code_smell",
                description="Identify a code smell or technical debt item",
                input_schema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "smell_type": {"type": "string"},
                        "description": {"type": "string"},
                        "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                        "impact": {"type": "string"}
                    },
                    "required": ["file_path", "smell_type", "description", "severity"]
                }
            ),
            Tool(
                name="create_refactoring_plan",
                description="Create a refactoring plan",
                input_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "steps": {"type": "array", "items": {"type": "string"}},
                        "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
                        "estimated_effort": {"type": "string"},
                        "benefits": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["title", "description", "steps", "risk_level"]
                }
            ),
            Tool(
                name="apply_refactoring",
                description="Apply a refactoring to code",
                input_schema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "refactoring_type": {"type": "string"},
                        "original_code": {"type": "string"},
                        "refactored_code": {"type": "string"},
                        "justification": {"type": "string"}
                    },
                    "required": ["file_path", "refactoring_type", "original_code", "refactored_code"]
                }
            ),
            Tool(
                name="update_tests",
                description="Update tests to verify refactoring",
                input_schema={
                    "type": "object",
                    "properties": {
                        "test_path": {"type": "string"},
                        "updates": {"type": "string"},
                        "purpose": {"type": "string"}
                    },
                    "required": ["test_path", "updates"]
                }
            )
        ]

        super().__init__(
            task_type=TaskType.REFACTORING,
            tools=tools,
            quality_requirement=0.85,
            **kwargs
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for Refactor agent"""
        return """You are the Refactor Agent, responsible for improving code quality through systematic refactoring.

# Your Responsibilities

## 1. Code Smell Detection
Identify common code smells:
- **Long Method**: Methods doing too much
- **Large Class**: Classes with too many responsibilities
- **Duplicate Code**: Repeated code blocks
- **Long Parameter List**: Too many parameters
- **Feature Envy**: Method using more of another class
- **Data Clumps**: Groups of data appearing together
- **Primitive Obsession**: Overuse of primitives vs objects
- **Switch Statements**: Type code with conditionals
- **Lazy Class**: Class not doing enough
- **Speculative Generality**: Unused abstraction
- **Dead Code**: Unused code

## 2. Refactoring Catalog
Apply appropriate refactorings:
- **Extract Method**: Break long methods into smaller ones
- **Extract Class**: Split large classes
- **Rename**: Improve naming
- **Move Method/Field**: Improve organization
- **Replace Conditional with Polymorphism**: Remove type switching
- **Introduce Parameter Object**: Group related parameters
- **Replace Magic Number with Constant**: Named constants
- **Decompose Conditional**: Simplify complex conditions
- **Consolidate Duplicate Code**: DRY principle

## 3. Refactoring Process
1. **Identify**: Find code that needs improvement
2. **Analyze**: Understand current behavior and test coverage
3. **Plan**: Create step-by-step refactoring plan
4. **Validate**: Ensure tests exist and pass
5. **Refactor**: Apply changes incrementally
6. **Test**: Run tests after each step
7. **Review**: Verify behavior preservation
8. **Document**: Record refactoring decisions

## 4. Safety Principles
- **Small steps**: Refactor incrementally
- **Test coverage**: Ensure adequate tests before refactoring
- **Green bar**: Keep tests passing
- **Behavior preservation**: Don't change functionality
- **Reversibility**: Be able to undo changes
- **Atomic commits**: Each refactoring is a commit

## 5. Risk Assessment
Evaluate refactoring risk:
- **Low risk**: Rename, extract method with good tests
- **Medium risk**: Move method, change signatures
- **High risk**: Change inheritance, modify public APIs

## 6. Quality Metrics
Track improvements:
- Cyclomatic complexity reduction
- Code duplication reduction
- Test coverage maintenance/improvement
- Readability improvement
- Maintainability index increase

## 7. Documentation
Document refactorings:
- What was changed and why
- Benefits achieved
- Any risks or tradeoffs
- Future improvement opportunities

# Refactoring Guidelines
1. **Tests first**: Ensure good test coverage
2. **One change**: One refactoring at a time
3. **Run tests**: After every change
4. **Small commits**: Commit working code frequently
5. **Communicate**: Explain rationale clearly
6. **Metrics**: Measure improvement

# Output Format
Use tools to identify smells, create plans, apply refactorings, and update tests.
Provide clear explanations of:
- What you're refactoring and why
- Benefits of the refactoring
- How you're preserving behavior
- Any risks or considerations"""

    async def execute(self, task: Task, context: Context) -> AgentResult:
        """Execute refactoring task"""
        evidence = []
        artifacts = []
        output = {}

        try:
            # Extract refactoring target
            target_files = task.input_data.get("target_files", [])
            refactoring_type = task.input_data.get("refactoring_type", "general")
            existing_code = task.input_data.get("existing_code", {})
            test_coverage = task.input_data.get("test_coverage", {})

            evidence.append(self.create_evidence(
                "refactoring_initiated",
                f"Analyzing {len(target_files)} files for {refactoring_type} refactoring",
                weight=1.0
            ))

            # Build refactoring prompt
            prompt = self._build_refactoring_prompt(
                target_files, refactoring_type, existing_code, test_coverage
            )

            # Invoke model for refactoring analysis
            response = await self.invoke_model(
                prompt=prompt,
                task=task,
                context=context,
                requires_tools=True,
                max_tokens=8192
            )

            # Process response
            refactoring_doc = response["content"]
            tool_calls = response.get("tool_calls", [])

            output["refactoring_document"] = refactoring_doc
            output["model_used"] = response["model_used"]

            # Process tool calls
            code_smells = []
            refactoring_plans = []
            refactorings_applied = []
            tests_updated = []

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_input = tool_call["input"]

                if tool_name == "identify_code_smell":
                    smell = tool_input
                    code_smells.append(smell)
                    evidence.append(self.create_evidence(
                        "code_smell_identified",
                        f"{smell['severity'].upper()} {smell['smell_type']} in {smell['file_path']}",
                        weight=0.85
                    ))

                elif tool_name == "create_refactoring_plan":
                    plan = tool_input
                    refactoring_plans.append(plan)
                    evidence.append(self.create_evidence(
                        "plan_created",
                        f"Created {plan['risk_level']} risk refactoring plan: {plan['title']}",
                        weight=0.9
                    ))

                elif tool_name == "apply_refactoring":
                    refactoring = self._apply_refactoring(
                        context.project_path,
                        tool_input
                    )
                    refactorings_applied.append(refactoring)
                    artifacts.append(refactoring["file_path"])
                    evidence.append(self.create_evidence(
                        "refactoring_applied",
                        f"Applied {tool_input['refactoring_type']} to {tool_input['file_path']}",
                        weight=0.95
                    ))

                elif tool_name == "update_tests":
                    test_path = self._update_tests(
                        context.project_path,
                        tool_input
                    )
                    tests_updated.append(test_path)
                    artifacts.append(test_path)
                    evidence.append(self.create_evidence(
                        "tests_updated",
                        f"Updated tests: {tool_input['test_path']}",
                        weight=0.9
                    ))

            # Save refactoring report
            report_path = self._create_refactoring_report(
                context.project_path,
                code_smells,
                refactoring_plans,
                refactorings_applied,
                refactoring_doc
            )
            artifacts.append(report_path)

            output["code_smells"] = code_smells
            output["refactoring_plans"] = refactoring_plans
            output["refactorings_applied"] = len(refactorings_applied)
            output["tests_updated"] = len(tests_updated)

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
                    "code_smells_found": len(code_smells),
                    "plans_created": len(refactoring_plans),
                    "refactorings_applied": len(refactorings_applied)
                }
            )

        except Exception as e:
            self.logger.error(f"Refactoring failed: {e}")
            return AgentResult(
                success=False,
                output=output,
                evidence=evidence,
                artifacts=artifacts,
                error=str(e)
            )

    def _build_refactoring_prompt(
        self,
        target_files: List[str],
        refactoring_type: str,
        existing_code: Dict[str, str],
        test_coverage: Dict[str, Any]
    ) -> str:
        """Build refactoring prompt"""
        files_str = "\n".join([f"- {f}" for f in target_files])
        code_str = "\n\n".join([
            f"**{path}**:\n```\n{code}\n```"
            for path, code in existing_code.items()
        ])

        prompt = f"""# Refactoring Task

## Target Files
{files_str}

## Refactoring Type
{refactoring_type}

## Current Code
{code_str}

## Test Coverage
{json.dumps(test_coverage, indent=2) if test_coverage else "Coverage information not available"}

## Your Task
Analyze the code and perform refactoring:

1. **Identify Code Smells**:
   - Use the identify_code_smell tool for each issue found
   - Assess severity and impact
   - Provide clear descriptions

2. **Create Refactoring Plans**:
   - For each significant refactoring needed
   - Break down into safe, incremental steps
   - Assess risk level
   - Document benefits

3. **Apply Refactorings**:
   - Execute refactorings incrementally
   - Preserve behavior (no functionality changes)
   - Improve code quality and readability
   - Follow SOLID principles

4. **Update Tests**:
   - Ensure tests still pass
   - Add tests if coverage is insufficient
   - Update tests if interfaces changed

Prioritize:
- High impact, low risk refactorings first
- Maintaining or improving test coverage
- Behavior preservation
- Incremental, reversible changes

Use the tools to identify issues, create plans, apply refactorings, and update tests."""

        return prompt

    def _apply_refactoring(
        self,
        project_path: str,
        refactoring_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply refactoring to file"""
        filepath = Path(project_path) / refactoring_data["file_path"]

        # Create backup
        backup_path = filepath.with_suffix(filepath.suffix + ".backup")
        if filepath.exists():
            backup_path.write_text(filepath.read_text())

        # Apply refactoring
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(refactoring_data["refactored_code"])

        return {
            "file_path": str(filepath),
            "backup_path": str(backup_path),
            "refactoring_type": refactoring_data["refactoring_type"],
            "justification": refactoring_data.get("justification", ""),
            "applied_at": datetime.now().isoformat()
        }

    def _update_tests(
        self,
        project_path: str,
        test_data: Dict[str, Any]
    ) -> str:
        """Update test file"""
        test_path = Path(project_path) / test_data["test_path"]
        test_path.parent.mkdir(parents=True, exist_ok=True)

        if not test_path.exists():
            content = test_data["updates"]
        else:
            content = test_path.read_text()
            content += f"\n\n# Updated for refactoring ({datetime.now().strftime('%Y-%m-%d')})\n"
            content += test_data["updates"]

        test_path.write_text(content)
        return str(test_path)

    def _create_refactoring_report(
        self,
        project_path: str,
        code_smells: List[Dict],
        plans: List[Dict],
        applied: List[Dict],
        refactoring_doc: str
    ) -> str:
        """Create refactoring report"""
        report_dir = Path(project_path) / "docs" / "refactoring"
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filepath = report_dir / f"refactoring-report-{timestamp}.md"

        content = f"""# Refactoring Report

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Agent: Refactor Agent

## Overview
{refactoring_doc}

## Code Smells Identified ({len(code_smells)})
{self._format_code_smells(code_smells)}

## Refactoring Plans ({len(plans)})
{self._format_plans(plans)}

## Refactorings Applied ({len(applied)})
{self._format_applied(applied)}

---
*Generated by Refactor Agent*
"""

        filepath.write_text(content)
        return str(filepath)

    def _format_code_smells(self, smells: List[Dict]) -> str:
        """Format code smells for markdown"""
        if not smells:
            return "No code smells identified."

        lines = []
        for smell in smells:
            lines.append(f"### {smell['smell_type']} - {smell['severity'].upper()}")
            lines.append(f"**File**: {smell['file_path']}")
            lines.append(f"**Description**: {smell['description']}")
            if smell.get('impact'):
                lines.append(f"**Impact**: {smell['impact']}")
            lines.append("")

        return "\n".join(lines)

    def _format_plans(self, plans: List[Dict]) -> str:
        """Format refactoring plans for markdown"""
        if not plans:
            return "No refactoring plans created."

        lines = []
        for plan in plans:
            lines.append(f"### {plan['title']}")
            lines.append(f"**Risk Level**: {plan['risk_level'].upper()}")
            lines.append(f"**Effort**: {plan.get('estimated_effort', 'Not estimated')}")
            lines.append(f"\n{plan['description']}\n")
            lines.append("**Steps**:")
            for i, step in enumerate(plan['steps'], 1):
                lines.append(f"{i}. {step}")
            if plan.get('benefits'):
                lines.append("\n**Benefits**:")
                for benefit in plan['benefits']:
                    lines.append(f"- {benefit}")
            lines.append("")

        return "\n".join(lines)

    def _format_applied(self, applied: List[Dict]) -> str:
        """Format applied refactorings for markdown"""
        if not applied:
            return "No refactorings applied."

        lines = []
        for refactoring in applied:
            lines.append(f"### {refactoring['refactoring_type']}")
            lines.append(f"**File**: {refactoring['file_path']}")
            lines.append(f"**Applied**: {refactoring['applied_at']}")
            if refactoring.get('justification'):
                lines.append(f"\n{refactoring['justification']}\n")
            lines.append("")

        return "\n".join(lines)
