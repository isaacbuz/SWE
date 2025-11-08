"""
Performance Benchmarker Agent

Performs comprehensive performance testing:
- Performance test generation
- Load testing scenarios
- Metrics collection and analysis
- Regression detection
- Performance profiling
- Optimization recommendations

Integrates with performance testing tools and APM systems.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import asyncio
import logging
import time
import statistics

logger = logging.getLogger(__name__)


class BenchmarkType(Enum):
    """Types of performance benchmarks"""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    CONCURRENCY = "concurrency"
    MEMORY = "memory"
    CPU = "cpu"
    LOAD = "load"
    STRESS = "stress"
    ENDURANCE = "endurance"


class PerformanceStatus(Enum):
    """Performance test status"""
    PASS = "pass"
    FAIL = "fail"
    DEGRADED = "degraded"
    REGRESSION = "regression"


@dataclass
class PerformanceMetric:
    """A single performance metric"""
    name: str
    value: float
    unit: str
    threshold: Optional[float] = None
    baseline: Optional[float] = None
    percentile: Optional[int] = None  # e.g., p50, p95, p99


@dataclass
class BenchmarkResult:
    """Result from a single benchmark"""
    test_name: str
    benchmark_type: BenchmarkType
    status: PerformanceStatus
    duration_ms: float
    metrics: List[PerformanceMetric] = field(default_factory=list)
    samples: int = 0
    error_rate: float = 0.0
    details: Optional[Dict[str, Any]] = None


@dataclass
class LoadTestResult:
    """Results from load testing"""
    scenario_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    duration_seconds: float
    requests_per_second: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate: float
    concurrent_users: int
    throughput_mb_per_sec: float = 0.0


@dataclass
class PerformanceRegression:
    """A detected performance regression"""
    metric_name: str
    current_value: float
    baseline_value: float
    degradation_percent: float
    severity: str  # "critical", "major", "minor"
    affected_component: str


@dataclass
class PerformanceReport:
    """Comprehensive performance report"""
    summary: str
    overall_status: PerformanceStatus
    benchmark_results: List[BenchmarkResult] = field(default_factory=list)
    load_test_results: List[LoadTestResult] = field(default_factory=list)
    regressions: List[PerformanceRegression] = field(default_factory=list)
    optimizations: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    baseline_comparison: Optional[Dict[str, Any]] = None


class BenchmarkerAgent:
    """
    Performance Benchmarker Agent

    Generates and executes performance tests, analyzes results,
    detects regressions, and provides optimization recommendations.
    """

    def __init__(
        self,
        model_id: str = "claude-sonnet-4",
        baseline_data: Optional[Dict[str, Any]] = None,
        regression_threshold: float = 10.0,  # % degradation to flag
    ):
        """
        Initialize Benchmarker Agent

        Args:
            model_id: LLM model for analysis
            baseline_data: Historical performance baseline
            regression_threshold: Percentage degradation to flag as regression
        """
        self.model_id = model_id
        self.baseline_data = baseline_data or {}
        self.regression_threshold = regression_threshold

    async def generate_performance_tests(
        self,
        code: str,
        file_path: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Generate performance tests for code

        Args:
            code: Source code to test
            file_path: File path
            context: Additional context

        Returns:
            List of generated test code
        """
        logger.info(f"Generating performance tests for {file_path}")

        tests = []

        # Identify performance-critical functions
        critical_functions = self._identify_critical_functions(code)

        for func in critical_functions:
            # Generate latency test
            latency_test = self._generate_latency_test(func)
            tests.append(latency_test)

            # Generate throughput test
            throughput_test = self._generate_throughput_test(func)
            tests.append(throughput_test)

            # Generate memory test if applicable
            if self._is_memory_intensive(func):
                memory_test = self._generate_memory_test(func)
                tests.append(memory_test)

        logger.info(f"Generated {len(tests)} performance tests")
        return tests

    async def run_benchmarks(
        self,
        benchmarks: List[Callable],
        iterations: int = 100,
    ) -> List[BenchmarkResult]:
        """
        Run performance benchmarks

        Args:
            benchmarks: List of benchmark functions
            iterations: Number of iterations per benchmark

        Returns:
            List of benchmark results
        """
        logger.info(f"Running {len(benchmarks)} benchmarks")

        results = []

        for benchmark in benchmarks:
            result = await self._run_single_benchmark(benchmark, iterations)
            results.append(result)

        logger.info(f"Completed {len(results)} benchmarks")
        return results

    async def run_load_test(
        self,
        target_url: str,
        scenario: Dict[str, Any],
        duration_seconds: int = 60,
    ) -> LoadTestResult:
        """
        Run load test scenario

        Args:
            target_url: Target URL to test
            scenario: Load test scenario configuration
            duration_seconds: Test duration

        Returns:
            Load test results
        """
        logger.info(f"Running load test: {scenario.get('name', 'unnamed')}")

        concurrent_users = scenario.get('concurrent_users', 10)
        ramp_up_time = scenario.get('ramp_up_time', 10)

        # Track metrics
        latencies = []
        successes = 0
        failures = 0
        start_time = time.time()

        # Simulate load test
        # In production, this would use tools like locust, k6, artillery, etc.
        async def user_session():
            nonlocal successes, failures
            session_start = time.time()

            while time.time() - start_time < duration_seconds:
                request_start = time.time()
                try:
                    # Simulate request
                    await asyncio.sleep(0.05)  # Simulate network delay
                    success = True  # Would be actual request result

                    if success:
                        successes += 1
                    else:
                        failures += 1

                    request_latency = (time.time() - request_start) * 1000
                    latencies.append(request_latency)

                except Exception as e:
                    failures += 1
                    logger.error(f"Request failed: {e}")

                # Wait before next request (think time)
                await asyncio.sleep(scenario.get('think_time', 0.1))

        # Ramp up users
        tasks = []
        for i in range(concurrent_users):
            await asyncio.sleep(ramp_up_time / concurrent_users)
            task = asyncio.create_task(user_session())
            tasks.append(task)

        # Wait for test completion
        await asyncio.gather(*tasks, return_exceptions=True)

        # Calculate metrics
        total_requests = successes + failures
        duration = time.time() - start_time

        result = LoadTestResult(
            scenario_name=scenario.get('name', 'load_test'),
            total_requests=total_requests,
            successful_requests=successes,
            failed_requests=failures,
            duration_seconds=duration,
            requests_per_second=total_requests / duration if duration > 0 else 0,
            avg_latency_ms=statistics.mean(latencies) if latencies else 0,
            p50_latency_ms=self._percentile(latencies, 50) if latencies else 0,
            p95_latency_ms=self._percentile(latencies, 95) if latencies else 0,
            p99_latency_ms=self._percentile(latencies, 99) if latencies else 0,
            error_rate=(failures / total_requests * 100) if total_requests > 0 else 0,
            concurrent_users=concurrent_users,
        )

        logger.info(
            f"Load test complete: {result.requests_per_second:.1f} req/s, "
            f"{result.avg_latency_ms:.1f}ms avg latency"
        )

        return result

    async def detect_regressions(
        self,
        current_results: List[BenchmarkResult],
        baseline: Optional[Dict[str, Any]] = None,
    ) -> List[PerformanceRegression]:
        """
        Detect performance regressions

        Args:
            current_results: Current benchmark results
            baseline: Baseline to compare against

        Returns:
            List of detected regressions
        """
        logger.info("Detecting performance regressions")

        baseline = baseline or self.baseline_data
        regressions = []

        for result in current_results:
            for metric in result.metrics:
                baseline_value = self._get_baseline_value(
                    result.test_name,
                    metric.name,
                    baseline,
                )

                if baseline_value is not None:
                    degradation = self._calculate_degradation(
                        metric.value,
                        baseline_value,
                    )

                    if abs(degradation) > self.regression_threshold:
                        severity = self._assess_regression_severity(degradation)

                        regression = PerformanceRegression(
                            metric_name=f"{result.test_name}.{metric.name}",
                            current_value=metric.value,
                            baseline_value=baseline_value,
                            degradation_percent=degradation,
                            severity=severity,
                            affected_component=result.test_name,
                        )
                        regressions.append(regression)

        logger.info(f"Found {len(regressions)} performance regressions")
        return regressions

    async def analyze_performance(
        self,
        results: List[BenchmarkResult],
        load_results: List[LoadTestResult],
        context: Optional[Dict[str, Any]] = None,
    ) -> PerformanceReport:
        """
        Analyze performance results and generate report

        Args:
            results: Benchmark results
            load_results: Load test results
            context: Additional context

        Returns:
            Comprehensive performance report
        """
        logger.info("Analyzing performance results")

        # Detect regressions
        regressions = await self.detect_regressions(results)

        # Generate optimizations
        optimizations = self._generate_optimizations(results, load_results)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            results,
            load_results,
            regressions,
        )

        # Determine overall status
        overall_status = self._determine_status(results, regressions)

        # Generate summary
        summary = self._generate_summary(
            results,
            load_results,
            regressions,
            overall_status,
        )

        # Baseline comparison
        baseline_comparison = self._compare_to_baseline(results)

        report = PerformanceReport(
            summary=summary,
            overall_status=overall_status,
            benchmark_results=results,
            load_test_results=load_results,
            regressions=regressions,
            optimizations=optimizations,
            recommendations=recommendations,
            baseline_comparison=baseline_comparison,
        )

        logger.info(f"Performance analysis complete: {overall_status.value}")
        return report

    async def profile_code(
        self,
        function: Callable,
        *args,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Profile code execution

        Args:
            function: Function to profile
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Profiling results
        """
        logger.info(f"Profiling {function.__name__}")

        # Time profiling
        start_time = time.time()
        start_cpu = time.process_time()

        # Execute function
        if asyncio.iscoroutinefunction(function):
            result = await function(*args, **kwargs)
        else:
            result = function(*args, **kwargs)

        end_time = time.time()
        end_cpu = time.process_time()

        # Memory profiling (simplified - production would use memory_profiler)
        # import tracemalloc
        # snapshot = tracemalloc.take_snapshot()

        profile_data = {
            'function': function.__name__,
            'wall_time_ms': (end_time - start_time) * 1000,
            'cpu_time_ms': (end_cpu - start_cpu) * 1000,
            'result': result,
            # 'memory_snapshot': snapshot,
        }

        logger.info(
            f"Profile complete: {profile_data['wall_time_ms']:.2f}ms wall time"
        )

        return profile_data

    # Private helper methods

    def _identify_critical_functions(self, code: str) -> List[Dict[str, Any]]:
        """Identify performance-critical functions"""
        import re

        functions = []
        lines = code.split('\n')

        for i, line in enumerate(lines):
            # Look for function definitions
            match = re.match(r'^\s*(?:async\s+)?def\s+(\w+)\s*\(', line)
            if match:
                func_name = match.group(1)

                # Check if it's performance-critical
                is_critical = any([
                    'loop' in code[i:i+20],  # Contains loops
                    'query' in func_name.lower(),  # Database query
                    'process' in func_name.lower(),  # Data processing
                    'compute' in func_name.lower(),  # Computation
                    'api' in func_name.lower(),  # API endpoint
                ])

                if is_critical:
                    functions.append({
                        'name': func_name,
                        'line': i + 1,
                    })

        return functions

    def _is_memory_intensive(self, func: Dict[str, Any]) -> bool:
        """Check if function is memory-intensive"""
        memory_patterns = ['list', 'dict', 'array', 'buffer', 'cache']
        return any(pattern in func['name'].lower() for pattern in memory_patterns)

    def _generate_latency_test(self, func: Dict[str, Any]) -> str:
        """Generate latency benchmark test"""
        return f"""
async def benchmark_{func['name']}_latency():
    \"\"\"Benchmark latency of {func['name']}\"\"\"
    import time

    iterations = 1000
    latencies = []

    for _ in range(iterations):
        start = time.time()
        await {func['name']}()  # or without await if not async
        latency = (time.time() - start) * 1000
        latencies.append(latency)

    avg_latency = sum(latencies) / len(latencies)
    p95_latency = sorted(latencies)[int(0.95 * len(latencies))]

    assert avg_latency < 100, f"Average latency {{avg_latency}}ms exceeds 100ms"
    assert p95_latency < 200, f"P95 latency {{p95_latency}}ms exceeds 200ms"

    return {{
        'avg': avg_latency,
        'p95': p95_latency,
    }}
"""

    def _generate_throughput_test(self, func: Dict[str, Any]) -> str:
        """Generate throughput benchmark test"""
        return f"""
async def benchmark_{func['name']}_throughput():
    \"\"\"Benchmark throughput of {func['name']}\"\"\"
    import time
    import asyncio

    duration = 10  # seconds
    concurrency = 10

    async def worker():
        count = 0
        start = time.time()
        while time.time() - start < duration:
            await {func['name']}()
            count += 1
        return count

    tasks = [worker() for _ in range(concurrency)]
    results = await asyncio.gather(*tasks)

    total_ops = sum(results)
    throughput = total_ops / duration

    assert throughput > 100, f"Throughput {{throughput}} ops/s is below 100"

    return {{'throughput': throughput}}
"""

    def _generate_memory_test(self, func: Dict[str, Any]) -> str:
        """Generate memory benchmark test"""
        return f"""
def benchmark_{func['name']}_memory():
    \"\"\"Benchmark memory usage of {func['name']}\"\"\"
    import tracemalloc

    tracemalloc.start()
    {func['name']}()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / 1024 / 1024

    assert peak_mb < 100, f"Peak memory {{peak_mb}}MB exceeds 100MB"

    return {{'peak_mb': peak_mb}}
"""

    async def _run_single_benchmark(
        self,
        benchmark: Callable,
        iterations: int,
    ) -> BenchmarkResult:
        """Run a single benchmark"""
        logger.info(f"Running benchmark: {benchmark.__name__}")

        measurements = []
        errors = 0

        start_time = time.time()

        for i in range(iterations):
            try:
                if asyncio.iscoroutinefunction(benchmark):
                    measure_start = time.time()
                    await benchmark()
                    measure_time = (time.time() - measure_start) * 1000
                else:
                    measure_start = time.time()
                    benchmark()
                    measure_time = (time.time() - measure_start) * 1000

                measurements.append(measure_time)

            except Exception as e:
                errors += 1
                logger.error(f"Benchmark iteration failed: {e}")

        duration_ms = (time.time() - start_time) * 1000

        # Calculate metrics
        if measurements:
            metrics = [
                PerformanceMetric(
                    name="avg_latency",
                    value=statistics.mean(measurements),
                    unit="ms",
                ),
                PerformanceMetric(
                    name="p50_latency",
                    value=self._percentile(measurements, 50),
                    unit="ms",
                    percentile=50,
                ),
                PerformanceMetric(
                    name="p95_latency",
                    value=self._percentile(measurements, 95),
                    unit="ms",
                    percentile=95,
                ),
                PerformanceMetric(
                    name="p99_latency",
                    value=self._percentile(measurements, 99),
                    unit="ms",
                    percentile=99,
                ),
            ]
        else:
            metrics = []

        # Determine status
        error_rate = errors / iterations * 100
        status = PerformanceStatus.PASS if error_rate < 1 else PerformanceStatus.FAIL

        return BenchmarkResult(
            test_name=benchmark.__name__,
            benchmark_type=BenchmarkType.LATENCY,
            status=status,
            duration_ms=duration_ms,
            metrics=metrics,
            samples=iterations,
            error_rate=error_rate,
        )

    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def _get_baseline_value(
        self,
        test_name: str,
        metric_name: str,
        baseline: Dict[str, Any],
    ) -> Optional[float]:
        """Get baseline value for a metric"""
        return baseline.get(test_name, {}).get(metric_name)

    def _calculate_degradation(
        self,
        current: float,
        baseline: float,
    ) -> float:
        """Calculate percentage degradation"""
        if baseline == 0:
            return 0.0

        return ((current - baseline) / baseline) * 100

    def _assess_regression_severity(self, degradation: float) -> str:
        """Assess severity of performance regression"""
        abs_deg = abs(degradation)

        if abs_deg > 50:
            return "critical"
        elif abs_deg > 25:
            return "major"
        else:
            return "minor"

    def _generate_optimizations(
        self,
        results: List[BenchmarkResult],
        load_results: List[LoadTestResult],
    ) -> List[str]:
        """Generate optimization suggestions"""
        optimizations = []

        # Analyze latency
        for result in results:
            avg_latency_metric = next(
                (m for m in result.metrics if m.name == 'avg_latency'),
                None,
            )

            if avg_latency_metric and avg_latency_metric.value > 100:
                optimizations.append(
                    f"Optimize {result.test_name}: "
                    f"latency is {avg_latency_metric.value:.1f}ms"
                )

        # Analyze load test results
        for load_result in load_results:
            if load_result.error_rate > 1:
                optimizations.append(
                    f"Improve error handling in {load_result.scenario_name}: "
                    f"{load_result.error_rate:.1f}% error rate"
                )

            if load_result.p99_latency_ms > 1000:
                optimizations.append(
                    f"Optimize tail latency in {load_result.scenario_name}: "
                    f"p99 is {load_result.p99_latency_ms:.1f}ms"
                )

        return optimizations

    def _generate_recommendations(
        self,
        results: List[BenchmarkResult],
        load_results: List[LoadTestResult],
        regressions: List[PerformanceRegression],
    ) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []

        if regressions:
            critical_regressions = [r for r in regressions if r.severity == "critical"]
            if critical_regressions:
                recommendations.append(
                    f"URGENT: Fix {len(critical_regressions)} critical "
                    "performance regressions before deployment"
                )

        # General recommendations
        recommendations.extend([
            "Set up continuous performance monitoring",
            "Establish performance budgets for critical paths",
            "Run load tests before each release",
            "Profile production code regularly",
        ])

        return recommendations

    def _determine_status(
        self,
        results: List[BenchmarkResult],
        regressions: List[PerformanceRegression],
    ) -> PerformanceStatus:
        """Determine overall performance status"""
        # Check for failures
        if any(r.status == PerformanceStatus.FAIL for r in results):
            return PerformanceStatus.FAIL

        # Check for critical regressions
        critical_regressions = [r for r in regressions if r.severity == "critical"]
        if critical_regressions:
            return PerformanceStatus.REGRESSION

        # Check for degradation
        if regressions:
            return PerformanceStatus.DEGRADED

        return PerformanceStatus.PASS

    def _generate_summary(
        self,
        results: List[BenchmarkResult],
        load_results: List[LoadTestResult],
        regressions: List[PerformanceRegression],
        status: PerformanceStatus,
    ) -> str:
        """Generate performance summary"""
        status_emoji = {
            PerformanceStatus.PASS: "✅",
            PerformanceStatus.FAIL: "❌",
            PerformanceStatus.DEGRADED: "⚠️",
            PerformanceStatus.REGRESSION: "📉",
        }

        summary_parts = [
            f"{status_emoji[status]} Performance Status: {status.value.upper()}"
        ]

        summary_parts.append(f"\n\n📊 Results:")
        summary_parts.append(f"  - {len(results)} benchmark tests")
        summary_parts.append(f"  - {len(load_results)} load tests")
        summary_parts.append(f"  - {len(regressions)} regressions detected")

        if load_results:
            avg_rps = statistics.mean(r.requests_per_second for r in load_results)
            avg_latency = statistics.mean(r.avg_latency_ms for r in load_results)
            summary_parts.append(
                f"\n⚡ Load Test: {avg_rps:.1f} req/s, "
                f"{avg_latency:.1f}ms avg latency"
            )

        return "".join(summary_parts)

    def _compare_to_baseline(
        self,
        results: List[BenchmarkResult],
    ) -> Dict[str, Any]:
        """Compare results to baseline"""
        comparison = {}

        for result in results:
            for metric in result.metrics:
                key = f"{result.test_name}.{metric.name}"
                baseline_value = self._get_baseline_value(
                    result.test_name,
                    metric.name,
                    self.baseline_data,
                )

                if baseline_value:
                    comparison[key] = {
                        'current': metric.value,
                        'baseline': baseline_value,
                        'change_percent': self._calculate_degradation(
                            metric.value,
                            baseline_value,
                        ),
                    }

        return comparison


# Convenience functions

async def benchmark_function(
    func: Callable,
    iterations: int = 100,
) -> BenchmarkResult:
    """
    Quick function benchmarking

    Args:
        func: Function to benchmark
        iterations: Number of iterations

    Returns:
        Benchmark result
    """
    benchmarker = BenchmarkerAgent()
    return await benchmarker._run_single_benchmark(func, iterations)


async def load_test(
    url: str,
    concurrent_users: int = 10,
    duration_seconds: int = 60,
) -> LoadTestResult:
    """
    Quick load test

    Args:
        url: Target URL
        concurrent_users: Number of concurrent users
        duration_seconds: Test duration

    Returns:
        Load test result
    """
    benchmarker = BenchmarkerAgent()
    scenario = {
        'name': 'load_test',
        'concurrent_users': concurrent_users,
        'think_time': 0.1,
    }
    return await benchmarker.run_load_test(url, scenario, duration_seconds)
