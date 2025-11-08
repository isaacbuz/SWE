"""
Test Generation and Execution Agent

Generates and executes various types of tests:
- Unit tests from code
- Integration tests from specifications
- Test data generation
- Mutation testing
- Coverage analysis

Supports multiple testing frameworks (pytest, vitest, jest, etc.)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from enum import Enum
import re
import asyncio
import logging
import json

logger = logging.getLogger(__name__)


class TestType(Enum):
    """Types of tests"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    MUTATION = "mutation"
    PERFORMANCE = "performance"


class TestStatus(Enum):
    """Test execution status"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestCase:
    """A single test case"""
    name: str
    test_type: TestType
    code: str
    file_path: str
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    test_data: Optional[Dict[str, Any]] = None


@dataclass
class TestResult:
    """Result of running a test"""
    test_name: str
    status: TestStatus
    duration_ms: float
    error_message: Optional[str] = None
    output: Optional[str] = None
    coverage: Optional[Dict[str, Any]] = None


@dataclass
class TestSuiteResult:
    """Results from running a test suite"""
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration_ms: float
    coverage_percentage: float
    test_results: List[TestResult] = field(default_factory=list)
    coverage_gaps: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class CoverageGap:
    """An area lacking test coverage"""
    file: str
    function: str
    lines: List[int]
    severity: str  # "critical", "high", "medium", "low"
    suggestion: str


class TesterAgent:
    """
    Test Generation and Execution Agent

    Generates comprehensive tests and analyzes coverage to ensure
    code quality and correctness.
    """

    def __init__(
        self,
        model_id: str = "claude-sonnet-4",
        framework: str = "pytest",  # pytest, jest, vitest, etc.
        coverage_threshold: float = 80.0,
    ):
        """
        Initialize the Tester Agent

        Args:
            model_id: LLM model to use for test generation
            framework: Testing framework to use
            coverage_threshold: Minimum acceptable coverage percentage
        """
        self.model_id = model_id
        self.framework = framework
        self.coverage_threshold = coverage_threshold

    async def generate_unit_tests(
        self,
        code: str,
        file_path: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[TestCase]:
        """
        Generate unit tests for given code

        Args:
            code: Source code to test
            file_path: Path to the source file
            context: Additional context (dependencies, etc.)

        Returns:
            List of generated test cases
        """
        logger.info(f"Generating unit tests for {file_path}")

        # Parse code to identify testable units
        functions = self._extract_functions(code)
        classes = self._extract_classes(code)

        test_cases = []

        # Generate tests for each function
        for func in functions:
            tests = await self._generate_function_tests(func, file_path)
            test_cases.extend(tests)

        # Generate tests for each class
        for cls in classes:
            tests = await self._generate_class_tests(cls, file_path)
            test_cases.extend(tests)

        logger.info(f"Generated {len(test_cases)} unit tests")
        return test_cases

    async def generate_integration_tests(
        self,
        specification: str,
        components: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[TestCase]:
        """
        Generate integration tests from specifications

        Args:
            specification: Test specification or user story
            components: Components to test together
            context: Additional context

        Returns:
            List of integration test cases
        """
        logger.info(f"Generating integration tests for {len(components)} components")

        test_cases = []

        # Parse specification for test scenarios
        scenarios = self._extract_test_scenarios(specification)

        for scenario in scenarios:
            test = await self._generate_integration_test(
                scenario,
                components,
                context,
            )
            if test:
                test_cases.append(test)

        logger.info(f"Generated {len(test_cases)} integration tests")
        return test_cases

    async def execute_tests(
        self,
        test_files: List[str],
        coverage: bool = True,
    ) -> TestSuiteResult:
        """
        Execute test suite

        Args:
            test_files: List of test files to run
            coverage: Whether to collect coverage data

        Returns:
            TestSuiteResult with execution results
        """
        logger.info(f"Executing {len(test_files)} test files")

        # This would integrate with actual test runners
        # For now, simulating the execution
        import time
        start_time = time.time()

        test_results = []

        for test_file in test_files:
            results = await self._run_test_file(test_file, coverage)
            test_results.extend(results)

        duration_ms = (time.time() - start_time) * 1000

        # Calculate statistics
        total_tests = len(test_results)
        passed = sum(1 for r in test_results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in test_results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in test_results if r.status == TestStatus.SKIPPED)
        errors = sum(1 for r in test_results if r.status == TestStatus.ERROR)

        # Aggregate coverage
        coverage_percentage = self._calculate_coverage(test_results)

        # Identify coverage gaps
        coverage_gaps = await self._identify_coverage_gaps(test_results)

        # Generate recommendations
        recommendations = self._generate_test_recommendations(
            test_results,
            coverage_percentage,
            coverage_gaps,
        )

        result = TestSuiteResult(
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration_ms=duration_ms,
            coverage_percentage=coverage_percentage,
            test_results=test_results,
            coverage_gaps=coverage_gaps,
            recommendations=recommendations,
        )

        logger.info(
            f"Tests completed: {passed}/{total_tests} passed, "
            f"{coverage_percentage:.1f}% coverage"
        )

        return result

    async def generate_test_data(
        self,
        schema: Dict[str, Any],
        count: int = 10,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate test data based on schema

        Args:
            schema: Data schema (JSON Schema, TypeScript type, etc.)
            count: Number of test data items to generate
            constraints: Additional constraints (ranges, patterns, etc.)

        Returns:
            List of generated test data items
        """
        logger.info(f"Generating {count} test data items")

        test_data = []

        for i in range(count):
            item = await self._generate_data_item(schema, constraints, i)
            test_data.append(item)

        logger.info(f"Generated {len(test_data)} test data items")
        return test_data

    async def run_mutation_tests(
        self,
        source_file: str,
        test_file: str,
    ) -> Dict[str, Any]:
        """
        Run mutation testing to assess test quality

        Args:
            source_file: Source code file
            test_file: Test file

        Returns:
            Mutation testing results
        """
        logger.info(f"Running mutation tests on {source_file}")

        # Generate mutations
        mutations = await self._generate_mutations(source_file)

        killed_mutations = 0
        survived_mutations = 0

        for mutation in mutations:
            # Apply mutation
            # Run tests
            # Check if tests fail (mutation killed)
            killed = await self._test_mutation(mutation, test_file)

            if killed:
                killed_mutations += 1
            else:
                survived_mutations += 1

        mutation_score = (
            killed_mutations / len(mutations) * 100 if mutations else 0
        )

        result = {
            'total_mutations': len(mutations),
            'killed': killed_mutations,
            'survived': survived_mutations,
            'mutation_score': mutation_score,
            'quality_assessment': self._assess_mutation_score(mutation_score),
        }

        logger.info(f"Mutation score: {mutation_score:.1f}%")
        return result

    async def analyze_coverage_gaps(
        self,
        coverage_data: Dict[str, Any],
        source_files: List[str],
    ) -> List[CoverageGap]:
        """
        Analyze coverage data to identify gaps

        Args:
            coverage_data: Coverage report data
            source_files: Source files to analyze

        Returns:
            List of coverage gaps
        """
        logger.info("Analyzing coverage gaps")

        gaps = []

        for file in source_files:
            file_coverage = coverage_data.get('files', {}).get(file, {})
            uncovered_lines = file_coverage.get('uncovered_lines', [])

            if uncovered_lines:
                # Group uncovered lines into functions
                functions = self._identify_uncovered_functions(
                    file,
                    uncovered_lines,
                )

                for func in functions:
                    gap = CoverageGap(
                        file=file,
                        function=func['name'],
                        lines=func['lines'],
                        severity=self._assess_gap_severity(func),
                        suggestion=self._suggest_gap_fix(func),
                    )
                    gaps.append(gap)

        logger.info(f"Found {len(gaps)} coverage gaps")
        return gaps

    # Private helper methods

    def _extract_functions(self, code: str) -> List[Dict[str, Any]]:
        """Extract function definitions from code"""
        functions = []
        lines = code.split('\n')

        for i, line in enumerate(lines):
            # Python function
            match = re.match(r'^(\s*)def\s+(\w+)\s*\((.*?)\)', line)
            if match:
                indent, name, params = match.groups()
                # Extract function body
                body_lines = [line]
                j = i + 1
                base_indent = len(indent)

                while j < len(lines):
                    next_line = lines[j]
                    if next_line.strip() and not next_line.startswith(' ' * (base_indent + 1)):
                        if not next_line.strip().startswith('#'):
                            break
                    body_lines.append(next_line)
                    j += 1

                functions.append({
                    'name': name,
                    'params': params,
                    'body': '\n'.join(body_lines),
                    'line_number': i + 1,
                })

        return functions

    def _extract_classes(self, code: str) -> List[Dict[str, Any]]:
        """Extract class definitions from code"""
        classes = []
        lines = code.split('\n')

        for i, line in enumerate(lines):
            match = re.match(r'^class\s+(\w+)', line)
            if match:
                name = match.group(1)
                # Extract class body
                body_lines = [line]
                j = i + 1

                while j < len(lines):
                    next_line = lines[j]
                    if next_line and not next_line[0].isspace() and next_line.strip():
                        break
                    body_lines.append(next_line)
                    j += 1

                classes.append({
                    'name': name,
                    'body': '\n'.join(body_lines),
                    'line_number': i + 1,
                })

        return classes

    async def _generate_function_tests(
        self,
        func: Dict[str, Any],
        file_path: str,
    ) -> List[TestCase]:
        """Generate tests for a single function"""
        tests = []

        # Generate test file path
        test_file = self._get_test_file_path(file_path)

        # Generate basic test
        test_name = f"test_{func['name']}_basic"
        test_code = self._generate_basic_function_test(func)

        tests.append(TestCase(
            name=test_name,
            test_type=TestType.UNIT,
            code=test_code,
            file_path=test_file,
            description=f"Basic test for {func['name']}",
        ))

        # Generate edge case tests
        edge_test_name = f"test_{func['name']}_edge_cases"
        edge_test_code = self._generate_edge_case_test(func)

        tests.append(TestCase(
            name=edge_test_name,
            test_type=TestType.UNIT,
            code=edge_test_code,
            file_path=test_file,
            description=f"Edge case tests for {func['name']}",
        ))

        return tests

    async def _generate_class_tests(
        self,
        cls: Dict[str, Any],
        file_path: str,
    ) -> List[TestCase]:
        """Generate tests for a class"""
        tests = []

        test_file = self._get_test_file_path(file_path)

        # Generate initialization test
        test_name = f"test_{cls['name']}_init"
        test_code = self._generate_class_init_test(cls)

        tests.append(TestCase(
            name=test_name,
            test_type=TestType.UNIT,
            code=test_code,
            file_path=test_file,
            description=f"Test {cls['name']} initialization",
        ))

        return tests

    def _generate_basic_function_test(self, func: Dict[str, Any]) -> str:
        """Generate basic test code for a function"""
        if self.framework == "pytest":
            return f"""
def test_{func['name']}_basic():
    \"\"\"Test {func['name']} with basic inputs\"\"\"
    # Arrange
    # TODO: Set up test data

    # Act
    result = {func['name']}()

    # Assert
    assert result is not None
    # TODO: Add specific assertions
"""
        elif self.framework in ["jest", "vitest"]:
            return f"""
describe('{func['name']}', () => {{
    it('should work with basic inputs', () => {{
        // Arrange
        // TODO: Set up test data

        // Act
        const result = {func['name']}();

        // Assert
        expect(result).toBeDefined();
        // TODO: Add specific assertions
    }});
}});
"""
        return ""

    def _generate_edge_case_test(self, func: Dict[str, Any]) -> str:
        """Generate edge case test code"""
        if self.framework == "pytest":
            return f"""
def test_{func['name']}_edge_cases():
    \"\"\"Test {func['name']} with edge cases\"\"\"
    # Test with None
    # Test with empty input
    # Test with invalid input
    # TODO: Implement edge case tests
    pass
"""
        return ""

    def _generate_class_init_test(self, cls: Dict[str, Any]) -> str:
        """Generate class initialization test"""
        if self.framework == "pytest":
            return f"""
def test_{cls['name']}_initialization():
    \"\"\"Test {cls['name']} can be initialized\"\"\"
    # Arrange
    # TODO: Prepare initialization parameters

    # Act
    instance = {cls['name']}()

    # Assert
    assert instance is not None
    # TODO: Add specific assertions
"""
        return ""

    def _extract_test_scenarios(self, specification: str) -> List[Dict[str, Any]]:
        """Extract test scenarios from specification"""
        # Parse specification for Given-When-Then patterns
        scenarios = []

        # Look for common patterns
        lines = specification.split('\n')
        current_scenario = None

        for line in lines:
            line = line.strip()
            if line.lower().startswith('scenario:'):
                if current_scenario:
                    scenarios.append(current_scenario)
                current_scenario = {'name': line[9:].strip(), 'steps': []}
            elif current_scenario and any(line.lower().startswith(kw) for kw in ['given', 'when', 'then', 'and']):
                current_scenario['steps'].append(line)

        if current_scenario:
            scenarios.append(current_scenario)

        return scenarios

    async def _generate_integration_test(
        self,
        scenario: Dict[str, Any],
        components: List[str],
        context: Optional[Dict[str, Any]],
    ) -> Optional[TestCase]:
        """Generate a single integration test"""
        test_code = f"""
async def test_{scenario['name'].lower().replace(' ', '_')}():
    \"\"\"
    Integration test: {scenario['name']}

    Steps:
    {chr(10).join('    - ' + step for step in scenario['steps'])}
    \"\"\"
    # TODO: Implement integration test
    pass
"""

        return TestCase(
            name=f"test_{scenario['name'].lower().replace(' ', '_')}",
            test_type=TestType.INTEGRATION,
            code=test_code,
            file_path="tests/integration/test_scenarios.py",
            description=scenario['name'],
        )

    async def _run_test_file(
        self,
        test_file: str,
        coverage: bool,
    ) -> List[TestResult]:
        """Run tests in a file"""
        # Simulate test execution
        # In production, this would actually run pytest/jest/etc

        await asyncio.sleep(0.1)  # Simulate test execution time

        # Mock results
        return [
            TestResult(
                test_name=f"test_example_1",
                status=TestStatus.PASSED,
                duration_ms=45.2,
                coverage={'lines': 85.5} if coverage else None,
            ),
            TestResult(
                test_name=f"test_example_2",
                status=TestStatus.PASSED,
                duration_ms=32.1,
                coverage={'lines': 90.0} if coverage else None,
            ),
        ]

    def _calculate_coverage(self, test_results: List[TestResult]) -> float:
        """Calculate overall coverage percentage"""
        coverage_values = [
            r.coverage.get('lines', 0)
            for r in test_results
            if r.coverage
        ]

        if not coverage_values:
            return 0.0

        return sum(coverage_values) / len(coverage_values)

    async def _identify_coverage_gaps(
        self,
        test_results: List[TestResult],
    ) -> List[Dict[str, Any]]:
        """Identify areas lacking coverage"""
        # This would analyze actual coverage data
        # For now, returning mock gaps
        return [
            {
                'file': 'src/utils.py',
                'function': 'handle_edge_case',
                'lines': [45, 46, 47],
                'severity': 'high',
            }
        ]

    def _generate_test_recommendations(
        self,
        test_results: List[TestResult],
        coverage_percentage: float,
        coverage_gaps: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate recommendations for improving tests"""
        recommendations = []

        if coverage_percentage < self.coverage_threshold:
            recommendations.append(
                f"Coverage ({coverage_percentage:.1f}%) is below threshold "
                f"({self.coverage_threshold}%). Add more tests."
            )

        failed_count = sum(1 for r in test_results if r.status == TestStatus.FAILED)
        if failed_count > 0:
            recommendations.append(
                f"{failed_count} test(s) failing. Fix failing tests before merging."
            )

        if len(coverage_gaps) > 5:
            recommendations.append(
                f"Found {len(coverage_gaps)} coverage gaps. "
                "Prioritize testing critical paths."
            )

        return recommendations

    async def _generate_data_item(
        self,
        schema: Dict[str, Any],
        constraints: Optional[Dict[str, Any]],
        index: int,
    ) -> Dict[str, Any]:
        """Generate a single test data item"""
        # Generate data based on schema
        # This is simplified - production would handle complex schemas
        data = {}

        for field, field_type in schema.items():
            if field_type == "string":
                data[field] = f"test_value_{index}"
            elif field_type == "number":
                data[field] = index
            elif field_type == "boolean":
                data[field] = index % 2 == 0
            elif field_type == "array":
                data[field] = [f"item_{i}" for i in range(3)]

        return data

    async def _generate_mutations(self, source_file: str) -> List[Dict[str, Any]]:
        """Generate code mutations for mutation testing"""
        # Common mutation operations:
        # - Change operators (+ to -, < to <=, etc.)
        # - Change constants
        # - Remove statements
        # This is simplified
        return [
            {'type': 'operator', 'line': 10, 'original': '+', 'mutated': '-'},
            {'type': 'constant', 'line': 15, 'original': '0', 'mutated': '1'},
        ]

    async def _test_mutation(
        self,
        mutation: Dict[str, Any],
        test_file: str,
    ) -> bool:
        """Test if a mutation is killed by tests"""
        # Apply mutation, run tests, check if they fail
        # Simulate: 80% of mutations are killed
        import random
        return random.random() < 0.8

    def _assess_mutation_score(self, score: float) -> str:
        """Assess mutation testing score"""
        if score >= 80:
            return "Excellent - Tests are highly effective"
        elif score >= 60:
            return "Good - Tests catch most issues"
        elif score >= 40:
            return "Fair - Tests need improvement"
        else:
            return "Poor - Tests are inadequate"

    def _identify_uncovered_functions(
        self,
        file: str,
        uncovered_lines: List[int],
    ) -> List[Dict[str, Any]]:
        """Identify functions with uncovered lines"""
        # This would parse the file and map lines to functions
        # Simplified version
        return [
            {
                'name': 'example_function',
                'lines': uncovered_lines,
            }
        ]

    def _assess_gap_severity(self, func: Dict[str, Any]) -> str:
        """Assess severity of a coverage gap"""
        # Consider: number of uncovered lines, function complexity, etc.
        line_count = len(func.get('lines', []))

        if line_count > 20:
            return "critical"
        elif line_count > 10:
            return "high"
        elif line_count > 5:
            return "medium"
        else:
            return "low"

    def _suggest_gap_fix(self, func: Dict[str, Any]) -> str:
        """Suggest how to fix a coverage gap"""
        return f"Add tests covering {func['name']} to improve coverage"

    def _get_test_file_path(self, source_file: str) -> str:
        """Get corresponding test file path"""
        # Convert src/module.py to tests/test_module.py
        if 'src/' in source_file:
            return source_file.replace('src/', 'tests/test_')
        else:
            return f"tests/test_{source_file}"


# Convenience functions

async def generate_tests(
    code: str,
    file_path: str,
    test_type: TestType = TestType.UNIT,
) -> List[TestCase]:
    """
    Quick test generation function

    Args:
        code: Source code
        file_path: File path
        test_type: Type of tests to generate

    Returns:
        List of test cases
    """
    tester = TesterAgent()

    if test_type == TestType.UNIT:
        return await tester.generate_unit_tests(code, file_path)
    else:
        raise ValueError(f"Unsupported test type: {test_type}")


async def run_tests(
    test_files: List[str],
    coverage: bool = True,
) -> TestSuiteResult:
    """
    Quick test execution function

    Args:
        test_files: Test files to run
        coverage: Collect coverage data

    Returns:
        Test suite results
    """
    tester = TesterAgent()
    return await tester.execute_tests(test_files, coverage)
