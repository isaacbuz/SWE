"""
Technical Debt Tracker Agent

Scans codebase for code smells, prioritizes refactoring opportunities,
estimates effort, creates tech debt issues, and tracks debt trends.
"""
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import re
import os

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from base import BaseAgent, Task, Context, AgentResult, TaskType, Priority
from protocol import Evidence


class DebtSeverity(str, Enum):
    """Technical debt severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DebtCategory(str, Enum):
    """Technical debt categories"""
    CODE_SMELL = "code_smell"
    DUPLICATION = "duplication"
    COMPLEXITY = "complexity"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    DEPRECATED = "deprecated"
    TODO_FIXME = "todo_fixme"


@dataclass
class TechDebtItem:
    """Individual technical debt item"""
    id: str
    category: DebtCategory
    severity: DebtSeverity
    description: str
    file_path: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    estimated_effort_hours: float = 0.0
    impact_score: float = 0.0  # 0-10
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RefactoringOpportunity:
    """Refactoring opportunity"""
    id: str
    title: str
    description: str
    affected_files: List[str]
    debt_items: List[str]  # IDs of related debt items
    priority: Priority
    estimated_effort_hours: float
    expected_benefits: List[str]
    risks: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class TechDebtTracker(BaseAgent):
    """
    Technical Debt Tracker for code quality management

    Features:
    - Code smell detection
    - Duplication analysis
    - Complexity metrics
    - TODO/FIXME tracking
    - Debt prioritization
    - Trend analysis
    - Refactoring recommendations
    """

    def __init__(
        self,
        agent_id: str = "tech_debt_tracker",
        complexity_threshold: int = 15,
        duplication_threshold: int = 50,
        scan_interval_hours: int = 24,
        **kwargs
    ):
        """
        Initialize tech debt tracker

        Args:
            agent_id: Agent identifier
            complexity_threshold: Cyclomatic complexity threshold
            duplication_threshold: Lines of duplication threshold
            scan_interval_hours: How often to scan
            **kwargs: Additional BaseAgent arguments
        """
        super().__init__(
            agent_id=agent_id,
            task_type=TaskType.REFACTORING,
            **kwargs
        )

        self.complexity_threshold = complexity_threshold
        self.duplication_threshold = duplication_threshold
        self.scan_interval_hours = scan_interval_hours

        # Debt tracking
        self.debt_items: Dict[str, TechDebtItem] = {}
        self.refactoring_opportunities: Dict[str, RefactoringOpportunity] = {}
        self.scan_history: List[Dict[str, Any]] = []

        self.logger = logging.getLogger(f"Agent.{agent_id}")

    def get_system_prompt(self) -> str:
        """Get system prompt"""
        return """You are a Technical Debt Tracker agent responsible for identifying,
analyzing, and prioritizing technical debt in codebases.

Your responsibilities:
1. Scan codebases for code smells and quality issues
2. Identify duplication and high complexity
3. Detect security and performance issues
4. Track TODO/FIXME comments
5. Prioritize refactoring opportunities
6. Estimate remediation effort
7. Track debt trends over time

When analyzing code:
- Use established code quality metrics
- Consider maintainability, readability, and testability
- Evaluate impact on development velocity
- Balance debt remediation with feature development
- Recommend incremental improvements

