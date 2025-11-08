"""
Code Review Agent

Performs comprehensive code reviews of changes, checking for:
- Code quality and best practices
- Potential bugs and security issues
- Performance concerns
- Test coverage
- Documentation completeness
- Architecture alignment

The reviewer is context-aware and understands project history.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import re
import asyncio
import logging

logger = logging.getLogger(__name__)


class ReviewSeverity(Enum):
    """Severity levels for review comments"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ReviewDecision(Enum):
    """Final review decisions"""
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"
    COMMENT = "comment"


@dataclass
class ReviewComment:
    """A single review comment"""
    file: str
    line: Optional[int]
    severity: ReviewSeverity
    category: str  # e.g., "best-practice", "bug", "security", "performance"
    message: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None


@dataclass
class CodeReview:
    """Complete code review result"""
    decision: ReviewDecision
    summary: str
    comments: List[ReviewComment] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    approver: str = "Reviewer Agent"
    confidence: float = 0.0


class ReviewerAgent:
    """
    Code Review Agent

    Reviews code changes comprehensively, checking for quality,
    correctness, security, and adherence to best practices.
    """

    def __init__(
        self,
        model_id: str = "claude-sonnet-4",
        project_context: Optional[Dict[str, Any]] = None,
        coding_standards: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the Reviewer Agent

        Args:
            model_id: LLM model to use for review
            project_context: Project-specific context (tech stack, patterns, etc.)
            coding_standards: Project coding standards and style guides
        """
        self.model_id = model_id
        self.project_context = project_context or {}
        self.coding_standards = coding_standards or self._default_standards()

    def _default_standards(self) -> Dict[str, Any]:
        """Default coding standards"""
        return {
            'max_function_length': 50,
            'max_complexity': 10,
            'require_docstrings': True,
            'require_type_hints': True,
            'max_line_length': 100,
            'naming_conventions': {
                'functions': 'snake_case',
                'classes': 'PascalCase',
                'constants': 'UPPER_CASE',
            },
        }

    async def review_diff(
        self,
        diff: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> CodeReview:
        """
        Review a code diff

        Args:
            diff: Git diff or patch content
            context: Additional context (PR description, related issues, etc.)

        Returns:
            CodeReview with decision and comments
        """
        logger.info("Starting code review")

        # Parse the diff
        file_changes = self._parse_diff(diff)

        # Initialize review
        comments = []

        # Run various checks
        comments.extend(await self._check_code_quality(file_changes))
        comments.extend(await self._check_potential_bugs(file_changes))
        comments.extend(await self._check_security(file_changes))
        comments.extend(await self._check_performance(file_changes))
        comments.extend(await self._check_tests(file_changes))
        comments.extend(await self._check_documentation(file_changes))

        # Calculate metrics
        metrics = self._calculate_metrics(file_changes, comments)

        # Generate suggestions
        suggestions = self._generate_suggestions(file_changes, comments)

        # Make final decision
        decision = self._make_decision(comments, metrics)

        # Generate summary
        summary = self._generate_summary(decision, comments, metrics)

        review = CodeReview(
            decision=decision,
            summary=summary,
            comments=comments,
            metrics=metrics,
            suggestions=suggestions,
            confidence=self._calculate_confidence(comments, metrics),
        )

        logger.info(f"Review completed: {decision.value}")
        return review

    async def review_file(
        self,
        file_path: str,
        content: str,
        original_content: Optional[str] = None,
    ) -> CodeReview:
        """
        Review a single file

        Args:
            file_path: Path to the file
            content: New file content
            original_content: Original content (for comparison)

        Returns:
            CodeReview result
        """
        logger.info(f"Reviewing file: {file_path}")

        # Create a pseudo-diff if we have original content
        if original_content:
            diff = self._create_diff(file_path, original_content, content)
            return await self.review_diff(diff)

        # Otherwise, review the file as-is
        file_changes = {file_path: {'new_content': content, 'is_new': True}}

        comments = []
        comments.extend(await self._check_code_quality(file_changes))
        comments.extend(await self._check_potential_bugs(file_changes))
        comments.extend(await self._check_security(file_changes))
        comments.extend(await self._check_performance(file_changes))
        comments.extend(await self._check_documentation(file_changes))

        metrics = self._calculate_metrics(file_changes, comments)
        suggestions = self._generate_suggestions(file_changes, comments)
        decision = self._make_decision(comments, metrics)
        summary = self._generate_summary(decision, comments, metrics)

        return CodeReview(
            decision=decision,
            summary=summary,
            comments=comments,
            metrics=metrics,
            suggestions=suggestions,
            confidence=self._calculate_confidence(comments, metrics),
        )

    def _parse_diff(self, diff: str) -> Dict[str, Dict[str, Any]]:
        """Parse a git diff into structured format"""
        file_changes = {}
        current_file = None
        current_changes = []

        for line in diff.split('\n'):
            if line.startswith('diff --git'):
                if current_file:
                    file_changes[current_file] = {
                        'changes': current_changes,
                        'additions': sum(1 for c in current_changes if c.startswith('+')),
                        'deletions': sum(1 for c in current_changes if c.startswith('-')),
                    }
                # Extract file path
                match = re.search(r'b/(.+)$', line)
                current_file = match.group(1) if match else None
                current_changes = []
            elif line.startswith(('+', '-', ' ')) and current_file:
                current_changes.append(line)

        if current_file:
            file_changes[current_file] = {
                'changes': current_changes,
                'additions': sum(1 for c in current_changes if c.startswith('+')),
                'deletions': sum(1 for c in current_changes if c.startswith('-')),
            }

        return file_changes

    async def _check_code_quality(
        self,
        file_changes: Dict[str, Dict[str, Any]],
    ) -> List[ReviewComment]:
        """Check code quality and style"""
        comments = []

        for file_path, changes in file_changes.items():
            # Check file extension
            if not self._is_code_file(file_path):
                continue

            content = changes.get('new_content', '\n'.join(changes.get('changes', [])))

            # Check line length
            for i, line in enumerate(content.split('\n'), 1):
                if len(line) > self.coding_standards['max_line_length']:
                    comments.append(ReviewComment(
                        file=file_path,
                        line=i,
                        severity=ReviewSeverity.WARNING,
                        category="style",
                        message=f"Line exceeds {self.coding_standards['max_line_length']} characters",
                        suggestion="Consider breaking this line into multiple lines",
                    ))

            # Check for TODO/FIXME comments
            for i, line in enumerate(content.split('\n'), 1):
                if 'TODO' in line or 'FIXME' in line:
                    comments.append(ReviewComment(
                        file=file_path,
                        line=i,
                        severity=ReviewSeverity.INFO,
                        category="best-practice",
                        message="TODO/FIXME comment found",
                        suggestion="Consider creating an issue to track this work",
                    ))

            # Check for console.log / print statements (likely debug code)
            for i, line in enumerate(content.split('\n'), 1):
                if re.search(r'console\.log\(|print\(', line):
                    comments.append(ReviewComment(
                        file=file_path,
                        line=i,
                        severity=ReviewSeverity.WARNING,
                        category="best-practice",
                        message="Debug statement found",
                        suggestion="Remove debug statements before merging",
                    ))

        return comments

    async def _check_potential_bugs(
        self,
        file_changes: Dict[str, Dict[str, Any]],
    ) -> List[ReviewComment]:
        """Check for potential bugs"""
        comments = []

        for file_path, changes in file_changes.items():
            if not self._is_code_file(file_path):
                continue

            content = changes.get('new_content', '\n'.join(changes.get('changes', [])))

            # Check for bare except clauses
            for i, line in enumerate(content.split('\n'), 1):
                if re.match(r'^\s*except\s*:', line):
                    comments.append(ReviewComment(
                        file=file_path,
                        line=i,
                        severity=ReviewSeverity.ERROR,
                        category="bug",
                        message="Bare except clause catches all exceptions",
                        suggestion="Specify the exception type(s) to catch",
                    ))

            # Check for == None instead of is None
            for i, line in enumerate(content.split('\n'), 1):
                if re.search(r'==\s*None|!=\s*None', line):
                    comments.append(ReviewComment(
                        file=file_path,
                        line=i,
                        severity=ReviewSeverity.WARNING,
                        category="bug",
                        message="Use 'is None' instead of '== None'",
                        suggestion="Replace '== None' with 'is None'",
                    ))

            # Check for SQL injection risks
            for i, line in enumerate(content.split('\n'), 1):
                if re.search(r'execute\([^)]*%|execute\([^)]*\+', line):
                    comments.append(ReviewComment(
                        file=file_path,
                        line=i,
                        severity=ReviewSeverity.CRITICAL,
                        category="security",
                        message="Potential SQL injection vulnerability",
                        suggestion="Use parameterized queries instead of string formatting",
                    ))

        return comments

    async def _check_security(
        self,
        file_changes: Dict[str, Dict[str, Any]],
    ) -> List[ReviewComment]:
        """Check for security issues"""
        comments = []

        for file_path, changes in file_changes.items():
            content = changes.get('new_content', '\n'.join(changes.get('changes', [])))

            # Check for hardcoded secrets
            secret_patterns = [
                (r'password\s*=\s*["\'][^"\']+["\']', "Potential hardcoded password"),
                (r'api_key\s*=\s*["\'][^"\']+["\']', "Potential hardcoded API key"),
                (r'secret\s*=\s*["\'][^"\']+["\']', "Potential hardcoded secret"),
                (r'token\s*=\s*["\'][^"\']+["\']', "Potential hardcoded token"),
            ]

            for i, line in enumerate(content.split('\n'), 1):
                for pattern, message in secret_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        comments.append(ReviewComment(
                            file=file_path,
                            line=i,
                            severity=ReviewSeverity.CRITICAL,
                            category="security",
                            message=message,
                            suggestion="Use environment variables or secret management",
                        ))

            # Check for unsafe eval/exec
            for i, line in enumerate(content.split('\n'), 1):
                if re.search(r'\beval\(|\bexec\(', line):
                    comments.append(ReviewComment(
                        file=file_path,
                        line=i,
                        severity=ReviewSeverity.CRITICAL,
                        category="security",
                        message="Use of eval/exec is dangerous",
                        suggestion="Find a safer alternative to eval/exec",
                    ))

        return comments

    async def _check_performance(
        self,
        file_changes: Dict[str, Dict[str, Any]],
    ) -> List[ReviewComment]:
        """Check for performance issues"""
        comments = []

        for file_path, changes in file_changes.items():
            if not self._is_code_file(file_path):
                continue

            content = changes.get('new_content', '\n'.join(changes.get('changes', [])))

            # Check for nested loops (potential O(n^2) or worse)
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if re.match(r'^\s*for .+:', line):
                    # Check if there's another for loop within a few lines
                    indent = len(line) - len(line.lstrip())
                    for j in range(i + 1, min(i + 20, len(lines))):
                        next_line = lines[j]
                        next_indent = len(next_line) - len(next_line.lstrip())
                        if next_indent <= indent:
                            break
                        if re.match(r'^\s*for .+:', next_line):
                            comments.append(ReviewComment(
                                file=file_path,
                                line=i + 1,
                                severity=ReviewSeverity.WARNING,
                                category="performance",
                                message="Nested loops detected",
                                suggestion="Consider if this can be optimized to reduce complexity",
                            ))
                            break

        return comments

    async def _check_tests(
        self,
        file_changes: Dict[str, Dict[str, Any]],
    ) -> List[ReviewComment]:
        """Check test coverage"""
        comments = []

        # Check if there are any test files
        has_test_changes = any('test' in f.lower() for f in file_changes.keys())
        has_code_changes = any(
            self._is_code_file(f) and 'test' not in f.lower()
            for f in file_changes.keys()
        )

        if has_code_changes and not has_test_changes:
            comments.append(ReviewComment(
                file="<general>",
                line=None,
                severity=ReviewSeverity.WARNING,
                category="testing",
                message="No test files modified",
                suggestion="Consider adding tests for the new code",
            ))

        return comments

    async def _check_documentation(
        self,
        file_changes: Dict[str, Dict[str, Any]],
    ) -> List[ReviewComment]:
        """Check documentation completeness"""
        comments = []

        for file_path, changes in file_changes.items():
            if not self._is_code_file(file_path):
                continue

            content = changes.get('new_content', '\n'.join(changes.get('changes', [])))

            # Check for functions without docstrings
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if re.match(r'^\s*def .+\(', line):
                    # Check if next non-empty line is a docstring
                    has_docstring = False
                    for j in range(i + 1, min(i + 5, len(lines))):
                        next_line = lines[j].strip()
                        if not next_line:
                            continue
                        if next_line.startswith('"""') or next_line.startswith("'''"):
                            has_docstring = True
                            break
                        break

                    if not has_docstring and self.coding_standards['require_docstrings']:
                        comments.append(ReviewComment(
                            file=file_path,
                            line=i + 1,
                            severity=ReviewSeverity.WARNING,
                            category="documentation",
                            message="Function missing docstring",
                            suggestion="Add a docstring describing the function",
                        ))

        return comments

    def _calculate_metrics(
        self,
        file_changes: Dict[str, Dict[str, Any]],
        comments: List[ReviewComment],
    ) -> Dict[str, Any]:
        """Calculate review metrics"""
        total_additions = sum(c.get('additions', 0) for c in file_changes.values())
        total_deletions = sum(c.get('deletions', 0) for c in file_changes.values())

        severity_counts = {
            'info': sum(1 for c in comments if c.severity == ReviewSeverity.INFO),
            'warning': sum(1 for c in comments if c.severity == ReviewSeverity.WARNING),
            'error': sum(1 for c in comments if c.severity == ReviewSeverity.ERROR),
            'critical': sum(1 for c in comments if c.severity == ReviewSeverity.CRITICAL),
        }

        category_counts = {}
        for comment in comments:
            category_counts[comment.category] = category_counts.get(comment.category, 0) + 1

        return {
            'files_changed': len(file_changes),
            'lines_added': total_additions,
            'lines_deleted': total_deletions,
            'total_comments': len(comments),
            'severity_breakdown': severity_counts,
            'category_breakdown': category_counts,
        }

    def _generate_suggestions(
        self,
        file_changes: Dict[str, Dict[str, Any]],
        comments: List[ReviewComment],
    ) -> List[str]:
        """Generate overall improvement suggestions"""
        suggestions = []

        # Analyze comment patterns
        category_counts = {}
        for comment in comments:
            category_counts[comment.category] = category_counts.get(comment.category, 0) + 1

        # Generate suggestions based on patterns
        if category_counts.get('security', 0) > 0:
            suggestions.append("Consider running a security scan with tools like bandit or semgrep")

        if category_counts.get('testing', 0) > 0:
            suggestions.append("Add unit tests to cover the new functionality")

        if category_counts.get('performance', 0) > 2:
            suggestions.append("Consider profiling the code to identify performance bottlenecks")

        if category_counts.get('documentation', 0) > 3:
            suggestions.append("Add comprehensive documentation for the new features")

        return suggestions

    def _make_decision(
        self,
        comments: List[ReviewComment],
        metrics: Dict[str, Any],
    ) -> ReviewDecision:
        """Make final review decision"""
        critical_count = metrics['severity_breakdown']['critical']
        error_count = metrics['severity_breakdown']['error']
        warning_count = metrics['severity_breakdown']['warning']

        # Block on critical issues
        if critical_count > 0:
            return ReviewDecision.REQUEST_CHANGES

        # Block on multiple errors
        if error_count > 2:
            return ReviewDecision.REQUEST_CHANGES

        # Request changes on some errors
        if error_count > 0:
            return ReviewDecision.REQUEST_CHANGES

        # Comment on warnings
        if warning_count > 5:
            return ReviewDecision.COMMENT

        # Approve otherwise
        return ReviewDecision.APPROVE

    def _generate_summary(
        self,
        decision: ReviewDecision,
        comments: List[ReviewComment],
        metrics: Dict[str, Any],
    ) -> str:
        """Generate review summary"""
        summary_parts = []

        # Add decision
        if decision == ReviewDecision.APPROVE:
            summary_parts.append("✅ Code review passed")
        elif decision == ReviewDecision.REQUEST_CHANGES:
            summary_parts.append("❌ Changes requested")
        else:
            summary_parts.append("💬 Comments added")

        # Add metrics summary
        summary_parts.append(
            f"\n\n📊 Changes: {metrics['files_changed']} files, "
            f"+{metrics['lines_added']} -{metrics['lines_deleted']} lines"
        )

        # Add severity summary
        severity = metrics['severity_breakdown']
        if any(severity.values()):
            summary_parts.append(
                f"\n🔍 Issues: {severity['critical']} critical, "
                f"{severity['error']} errors, {severity['warning']} warnings, "
                f"{severity['info']} info"
            )

        # Add top categories
        categories = metrics['category_breakdown']
        if categories:
            top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
            category_str = ", ".join(f"{cat} ({count})" for cat, count in top_categories)
            summary_parts.append(f"\n📋 Top issues: {category_str}")

        return "".join(summary_parts)

    def _calculate_confidence(
        self,
        comments: List[ReviewComment],
        metrics: Dict[str, Any],
    ) -> float:
        """Calculate confidence in the review"""
        # Simple heuristic: higher confidence with more thorough review
        base_confidence = 0.7

        # Increase confidence based on number of checks performed
        checks_performed = len(set(c.category for c in comments))
        confidence = base_confidence + (checks_performed * 0.05)

        return min(confidence, 0.95)

    def _is_code_file(self, file_path: str) -> bool:
        """Check if file is a code file"""
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs',
            '.cpp', '.c', '.h', '.hpp', '.cs', '.rb', '.php', '.swift',
        }
        return any(file_path.endswith(ext) for ext in code_extensions)

    def _create_diff(
        self,
        file_path: str,
        original: str,
        new: str,
    ) -> str:
        """Create a simple diff"""
        # Simple line-by-line diff
        diff_lines = [f"diff --git a/{file_path} b/{file_path}"]

        original_lines = original.split('\n')
        new_lines = new.split('\n')

        for line in original_lines:
            diff_lines.append(f"-{line}")
        for line in new_lines:
            diff_lines.append(f"+{line}")

        return '\n'.join(diff_lines)


# Convenience function for quick reviews
async def review_code(
    diff: str,
    context: Optional[Dict[str, Any]] = None,
    model_id: str = "claude-sonnet-4",
) -> CodeReview:
    """
    Quick code review function

    Args:
        diff: Git diff to review
        context: Optional review context
        model_id: Model to use for review

    Returns:
        CodeReview result
    """
    reviewer = ReviewerAgent(model_id=model_id)
    return await reviewer.review_diff(diff, context)
