"""
Migration Specialist Agent

Analyzes migration scope, generates incremental migration plans, implements migration steps,
validates at each step, and creates comprehensive migration guides.
"""
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

import sys
sys.path.append(str(Path(__file__).parent.parent))
from base import BaseAgent, Task, Context, AgentResult, TaskType, Tool, Evidence


class MigrationSpecialistAgent(BaseAgent):
    """
    Migration Specialist - Complex Migration Expert

    Responsibilities:
    - Analyze migration scope and complexity
    - Generate incremental, safe migration plans
    - Implement migration steps with rollback capability
    - Validate data and behavior at each step
    - Create comprehensive migration guides
    - Handle schema migrations, code migrations, and data migrations
    - Ensure zero-downtime where possible
    """

    def __init__(self, **kwargs):
        tools = [
            Tool(
                name="analyze_migration_scope",
                description="Analyze migration scope and complexity",
                input_schema={
                    "type": "object",
                    "properties": {
                        "migration_type": {"type": "string"},
                        "from_version": {"type": "string"},
                        "to_version": {"type": "string"},
                        "affected_components": {"type": "array", "items": {"type": "string"}},
                        "estimated_complexity": {"type": "string", "enum": ["low", "medium", "high", "very_high"]},
                        "risk_assessment": {"type": "string"}
                    },
                    "required": ["migration_type", "affected_components", "estimated_complexity"]
                }
            ),
            Tool(
                name="create_migration_step",
                description="Create a migration step",
                input_schema={
                    "type": "object",
                    "properties": {
                        "step_number": {"type": "integer"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "implementation": {"type": "string"},
                        "validation": {"type": "string"},
                        "rollback": {"type": "string"},
                        "dependencies": {"type": "array", "items": {"type": "integer"}}
                    },
                    "required": ["step_number", "title", "description", "implementation", "validation", "rollback"]
                }
            ),
            Tool(
                name="create_migration_script",
                description="Create a migration script",
                input_schema={
                    "type": "object",
                    "properties": {
                        "script_name": {"type": "string"},
                        "script_type": {"type": "string", "enum": ["schema", "data", "code"]},
                        "script_content": {"type": "string"},
                        "rollback_script": {"type": "string"}
                    },
                    "required": ["script_name", "script_type", "script_content"]
                }
            ),
            Tool(
                name="create_validation_test",
                description="Create a validation test for migration",
                input_schema={
                    "type": "object",
                    "properties": {
                        "test_name": {"type": "string"},
                        "test_content": {"type": "string"},
                        "validation_criteria": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["test_name", "test_content", "validation_criteria"]
                }
            )
        ]

        super().__init__(
            task_type=TaskType.CODE_GENERATION,  # Migrations involve code generation
            tools=tools,
            quality_requirement=0.9,  # High quality for migrations
            **kwargs
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for Migration Specialist"""
        return """You are the Migration Specialist, responsible for planning and executing complex migrations safely and incrementally.

# Your Responsibilities

## 1. Migration Analysis
Analyze migration requirements:
- **Scope**: What needs to be migrated?
- **Dependencies**: What are the dependencies and constraints?
- **Risks**: What could go wrong?
- **Complexity**: How complex is this migration?
- **Impact**: What systems/users are affected?
- **Timeline**: What's the migration timeline?

## 2. Migration Planning
Create detailed migration plans:
- **Incremental**: Break into small, safe steps
- **Reversible**: Each step has a rollback plan
- **Validated**: Each step includes validation
- **Zero-downtime**: Minimize downtime where possible
- **Phased**: Consider phased rollout strategies

## 3. Migration Types
Handle different migration types:
- **Schema Migration**: Database schema changes
- **Data Migration**: Data transformation and movement
- **Code Migration**: API changes, framework upgrades
- **Platform Migration**: Cloud platform changes
- **Version Migration**: Major version upgrades

## 4. Safety Principles
Ensure safe migrations:
- **Backward Compatibility**: Maintain compatibility during migration
- **Dual Write**: Write to both old and new during transition
- **Feature Flags**: Use flags to control rollout
- **Canary Deployment**: Test with subset of traffic first
- **Monitoring**: Monitor metrics closely during migration
- **Rollback Plan**: Always have a rollback plan

## 5. Migration Steps Structure
Each step should include:
- **Implementation**: What to do
- **Validation**: How to verify it worked
- **Rollback**: How to undo if needed
- **Monitoring**: What to monitor
- **Success Criteria**: When to proceed to next step

## 6. Data Migration Patterns
Use appropriate patterns:
- **Stop-the-World**: Brief downtime for simple migrations
- **Dual-Write**: Write to both old and new
- **Read-from-Old**: Gradually switch reads
- **Backfill**: Migrate historical data separately
- **Shadow Mode**: Run new system in parallel

## 7. Validation
Validate at each step:
- **Data Integrity**: Data is correct and complete
- **Behavior Preservation**: System behaves correctly
- **Performance**: Performance is acceptable
- **Completeness**: All data migrated
- **Consistency**: Data is consistent

## 8. Documentation
Create comprehensive guides:
- **Migration Plan**: Step-by-step plan
- **Runbook**: Operational procedures
- **Rollback Procedures**: How to rollback
- **Monitoring Guide**: What to watch
- **Troubleshooting**: Common issues and solutions

# Migration Best Practices
1. **Test in Production-Like Environment**: Test thoroughly
2. **Start Small**: Migrate small subset first
3. **Monitor Closely**: Watch metrics during migration
4. **Have Rollback Ready**: Be prepared to rollback
5. **Communicate**: Keep stakeholders informed
6. **Validate Continuously**: Validate at each step
7. **Document Everything**: Document decisions and steps

# Output Format
Use tools to:
- Analyze scope and create migration analysis
- Create detailed migration steps
- Generate migration scripts
- Create validation tests

Provide comprehensive migration guide with:
- Clear step-by-step instructions
- Rollback procedures
- Validation checkpoints
- Monitoring guidelines
- Risk mitigation strategies"""

    async def execute(self, task: Task, context: Context) -> AgentResult:
        """Execute migration planning/implementation task"""
        evidence = []
        artifacts = []
        output = {}

        try:
            # Extract migration details
            migration_type = task.input_data.get("migration_type", "")
            from_version = task.input_data.get("from_version", "")
            to_version = task.input_data.get("to_version", "")
            requirements = task.input_data.get("requirements", "")
            constraints = task.input_data.get("constraints", {})

            evidence.append(self.create_evidence(
                "migration_analysis_started",
                f"Analyzing {migration_type} migration from {from_version} to {to_version}",
                weight=1.0
            ))

            # Build migration prompt
            prompt = self._build_migration_prompt(
                migration_type, from_version, to_version, requirements, constraints
            )

            # Invoke model for migration planning
            response = await self.invoke_model(
                prompt=prompt,
                task=task,
                context=context,
                requires_tools=True,
                max_tokens=8192
            )

            # Process response
            migration_doc = response["content"]
            tool_calls = response.get("tool_calls", [])

            output["migration_document"] = migration_doc
            output["model_used"] = response["model_used"]

            # Process tool calls
            scope_analysis = None
            migration_steps = []
            migration_scripts = []
            validation_tests = []

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_input = tool_call["input"]

                if tool_name == "analyze_migration_scope":
                    scope_analysis = tool_input
                    evidence.append(self.create_evidence(
                        "scope_analyzed",
                        f"{tool_input['estimated_complexity'].upper()} complexity migration affecting {len(tool_input['affected_components'])} components",
                        weight=0.95
                    ))

                elif tool_name == "create_migration_step":
                    step = tool_input
                    migration_steps.append(step)
                    evidence.append(self.create_evidence(
                        "migration_step_created",
                        f"Step {step['step_number']}: {step['title']}",
                        weight=0.9
                    ))

                elif tool_name == "create_migration_script":
                    script_path = self._create_migration_script(
                        context.project_path,
                        tool_input
                    )
                    migration_scripts.append(script_path)
                    artifacts.append(script_path)
                    evidence.append(self.create_evidence(
                        "migration_script_created",
                        f"Created {tool_input['script_type']} script: {tool_input['script_name']}",
                        weight=0.9
                    ))

                elif tool_name == "create_validation_test":
                    test_path = self._create_validation_test(
                        context.project_path,
                        tool_input
                    )
                    validation_tests.append(test_path)
                    artifacts.append(test_path)
                    evidence.append(self.create_evidence(
                        "validation_test_created",
                        f"Created validation test: {tool_input['test_name']}",
                        weight=0.9
                    ))

            # Sort migration steps by step number
            migration_steps.sort(key=lambda x: x['step_number'])

            # Create comprehensive migration guide
            guide_path = self._create_migration_guide(
                context.project_path,
                scope_analysis,
                migration_steps,
                migration_scripts,
                validation_tests,
                migration_doc
            )
            artifacts.append(guide_path)

            output["scope_analysis"] = scope_analysis
            output["migration_steps"] = migration_steps
            output["migration_scripts"] = migration_scripts
            output["validation_tests"] = validation_tests

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
                    "complexity": scope_analysis.get("estimated_complexity") if scope_analysis else "unknown",
                    "steps_count": len(migration_steps),
                    "scripts_count": len(migration_scripts),
                    "tests_count": len(validation_tests)
                }
            )

        except Exception as e:
            self.logger.error(f"Migration planning failed: {e}")
            return AgentResult(
                success=False,
                output=output,
                evidence=evidence,
                artifacts=artifacts,
                error=str(e)
            )

    def _build_migration_prompt(
        self,
        migration_type: str,
        from_version: str,
        to_version: str,
        requirements: str,
        constraints: Dict[str, Any]
    ) -> str:
        """Build migration prompt"""
        prompt = f"""# Migration Planning Task

## Migration Type
{migration_type}

## Version Transition
From: {from_version}
To: {to_version}

## Requirements
{requirements}

## Constraints
{json.dumps(constraints, indent=2)}

## Your Task
Create a comprehensive migration plan:

1. **Analyze Scope**:
   - Use analyze_migration_scope tool
   - Identify all affected components
   - Assess complexity and risks
   - Estimate timeline and effort

2. **Create Migration Steps**:
   - Break migration into incremental steps
   - Each step should be:
     * Small and safe
     * Independently executable
     * Reversible (with rollback)
     * Validated (with verification)
   - Order steps by dependencies

3. **Generate Migration Scripts**:
   - Schema migration scripts
   - Data migration scripts
   - Code migration helpers
   - Include rollback scripts

4. **Create Validation Tests**:
   - Tests to verify each migration step
   - Data integrity checks
   - Behavior verification tests
   - Performance validation

5. **Consider Zero-Downtime**:
   - Can migration be done without downtime?
   - Use dual-write patterns if needed
   - Plan phased rollout

6. **Risk Mitigation**:
   - Identify risks at each step
   - Provide mitigation strategies
   - Define success criteria
   - Plan monitoring approach

Use the tools to create a complete, executable migration plan."""

        return prompt

    def _create_migration_script(
        self,
        project_path: str,
        script_data: Dict[str, Any]
    ) -> str:
        """Create migration script"""
        migrations_dir = Path(project_path) / "migrations"
        migrations_dir.mkdir(parents=True, exist_ok=True)

        script_type = script_data["script_type"]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        script_name = script_data["script_name"].replace(" ", "_").lower()

        filename = f"{timestamp}_{script_type}_{script_name}.sql"
        if script_type == "code":
            filename = f"{timestamp}_{script_type}_{script_name}.py"

        filepath = migrations_dir / filename

        content = f"""-- Migration Script
-- Type: {script_type}
-- Name: {script_data['script_name']}
-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{script_data['script_content']}

-- Rollback Script
{script_data.get('rollback_script', '-- No rollback script provided')}
"""

        filepath.write_text(content)
        return str(filepath)

    def _create_validation_test(
        self,
        project_path: str,
        test_data: Dict[str, Any]
    ) -> str:
        """Create validation test"""
        tests_dir = Path(project_path) / "tests" / "migration"
        tests_dir.mkdir(parents=True, exist_ok=True)

        test_name = test_data["test_name"].replace(" ", "_").lower()
        filepath = tests_dir / f"test_{test_name}.py"

        content = f"""\"\"\"
Migration Validation Test: {test_data['test_name']}

Validation Criteria:
{self._format_criteria(test_data['validation_criteria'])}

Generated by Migration Specialist
Date: {datetime.now().strftime('%Y-%m-%d')}
\"\"\"

{test_data['test_content']}
"""

        filepath.write_text(content)
        return str(filepath)

    def _create_migration_guide(
        self,
        project_path: str,
        scope: Optional[Dict],
        steps: List[Dict],
        scripts: List[str],
        tests: List[str],
        migration_doc: str
    ) -> str:
        """Create comprehensive migration guide"""
        docs_dir = Path(project_path) / "docs" / "migration"
        docs_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filepath = docs_dir / f"migration-guide-{timestamp}.md"

        content = f"""# Migration Guide

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Agent: Migration Specialist

## Overview
{migration_doc}

## Scope Analysis
{self._format_scope_analysis(scope)}

## Migration Steps ({len(steps)})
{self._format_migration_steps(steps)}

## Migration Scripts ({len(scripts)})
{self._format_script_list(scripts)}

## Validation Tests ({len(tests)})
{self._format_test_list(tests)}

## Pre-Migration Checklist
- [ ] Review migration plan with team
- [ ] Test migration in staging environment
- [ ] Verify backup procedures
- [ ] Prepare rollback plan
- [ ] Set up monitoring and alerts
- [ ] Communicate timeline to stakeholders
- [ ] Schedule maintenance window (if needed)

## During Migration
- [ ] Monitor system metrics closely
- [ ] Validate each step before proceeding
- [ ] Keep stakeholders informed
- [ ] Document any issues encountered
- [ ] Be ready to rollback if needed

## Post-Migration Checklist
- [ ] Verify all validation tests pass
- [ ] Check system metrics are normal
- [ ] Confirm no data loss
- [ ] Update documentation
- [ ] Communicate completion
- [ ] Schedule post-migration review

## Rollback Procedures
If migration needs to be rolled back:
1. Stop migration process immediately
2. Execute rollback scripts in reverse order
3. Verify system is in stable state
4. Investigate root cause
5. Update migration plan before retry

## Monitoring
Key metrics to monitor:
- Error rates
- Response times
- Database query performance
- Resource utilization
- User experience metrics

## Troubleshooting
Common issues and solutions will be documented here during migration.

---
*Generated by Migration Specialist Agent*
"""

        filepath.write_text(content)
        return str(filepath)

    def _format_criteria(self, criteria: List[str]) -> str:
        """Format validation criteria"""
        return "\n".join([f"- {c}" for c in criteria])

    def _format_scope_analysis(self, scope: Optional[Dict]) -> str:
        """Format scope analysis"""
        if not scope:
            return "Scope analysis not available."

        lines = [
            f"**Migration Type**: {scope.get('migration_type', 'N/A')}",
            f"**Complexity**: {scope.get('estimated_complexity', 'N/A').upper()}",
            f"**From Version**: {scope.get('from_version', 'N/A')}",
            f"**To Version**: {scope.get('to_version', 'N/A')}",
            f"\n**Affected Components**: {len(scope.get('affected_components', []))}",
        ]

        for component in scope.get('affected_components', []):
            lines.append(f"- {component}")

        if scope.get('risk_assessment'):
            lines.append(f"\n**Risk Assessment**:\n{scope['risk_assessment']}")

        return "\n".join(lines)

    def _format_migration_steps(self, steps: List[Dict]) -> str:
        """Format migration steps"""
        if not steps:
            return "No migration steps defined."

        lines = []
        for step in steps:
            lines.append(f"### Step {step['step_number']}: {step['title']}")
            lines.append(f"\n{step['description']}\n")
            lines.append("**Implementation**:")
            lines.append(f"```\n{step['implementation']}\n```")
            lines.append("\n**Validation**:")
            lines.append(f"```\n{step['validation']}\n```")
            lines.append("\n**Rollback**:")
            lines.append(f"```\n{step['rollback']}\n```")
            if step.get('dependencies'):
                lines.append(f"\n**Dependencies**: Steps {', '.join(map(str, step['dependencies']))}")
            lines.append("")

        return "\n".join(lines)

    def _format_script_list(self, scripts: List[str]) -> str:
        """Format script list"""
        if not scripts:
            return "No scripts generated."
        return "\n".join([f"- `{Path(s).name}`" for s in scripts])

    def _format_test_list(self, tests: List[str]) -> str:
        """Format test list"""
        if not tests:
            return "No validation tests generated."
        return "\n".join([f"- `{Path(t).name}`" for t in tests])
