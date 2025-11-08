"""
Chief Architect Agent

Translates product requirements into concrete, evolvable system architectures.
Produces Architecture Decision Records (ADRs), diagrams, and technical specifications.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

import sys
sys.path.append(str(Path(__file__).parent.parent))
from base import BaseAgent, Task, Context, AgentResult, TaskType, Tool, Evidence


class ChiefArchitectAgent(BaseAgent):
    """
    Chief Architect - Strategic Technical Design

    Responsibilities:
    - Convert product requirements into system architecture
    - Generate Architecture Decision Records (ADRs)
    - Create Mermaid diagrams (C4, sequence, ER, deployment)
    - Define API boundaries and data models
    - Specify non-functional requirements (SLOs, performance budgets)
    - Provide technology stack recommendations
    - Define rollback and migration strategies
    """

    def __init__(self, **kwargs):
        # Define tools for architecture work
        tools = [
            Tool(
                name="create_adr",
                description="Create an Architecture Decision Record",
                input_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "context": {"type": "string"},
                        "decision": {"type": "string"},
                        "consequences": {"type": "string"},
                        "alternatives": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["title", "context", "decision", "consequences"]
                }
            ),
            Tool(
                name="create_diagram",
                description="Create a Mermaid diagram",
                input_schema={
                    "type": "object",
                    "properties": {
                        "diagram_type": {
                            "type": "string",
                            "enum": ["c4", "sequence", "er", "deployment", "class", "flowchart"]
                        },
                        "title": {"type": "string"},
                        "mermaid_code": {"type": "string"}
                    },
                    "required": ["diagram_type", "title", "mermaid_code"]
                }
            ),
            Tool(
                name="define_api_contract",
                description="Define API boundary contract",
                input_schema={
                    "type": "object",
                    "properties": {
                        "service_name": {"type": "string"},
                        "endpoints": {"type": "array"},
                        "data_models": {"type": "object"}
                    },
                    "required": ["service_name", "endpoints"]
                }
            )
        ]

        super().__init__(
            task_type=TaskType.PLANNING,
            tools=tools,
            quality_requirement=0.9,  # High quality for architecture
            **kwargs
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for Chief Architect"""
        return """You are the Chief Architect, responsible for translating product requirements into concrete, evolvable system architectures.

# Your Responsibilities

## 1. Architecture Design
- Analyze product requirements and create system architecture
- Define modular boundaries and component interactions
- Ensure scalability, maintainability, and evolvability
- Prefer modular monolith for MVP unless scale demands otherwise

## 2. Architecture Decision Records (ADRs)
For each significant decision, create an ADR with:
- **Context**: What problem are we solving? What constraints exist?
- **Decision**: What did we decide and why?
- **Consequences**: What are the implications (positive and negative)?
- **Alternatives**: What other options were considered and why were they rejected?

## 3. Diagrams
Create Mermaid diagrams to visualize:
- **C4 Model**: System context, container, component views
- **Sequence Diagrams**: Key interaction flows
- **ER Diagrams**: Data model relationships
- **Deployment Diagrams**: Infrastructure and deployment topology

## 4. API Boundaries
- Define clear public interfaces between modules/services
- Specify data contracts and versioning strategy
- Hide implementation details behind interfaces
- Plan for backward compatibility

## 5. Non-Functional Requirements
- Define SLOs (Service Level Objectives)
- Set performance budgets
- Specify security requirements
- Define monitoring and observability strategy

## 6. Technology Stack
- Recommend appropriate technologies
- Consider team expertise and ecosystem maturity
- Balance innovation with stability
- Document rationale for each choice

## 7. Migration & Rollback
- Provide incremental migration paths
- Define rollback strategies
- Ensure backward compatibility where needed

# Design Principles
1. **Modularity**: Design for loose coupling and high cohesion
2. **Simplicity**: Start simple, add complexity when needed
3. **Evolvability**: Design for change
4. **Documentation**: Every decision is documented with rationale
5. **Pragmatism**: Balance ideal architecture with practical constraints

# Output Format
Your outputs should be structured and include:
- ADRs in markdown format
- Mermaid diagram specifications
- API contracts in JSON/YAML
- Technical specifications
- Implementation guidance

Always provide evidence IDs for your decisions and reference source requirements."""

    async def execute(self, task: Task, context: Context) -> AgentResult:
        """Execute architecture design task"""
        evidence = []
        artifacts = []
        output = {}

        try:
            # Extract requirements from task
            requirements = task.input_data.get("requirements", "")
            project_type = task.input_data.get("project_type", "web_application")
            constraints = task.input_data.get("constraints", {})

            # Add evidence for input analysis
            evidence.append(self.create_evidence(
                "input_analysis",
                f"Analyzed requirements for {project_type} with {len(constraints)} constraints",
                weight=1.0
            ))

            # Create architecture prompt
            prompt = self._build_architecture_prompt(
                requirements, project_type, constraints
            )

            # Invoke model to generate architecture
            response = await self.invoke_model(
                prompt=prompt,
                task=task,
                context=context,
                requires_tools=True,
                max_tokens=8192
            )

            # Process response
            architecture_doc = response["content"]
            tool_calls = response.get("tool_calls", [])

            output["architecture_document"] = architecture_doc
            output["model_used"] = response["model_used"]
            output["execution_time_ms"] = response["execution_time_ms"]

            # Process tool calls to create artifacts
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_input = tool_call["input"]

                if tool_name == "create_adr":
                    adr_path = self._create_adr_file(
                        context.project_path,
                        tool_input
                    )
                    artifacts.append(adr_path)
                    evidence.append(self.create_evidence(
                        "adr_created",
                        f"Created ADR: {tool_input['title']}",
                        weight=0.95
                    ))

                elif tool_name == "create_diagram":
                    diagram_path = self._create_diagram_file(
                        context.project_path,
                        tool_input
                    )
                    artifacts.append(diagram_path)
                    evidence.append(self.create_evidence(
                        "diagram_created",
                        f"Created {tool_input['diagram_type']} diagram: {tool_input['title']}",
                        weight=0.9
                    ))

                elif tool_name == "define_api_contract":
                    contract_path = self._create_api_contract_file(
                        context.project_path,
                        tool_input
                    )
                    artifacts.append(contract_path)
                    evidence.append(self.create_evidence(
                        "api_contract_defined",
                        f"Defined API contract for {tool_input['service_name']}",
                        weight=0.9
                    ))

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
                    "adr_count": len([a for a in artifacts if "adr" in a]),
                    "diagram_count": len([a for a in artifacts if "diagram" in a]),
                    "tool_calls": len(tool_calls)
                }
            )

        except Exception as e:
            self.logger.error(f"Architecture design failed: {e}")
            return AgentResult(
                success=False,
                output=output,
                evidence=evidence,
                artifacts=artifacts,
                error=str(e)
            )

    def _build_architecture_prompt(
        self,
        requirements: str,
        project_type: str,
        constraints: Dict[str, Any]
    ) -> str:
        """Build prompt for architecture generation"""
        prompt = f"""# Architecture Design Task

## Product Requirements
{requirements}

## Project Type
{project_type}

## Constraints
{json.dumps(constraints, indent=2)}

## Your Task
Design a comprehensive system architecture that addresses these requirements. You should:

1. **Create at least 2-3 ADRs** covering major architectural decisions:
   - Overall architecture pattern (monolith vs microservices, etc.)
   - Technology stack choices
   - Data storage strategy
   - Any other significant decisions

2. **Create diagrams** to visualize the architecture:
   - C4 Context diagram (system in its environment)
   - C4 Container diagram (high-level technology choices)
   - Sequence diagrams for key workflows
   - ER diagram for data model

3. **Define API boundaries** between major components

4. **Specify non-functional requirements**:
   - Performance SLOs
   - Security requirements
   - Scalability targets
   - Monitoring strategy

5. **Provide implementation guidance**:
   - Suggested tech stack
   - Migration/rollback strategy
   - Development phases

Use the tools provided to create ADRs, diagrams, and API contracts. Provide a comprehensive architecture document as your main response."""

        return prompt

    def _create_adr_file(
        self,
        project_path: str,
        adr_data: Dict[str, Any]
    ) -> str:
        """Create ADR file"""
        # Create ADR directory
        adr_dir = Path(project_path) / "docs" / "architecture" / "decisions"
        adr_dir.mkdir(parents=True, exist_ok=True)

        # Generate ADR number
        existing_adrs = list(adr_dir.glob("*.md"))
        adr_num = len(existing_adrs) + 1

        # Create ADR filename
        title_slug = adr_data["title"].lower().replace(" ", "-")
        filename = f"{adr_num:04d}-{title_slug}.md"
        filepath = adr_dir / filename

        # Generate ADR content
        content = f"""# {adr_num}. {adr_data['title']}

Date: {datetime.now().strftime('%Y-%m-%d')}

## Status

Proposed

## Context

{adr_data['context']}

## Decision

{adr_data['decision']}

## Consequences

{adr_data['consequences']}

## Alternatives Considered

{self._format_alternatives(adr_data.get('alternatives', []))}

---

*This ADR was generated by the Chief Architect agent.*
"""

        # Write file
        filepath.write_text(content)

        return str(filepath)

    def _create_diagram_file(
        self,
        project_path: str,
        diagram_data: Dict[str, Any]
    ) -> str:
        """Create diagram file"""
        # Create diagrams directory
        diagrams_dir = Path(project_path) / "docs" / "architecture" / "diagrams"
        diagrams_dir.mkdir(parents=True, exist_ok=True)

        # Create filename
        title_slug = diagram_data["title"].lower().replace(" ", "-")
        diagram_type = diagram_data["diagram_type"]
        filename = f"{diagram_type}-{title_slug}.md"
        filepath = diagrams_dir / filename

        # Generate diagram content
        content = f"""# {diagram_data['title']}

Type: {diagram_type.upper()}

```mermaid
{diagram_data['mermaid_code']}
```

---

*Generated by Chief Architect agent on {datetime.now().strftime('%Y-%m-%d')}*
"""

        # Write file
        filepath.write_text(content)

        return str(filepath)

    def _create_api_contract_file(
        self,
        project_path: str,
        contract_data: Dict[str, Any]
    ) -> str:
        """Create API contract file"""
        # Create contracts directory
        contracts_dir = Path(project_path) / "docs" / "architecture" / "contracts"
        contracts_dir.mkdir(parents=True, exist_ok=True)

        # Create filename
        service_name = contract_data["service_name"]
        filename = f"{service_name.lower().replace(' ', '-')}-api.json"
        filepath = contracts_dir / filename

        # Add metadata
        contract_data["generated_at"] = datetime.now().isoformat()
        contract_data["generated_by"] = "chief_architect_agent"

        # Write file
        filepath.write_text(json.dumps(contract_data, indent=2))

        return str(filepath)

    def _format_alternatives(self, alternatives: List[str]) -> str:
        """Format alternatives list"""
        if not alternatives:
            return "No alternatives were documented."

        formatted = []
        for i, alt in enumerate(alternatives, 1):
            formatted.append(f"{i}. {alt}")

        return "\n".join(formatted)
