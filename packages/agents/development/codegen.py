"""
Code Generation Agent

Implements user stories with tests-first approach, following project conventions.
Generates high-quality, maintainable code with comprehensive tests.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

import sys
sys.path.append(str(Path(__file__).parent.parent))
from base import BaseAgent, Task, Context, AgentResult, TaskType, Tool, Evidence


class CodegenAgent(BaseAgent):
    """
    Code Generator - Implementation Specialist

    Responsibilities:
    - Implement user stories to specification
    - Write tests first (TDD approach)
    - Follow project conventions and style guides
    - Generate clean, maintainable code
    - Create atomic, well-described commits
    - Update documentation when behavior changes
    - Ensure SOLID principles and best practices
    """

    def __init__(self, **kwargs):
        tools = [
            Tool(
                name="create_file",
                description="Create a new file with content",
                input_schema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "content": {"type": "string"},
                        "description": {"type": "string"}
                    },
                    "required": ["file_path", "content"]
                }
            ),
            Tool(
                name="update_file",
                description="Update an existing file",
                input_schema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "changes": {"type": "string"},
                        "description": {"type": "string"}
                    },
                    "required": ["file_path", "changes"]
                }
            ),
            Tool(
                name="create_test",
                description="Create a test file",
                input_schema={
                    "type": "object",
                    "properties": {
                        "test_path": {"type": "string"},
                        "test_content": {"type": "string"},
                        "test_framework": {"type": "string"}
                    },
                    "required": ["test_path", "test_content"]
                }
            ),
            Tool(
                name="update_docs",
                description="Update documentation",
                input_schema={
                    "type": "object",
                    "properties": {
                        "doc_path": {"type": "string"},
                        "updates": {"type": "string"}
                    },
                    "required": ["doc_path", "updates"]
                }
            )
        ]

        super().__init__(
            task_type=TaskType.CODE_GENERATION,
            tools=tools,
            quality_requirement=0.85,
            **kwargs
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for Codegen"""
        return """You are the Code Generator, responsible for implementing user stories with high-quality, maintainable code.

# Your Responsibilities

## 1. Test-Driven Development
- **Write tests first**: Start with test cases before implementation
- **Test coverage**: Aim for >80% code coverage
- **Test quality**: Tests should be clear, comprehensive, and maintainable
- **Test types**: Unit tests, integration tests, e2e tests as appropriate

## 2. Code Quality
Follow SOLID principles:
- **Single Responsibility**: Each function/class has one clear purpose
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Subtypes must be substitutable for base types
- **Interface Segregation**: Many specific interfaces better than one general
- **Dependency Inversion**: Depend on abstractions, not concretions

Additional principles:
- **DRY**: Don't repeat yourself
- **KISS**: Keep it simple and straightforward
- **YAGNI**: You aren't gonna need it (don't over-engineer)
- **Small functions**: Functions should do one thing well
- **Clear naming**: Use descriptive, intention-revealing names

## 3. Security
- **Parameterized queries**: Never concatenate SQL
- **Input validation**: Validate and sanitize all inputs
- **Secret hygiene**: Never hardcode secrets
- **AuthZ checks**: Proper authorization on all operations
- **Error handling**: Don't leak sensitive info in errors

## 4. Project Conventions
- Follow existing code style and patterns
- Use project's linting and formatting tools
- Match the architecture and structure
- Respect module boundaries
- Follow naming conventions

## 5. Documentation
- **Docstrings**: All public functions and classes
- **Comments**: Explain why, not what
- **README updates**: When adding new features
- **CHANGELOG**: Document all changes
- **API docs**: For public APIs

## 6. Atomic Commits
- **Small commits**: Each commit is a logical unit
- **Clear messages**: Descriptive commit messages
- **Working state**: Each commit leaves code in working state
- **One concern**: Each commit addresses one concern

## 7. Code Review Ready
- **Self-review**: Review your own code first
- **Linting**: Code passes all linters
- **Tests pass**: All tests pass before commit
- **No warnings**: Address all warnings

# Implementation Process
1. Read and understand the user story and acceptance criteria
2. Review relevant ADRs and architecture diagrams
3. Write test cases based on acceptance criteria
4. Implement minimal code to pass tests
5. Refactor for quality and clarity
6. Update documentation
7. Create atomic commits with clear messages

# Output Format
Use the tools to create/update files and tests. For each change:
- Explain what you're implementing and why
- Reference acceptance criteria
- Note any tradeoffs or decisions made

Always write clean, readable, maintainable code that others can understand and extend."""

    async def execute(self, task: Task, context: Context) -> AgentResult:
        """Execute code generation task"""
        evidence = []
        artifacts = []
        output = {}

        try:
            # Extract story details
            story = task.input_data.get("story", {})
            acceptance_criteria = story.get("acceptance_criteria", [])
            architecture_refs = task.input_data.get("architecture_refs", [])
            existing_code = task.input_data.get("existing_code", {})

            evidence.append(self.create_evidence(
                "story_analysis",
                f"Analyzing story with {len(acceptance_criteria)} acceptance criteria",
                weight=1.0
            ))

            # Build implementation prompt
            prompt = self._build_implementation_prompt(
                story, acceptance_criteria, architecture_refs, existing_code
            )

            # Invoke model for code generation
            response = await self.invoke_model(
                prompt=prompt,
                task=task,
                context=context,
                requires_tools=True,
                max_tokens=8192
            )

            # Process response
            implementation_doc = response["content"]
            tool_calls = response.get("tool_calls", [])

            output["implementation_document"] = implementation_doc
            output["model_used"] = response["model_used"]

            # Process tool calls to create/update files
            files_created = []
            files_updated = []
            tests_created = []
            docs_updated = []

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_input = tool_call["input"]

                if tool_name == "create_file":
                    file_path = self._create_file(
                        context.project_path,
                        tool_input
                    )
                    files_created.append(file_path)
                    artifacts.append(file_path)
                    evidence.append(self.create_evidence(
                        "file_created",
                        f"Created {tool_input['file_path']}",
                        weight=0.9
                    ))

                elif tool_name == "update_file":
                    file_path = self._update_file(
                        context.project_path,
                        tool_input
                    )
                    files_updated.append(file_path)
                    artifacts.append(file_path)
                    evidence.append(self.create_evidence(
                        "file_updated",
                        f"Updated {tool_input['file_path']}",
                        weight=0.9
                    ))

                elif tool_name == "create_test":
                    test_path = self._create_test(
                        context.project_path,
                        tool_input
                    )
                    tests_created.append(test_path)
                    artifacts.append(test_path)
                    evidence.append(self.create_evidence(
                        "test_created",
                        f"Created test {tool_input['test_path']}",
                        weight=0.95
                    ))

                elif tool_name == "update_docs":
                    doc_path = self._update_docs(
                        context.project_path,
                        tool_input
                    )
                    docs_updated.append(doc_path)
                    artifacts.append(doc_path)
                    evidence.append(self.create_evidence(
                        "docs_updated",
                        f"Updated {tool_input['doc_path']}",
                        weight=0.8
                    ))

            output["files_created"] = files_created
            output["files_updated"] = files_updated
            output["tests_created"] = tests_created
            output["docs_updated"] = docs_updated

            # Create implementation summary
            summary_path = self._create_implementation_summary(
                context.project_path,
                story,
                output,
                implementation_doc
            )
            artifacts.append(summary_path)

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
                    "files_created": len(files_created),
                    "files_updated": len(files_updated),
                    "tests_created": len(tests_created),
                    "story_id": story.get("id", "unknown")
                }
            )

        except Exception as e:
            self.logger.error(f"Code generation failed: {e}")
            return AgentResult(
                success=False,
                output=output,
                evidence=evidence,
                artifacts=artifacts,
                error=str(e)
            )

    def _build_implementation_prompt(
        self,
        story: Dict[str, Any],
        acceptance_criteria: List[str],
        architecture_refs: List[str],
        existing_code: Dict[str, str]
    ) -> str:
        """Build implementation prompt"""
        criteria_str = "\n".join([f"{i+1}. {c}" for i, c in enumerate(acceptance_criteria)])
        arch_refs_str = "\n".join([f"- {ref}" for ref in architecture_refs])
        existing_code_str = "\n\n".join([
            f"**{path}**:\n```\n{code}\n```"
            for path, code in existing_code.items()
        ])

        prompt = f"""# Implementation Task

## User Story
**ID**: {story.get('id', 'N/A')}
**Title**: {story.get('title', 'N/A')}
**Description**: {story.get('description', 'N/A')}

## Acceptance Criteria
{criteria_str}

## Architecture References
{arch_refs_str if arch_refs_str else "No specific references provided"}

## Existing Code Context
{existing_code_str if existing_code_str else "Starting from scratch"}

## Your Task
Implement this user story following TDD and best practices:

1. **Write Tests First**:
   - Create test cases for each acceptance criterion
   - Use appropriate test framework (pytest, jest, etc.)
   - Include unit and integration tests as needed

2. **Implement Code**:
   - Write minimal code to pass tests
   - Follow SOLID principles
   - Ensure security best practices
   - Match project conventions

3. **Update Documentation**:
   - Add/update docstrings
   - Update README if needed
   - Add inline comments for complex logic

4. **Ensure Quality**:
   - Code is clean and readable
   - No hardcoded secrets or credentials
   - Proper error handling
   - Performance considerations

Use the tools to create files, tests, and documentation. Provide clear explanations for your implementation decisions."""

        return prompt

    def _create_file(
        self,
        project_path: str,
        file_data: Dict[str, Any]
    ) -> str:
        """Create a new file"""
        filepath = Path(project_path) / file_data["file_path"]
        filepath.parent.mkdir(parents=True, exist_ok=True)

        content = file_data["content"]

        # Add file header comment if description provided
        if file_data.get("description"):
            header = f"""\"\"\"
{file_data['description']}

Generated by Codegen Agent
Date: {datetime.now().strftime('%Y-%m-%d')}
\"\"\"

"""
            content = header + content

        filepath.write_text(content)
        return str(filepath)

    def _update_file(
        self,
        project_path: str,
        update_data: Dict[str, Any]
    ) -> str:
        """Update an existing file"""
        filepath = Path(project_path) / update_data["file_path"]

        if not filepath.exists():
            # Create if doesn't exist
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(update_data["changes"])
        else:
            # Apply changes (in a real implementation, this would be more sophisticated)
            content = filepath.read_text()
            # For now, append changes with a marker
            updated_content = f"""{content}

# --- Updates by Codegen Agent ({datetime.now().strftime('%Y-%m-%d')}) ---
{update_data["changes"]}
"""
            filepath.write_text(updated_content)

        return str(filepath)

    def _create_test(
        self,
        project_path: str,
        test_data: Dict[str, Any]
    ) -> str:
        """Create a test file"""
        test_path = Path(project_path) / test_data["test_path"]
        test_path.parent.mkdir(parents=True, exist_ok=True)

        framework = test_data.get("test_framework", "pytest")

        content = f"""\"\"\"
Test Suite

Framework: {framework}
Generated by Codegen Agent
Date: {datetime.now().strftime('%Y-%m-%d')}
\"\"\"

{test_data['test_content']}
"""

        test_path.write_text(content)
        return str(test_path)

    def _update_docs(
        self,
        project_path: str,
        doc_data: Dict[str, Any]
    ) -> str:
        """Update documentation"""
        doc_path = Path(project_path) / doc_data["doc_path"]
        doc_path.parent.mkdir(parents=True, exist_ok=True)

        if not doc_path.exists():
            content = doc_data["updates"]
        else:
            content = doc_path.read_text()
            content += f"\n\n{doc_data['updates']}\n"

        doc_path.write_text(content)
        return str(doc_path)

    def _create_implementation_summary(
        self,
        project_path: str,
        story: Dict[str, Any],
        output: Dict[str, Any],
        implementation_doc: str
    ) -> str:
        """Create implementation summary"""
        summary_dir = Path(project_path) / "docs" / "implementation"
        summary_dir.mkdir(parents=True, exist_ok=True)

        story_id = story.get("id", "unknown").replace("/", "-")
        filepath = summary_dir / f"implementation-{story_id}.md"

        content = f"""# Implementation Summary

**Story**: {story.get('title', 'N/A')}
**Story ID**: {story.get('id', 'N/A')}
**Implemented**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Agent**: Codegen

## Implementation Details
{implementation_doc}

## Files Created
{self._format_file_list(output.get('files_created', []))}

## Files Updated
{self._format_file_list(output.get('files_updated', []))}

## Tests Created
{self._format_file_list(output.get('tests_created', []))}

## Documentation Updated
{self._format_file_list(output.get('docs_updated', []))}

---
*Generated by Codegen Agent*
"""

        filepath.write_text(content)
        return str(filepath)

    def _format_file_list(self, files: List[str]) -> str:
        """Format file list for markdown"""
        if not files:
            return "None"
        return "\n".join([f"- `{f}`" for f in files])