Provide analysis in JSON format:
{
  "debt_items": [
    {
      "category": "code_smell|duplication|complexity|etc",
      "severity": "critical|high|medium|low",
      "description": "detailed description",
      "file_path": "path/to/file",
      "line_number": 42,
      "estimated_effort_hours": 2.5,
      "impact_score": 7.5
    }
  ],
  "refactoring_opportunities": [
    {
      "title": "refactoring title",
      "description": "detailed description",
      "affected_files": ["file1", "file2"],
      "priority": "high|medium|low",
      "estimated_effort_hours": 8.0,
      "expected_benefits": ["benefit 1", "benefit 2"]
    }
  ],
  "metrics": {
    "total_debt_items": 15,
    "critical_items": 2,
    "total_estimated_hours": 40.0,
    "debt_trend": "increasing|stable|decreasing"
  }
}"""

    async def execute(self, task: Task, context: Context) -> AgentResult:
        """
        Execute technical debt analysis

        Args:
            task: Task specifying scan parameters
            context: Execution context

        Returns:
            Analysis results
        """
        try:
            project_path = context.project_path

            # Scan for technical debt
            self.logger.info(f"Scanning {project_path} for technical debt")

            # Step 1: Scan for code smells
            code_smells = await self._scan_code_smells(project_path, context)

            # Step 2: Detect duplication
            duplications = await self._detect_duplications(project_path, context)

            # Step 3: Analyze complexity
            complex_code = await self._analyze_complexity(project_path, context)

            # Step 4: Find TODO/FIXME
            todos = await self._find_todos_fixmes(project_path, context)

            # Step 5: Check for deprecated code
            deprecated = await self._find_deprecated_code(project_path, context)

            # Combine all debt items
            all_debt = (
                code_smells + duplications + complex_code +
                todos + deprecated
            )

            # Store debt items
            for item in all_debt:
                self.debt_items[item.id] = item

            # Step 6: Identify refactoring opportunities
            opportunities = await self._identify_refactoring_opportunities(
                all_debt,
                context
            )

            # Store opportunities
            for opp in opportunities:
                self.refactoring_opportunities[opp.id] = opp

            # Step 7: Analyze trends
            trends = self._analyze_trends()

            # Step 8: Create prioritized action plan
            action_plan = self._create_action_plan(all_debt, opportunities)

            # Record scan
            scan_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "total_items": len(all_debt),
                "by_severity": self._count_by_severity(all_debt),
                "by_category": self._count_by_category(all_debt),
                "total_estimated_hours": sum(item.estimated_effort_hours for item in all_debt)
            }
            self.scan_history.append(scan_record)

            evidence = [
                self.create_evidence(
                    "tech_debt_scan",
                    f"Scanned codebase, found {len(all_debt)} debt items"
                )
            ]

            return AgentResult(
                success=True,
                output={
                    "debt_items": [self._debt_to_dict(item) for item in all_debt],
                    "refactoring_opportunities": [
                        self._opportunity_to_dict(opp) for opp in opportunities
                    ],
                    "metrics": {
                        "total_debt_items": len(all_debt),
                        "critical_items": sum(1 for i in all_debt if i.severity == DebtSeverity.CRITICAL),
                        "high_items": sum(1 for i in all_debt if i.severity == DebtSeverity.HIGH),
                        "total_estimated_hours": sum(i.estimated_effort_hours for i in all_debt),
                        "by_category": self._count_by_category(all_debt),
                        "by_severity": self._count_by_severity(all_debt)
                    },
                    "trends": trends,
                    "action_plan": action_plan
                },
                evidence=evidence,
                metadata={
                    "scanned_path": project_path,
                    "scan_timestamp": datetime.utcnow().isoformat()
                }
            )

        except Exception as e:
            self.logger.error(f"Tech debt tracking failed: {e}")
            return AgentResult(
                success=False,
                output={},
                evidence=[],
                error=str(e)
            )

    async def _scan_code_smells(
        self,
        project_path: str,
        context: Context
    ) -> List[TechDebtItem]:
        """Scan for code smells"""
        debt_items = []

        # Common code smell patterns
        patterns = {
            "long_method": (r"def\s+\w+\([^)]*\):(?:\n\s+[^\n]+){30,}", "Function exceeds 30 lines"),
            "long_parameter_list": (r"def\s+\w+\([^)]*,[^)]*,[^)]*,[^)]*,[^)]*,[^)]*\)", "Function has too many parameters"),
            "deep_nesting": (r"(\s{4,}){4,}if\s+", "Deep nesting level"),
            "magic_numbers": (r"\b(?<!\.)\d{2,}\b(?!\.)", "Magic number in code"),
        }

        try:
            for root, dirs, files in os.walk(project_path):
                # Skip common non-source directories
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.venv', 'venv']]

                for file in files:
                    if not (file.endswith('.py') or file.endswith('.js') or file.endswith('.ts')):
                        continue

                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        for smell_type, (pattern, description) in patterns.items():
                            matches = re.finditer(pattern, content)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1

                                debt_items.append(TechDebtItem(
                                    id=f"smell_{smell_type}_{file_path}_{line_num}",
                                    category=DebtCategory.CODE_SMELL,
                                    severity=DebtSeverity.MEDIUM,
                                    description=f"{description} in {file}",
                                    file_path=file_path,
                                    line_number=line_num,
                                    estimated_effort_hours=0.5,
                                    impact_score=5.0,
                                    metadata={"smell_type": smell_type}
                                ))
                    except Exception as e:
                        self.logger.warning(f"Error scanning {file_path}: {e}")

        except Exception as e:
            self.logger.error(f"Code smell scan failed: {e}")

        return debt_items

    async def _detect_duplications(
        self,
        project_path: str,
        context: Context
    ) -> List[TechDebtItem]:
        """Detect code duplication"""
        # Simplified duplication detection
        # In production, use tools like pylint, flake8, or dedicated duplication detectors
        debt_items = []

        # TODO: Implement more sophisticated duplication detection
        # For now, just a placeholder

        return debt_items

    async def _analyze_complexity(
        self,
        project_path: str,
        context: Context
    ) -> List[TechDebtItem]:
        """Analyze code complexity"""
        debt_items = []

        # Simplified complexity analysis
        # In production, use radon, mccabe, or similar tools

        try:
            for root, dirs, files in os.walk(project_path):
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.venv', 'venv']]

                for file in files:
                    if not file.endswith('.py'):
                        continue

                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Count nested blocks as simple complexity metric
                        functions = re.finditer(r"def\s+(\w+)\([^)]*\):(.*?)(?=\ndef\s|\Z)", content, re.DOTALL)
                        for func_match in functions:
                            func_name = func_match.group(1)
                            func_body = func_match.group(2)

                            # Count control structures
                            complexity = (
                                func_body.count("if ") +
                                func_body.count("for ") +
                                func_body.count("while ") +
                                func_body.count("except ") +
                                func_body.count("and ") +
                                func_body.count("or ")
                            )

                            if complexity > self.complexity_threshold:
                                line_num = content[:func_match.start()].count('\n') + 1

                                debt_items.append(TechDebtItem(
                                    id=f"complexity_{file_path}_{func_name}",
                                    category=DebtCategory.COMPLEXITY,
                                    severity=DebtSeverity.HIGH if complexity > 20 else DebtSeverity.MEDIUM,
                                    description=f"High complexity in function {func_name} (score: {complexity})",
                                    file_path=file_path,
                                    line_number=line_num,
                                    estimated_effort_hours=complexity / 10,
                                    impact_score=min(10, complexity / 2),
                                    metadata={"complexity_score": complexity, "function_name": func_name}
                                ))
                    except Exception as e:
                        self.logger.warning(f"Error analyzing {file_path}: {e}")

        except Exception as e:
            self.logger.error(f"Complexity analysis failed: {e}")

        return debt_items

    async def _find_todos_fixmes(
        self,
        project_path: str,
        context: Context
    ) -> List[TechDebtItem]:
        """Find TODO and FIXME comments"""
        debt_items = []

        patterns = [
            (r"#\s*TODO:?\s*(.+)", "TODO"),
            (r"#\s*FIXME:?\s*(.+)", "FIXME"),
            (r"#\s*HACK:?\s*(.+)", "HACK"),
            (r"//\s*TODO:?\s*(.+)", "TODO"),
            (r"//\s*FIXME:?\s*(.+)", "FIXME"),
        ]

        try:
            for root, dirs, files in os.walk(project_path):
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.venv', 'venv']]

                for file in files:
                    if not (file.endswith('.py') or file.endswith('.js') or file.endswith('.ts')):
                        continue

                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        for pattern, marker_type in patterns:
                            matches = re.finditer(pattern, content)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                comment = match.group(1).strip()

                                severity = DebtSeverity.HIGH if marker_type == "FIXME" else DebtSeverity.MEDIUM

                                debt_items.append(TechDebtItem(
                                    id=f"todo_{file_path}_{line_num}",
                                    category=DebtCategory.TODO_FIXME,
                                    severity=severity,
                                    description=f"{marker_type}: {comment}",
                                    file_path=file_path,
                                    line_number=line_num,
                                    estimated_effort_hours=1.0 if marker_type == "FIXME" else 0.5,
                                    impact_score=7.0 if marker_type == "FIXME" else 4.0,
                                    metadata={"marker_type": marker_type, "comment": comment}
                                ))
                    except Exception as e:
                        self.logger.warning(f"Error scanning {file_path}: {e}")

        except Exception as e:
            self.logger.error(f"TODO/FIXME scan failed: {e}")

        return debt_items

    async def _find_deprecated_code(
        self,
        project_path: str,
        context: Context
    ) -> List[TechDebtItem]:
        """Find deprecated code"""
        debt_items = []

        # Look for deprecation markers
        patterns = [
            r"@deprecated",
            r"# deprecated",
            r"// deprecated",
        ]

        # TODO: Implement deprecated code detection

        return debt_items

    async def _identify_refactoring_opportunities(
        self,
        debt_items: List[TechDebtItem],
        context: Context
    ) -> List[RefactoringOpportunity]:
        """Identify refactoring opportunities"""
        opportunities = []

        # Group debt items by file
        by_file: Dict[str, List[TechDebtItem]] = {}
        for item in debt_items:
            if item.file_path not in by_file:
                by_file[item.file_path] = []
            by_file[item.file_path].append(item)

        # Identify files with multiple issues
        for file_path, items in by_file.items():
            if len(items) >= 3:
                total_effort = sum(item.estimated_effort_hours for item in items)
                avg_impact = sum(item.impact_score for item in items) / len(items)

                opportunities.append(RefactoringOpportunity(
                    id=f"refactor_{file_path}",
                    title=f"Refactor {os.path.basename(file_path)}",
                    description=f"File has {len(items)} technical debt items",
                    affected_files=[file_path],
                    debt_items=[item.id for item in items],
                    priority=Priority.HIGH if avg_impact > 7 else Priority.MEDIUM,
                    estimated_effort_hours=total_effort,
                    expected_benefits=[
                        "Improved code quality",
                        "Reduced complexity",
                        "Better maintainability"
                    ],
                    risks=["May require extensive testing"]
                ))

        return opportunities

    def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze tech debt trends"""
        if len(self.scan_history) < 2:
            return {"trend": "insufficient_data", "scans": len(self.scan_history)}

        latest = self.scan_history[-1]
        previous = self.scan_history[-2]

        change = latest["total_items"] - previous["total_items"]
        percent_change = (change / previous["total_items"] * 100) if previous["total_items"] > 0 else 0

        if percent_change > 10:
            trend = "increasing"
        elif percent_change < -10:
            trend = "decreasing"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "current_items": latest["total_items"],
            "previous_items": previous["total_items"],
            "change": change,
            "percent_change": percent_change,
            "scans_analyzed": len(self.scan_history)
        }

    def _create_action_plan(
        self,
        debt_items: List[TechDebtItem],
        opportunities: List[RefactoringOpportunity]
    ) -> Dict[str, Any]:
        """Create prioritized action plan"""
        # Prioritize critical items
        critical = [item for item in debt_items if item.severity == DebtSeverity.CRITICAL]
        high = [item for item in debt_items if item.severity == DebtSeverity.HIGH]

        # Sort opportunities by priority and ROI
        sorted_opps = sorted(
            opportunities,
            key=lambda o: (
                o.priority.value,
                -o.estimated_effort_hours,
                -len(o.debt_items)
            )
        )

        return {
            "immediate_actions": [
                {
                    "type": "fix_critical",
                    "description": f"Address {len(critical)} critical debt items",
                    "estimated_hours": sum(i.estimated_effort_hours for i in critical)
                }
            ] if critical else [],
            "short_term_actions": [
                {
                    "type": "fix_high_priority",
                    "description": f"Address {len(high)} high priority debt items",
                    "estimated_hours": sum(i.estimated_effort_hours for i in high)
                }
            ] if high else [],
            "refactoring_opportunities": [
                {
                    "title": opp.title,
                    "priority": opp.priority.value,
                    "estimated_hours": opp.estimated_effort_hours
                }
                for opp in sorted_opps[:5]  # Top 5
            ],
            "total_estimated_effort_hours": sum(i.estimated_effort_hours for i in debt_items)
        }

    def _count_by_severity(self, items: List[TechDebtItem]) -> Dict[str, int]:
        """Count items by severity"""
        counts = {severity.value: 0 for severity in DebtSeverity}
        for item in items:
            counts[item.severity.value] += 1
        return counts

    def _count_by_category(self, items: List[TechDebtItem]) -> Dict[str, int]:
        """Count items by category"""
        counts = {}
        for item in items:
            counts[item.category.value] = counts.get(item.category.value, 0) + 1
        return counts

    def _debt_to_dict(self, item: TechDebtItem) -> Dict[str, Any]:
        """Convert debt item to dictionary"""
        return {
            "id": item.id,
            "category": item.category.value,
            "severity": item.severity.value,
            "description": item.description,
            "file_path": item.file_path,
            "line_number": item.line_number,
            "estimated_effort_hours": item.estimated_effort_hours,
            "impact_score": item.impact_score
        }

    def _opportunity_to_dict(self, opp: RefactoringOpportunity) -> Dict[str, Any]:
        """Convert opportunity to dictionary"""
        return {
            "id": opp.id,
            "title": opp.title,
            "description": opp.description,
            "affected_files": opp.affected_files,
            "priority": opp.priority.value,
            "estimated_effort_hours": opp.estimated_effort_hours,
            "expected_benefits": opp.expected_benefits,
            "risks": opp.risks
        }
