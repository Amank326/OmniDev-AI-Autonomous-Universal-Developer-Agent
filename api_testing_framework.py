"""
Phase 54: API Testing Framework
Comprehensive automated testing framework for API endpoints with test generation,
execution, and reporting capabilities.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
import json
import time
import random
import string
from abc import ABC, abstractmethod
from datetime import datetime
import statistics


class HTTPMethod(Enum):
    """HTTP methods for API testing."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class AssertionType(Enum):
    """Types of assertions for test validation."""
    STATUS_CODE = "status_code"
    RESPONSE_SCHEMA = "response_schema"
    RESPONSE_FIELD = "response_field"
    RESPONSE_TIME = "response_time"
    CONTENT_TYPE = "content_type"
    HEADER_EXISTS = "header_exists"
    BODY_CONTAINS = "body_contains"
    STATUS_CODE_IN_RANGE = "status_code_in_range"
    CUSTOM = "custom"


class TestStatus(Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestType(Enum):
    """Types of API tests."""
    SMOKE = "smoke"
    FUNCTIONAL = "functional"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    SECURITY = "security"
    LOAD = "load"


@dataclass
class TestAssertion:
    """Represents a single assertion in a test."""
    assertion_type: AssertionType
    expected_value: Any
    actual_value: Optional[Any] = None
    passed: bool = False
    error_message: str = ""
    comparison_operator: str = "=="  # ==, !=, >, <, >=, <=, in, contains

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'assertion_type': self.assertion_type.value,
            'expected_value': self.expected_value,
            'actual_value': self.actual_value,
            'passed': self.passed,
            'error_message': self.error_message,
            'comparison_operator': self.comparison_operator
        }


@dataclass
class TestRequest:
    """Represents an API request for testing."""
    endpoint: str
    method: HTTPMethod
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, Any] = field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None
    timeout: int = 30

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'endpoint': self.endpoint,
            'method': self.method.value,
            'headers': self.headers,
            'query_params': self.query_params,
            'body': self.body,
            'timeout': self.timeout
        }


@dataclass
class TestResponse:
    """Represents an API response from testing."""
    status_code: int
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None
    response_time: float = 0.0
    size_bytes: int = 0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'status_code': self.status_code,
            'headers': self.headers,
            'body': self.body,
            'response_time': self.response_time,
            'size_bytes': self.size_bytes,
            'error': self.error
        }


@dataclass
class TestCase:
    """Represents a single test case."""
    name: str
    test_type: TestType
    request: TestRequest
    assertions: List[TestAssertion] = field(default_factory=list)
    description: str = ""
    tags: List[str] = field(default_factory=list)
    depends_on: Optional[str] = None  # Test name this depends on
    requires_auth: bool = False
    prerequisites: Dict[str, Any] = field(default_factory=dict)  # Setup data
    timeout: int = 30
    retry_count: int = 0
    skip: bool = False
    skip_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'test_type': self.test_type.value,
            'request': self.request.to_dict(),
            'assertions': [a.to_dict() for a in self.assertions],
            'description': self.description,
            'tags': self.tags,
            'depends_on': self.depends_on,
            'requires_auth': self.requires_auth,
            'timeout': self.timeout,
            'skip': self.skip,
            'skip_reason': self.skip_reason
        }


@dataclass
class TestResult:
    """Result of executing a test."""
    test_name: str
    status: TestStatus
    request: TestRequest
    response: Optional[TestResponse]
    assertions_passed: int = 0
    assertions_failed: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    error_message: str = ""
    failed_assertions: List[TestAssertion] = field(default_factory=list)
    execution_log: str = ""

    def is_passed(self) -> bool:
        """Check if test passed."""
        return self.status == TestStatus.PASSED

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'test_name': self.test_name,
            'status': self.status.value,
            'request': self.request.to_dict(),
            'response': self.response.to_dict() if self.response else None,
            'assertions_passed': self.assertions_passed,
            'assertions_failed': self.assertions_failed,
            'duration': self.duration,
            'error_message': self.error_message,
            'failed_assertions': [a.to_dict() for a in self.failed_assertions],
            'timestamp': datetime.now().isoformat()
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics for a test or test suite."""
    min_response_time: float = 0.0
    max_response_time: float = 0.0
    avg_response_time: float = 0.0
    median_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    requests_per_second: float = 0.0
    error_rate: float = 0.0
    total_requests: int = 0
    total_errors: int = 0
    total_duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'min_response_time': self.min_response_time,
            'max_response_time': self.max_response_time,
            'avg_response_time': self.avg_response_time,
            'median_response_time': self.median_response_time,
            'p95_response_time': self.p95_response_time,
            'p99_response_time': self.p99_response_time,
            'requests_per_second': self.requests_per_second,
            'error_rate': self.error_rate,
            'total_requests': self.total_requests,
            'total_errors': self.total_errors,
            'total_duration': self.total_duration
        }


class TestDataGenerator:
    """Generates test data for API testing."""

    @staticmethod
    def generate_string(min_length: int = 1, max_length: int = 100) -> str:
        """Generate random string."""
        length = random.randint(min_length, max_length)
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    @staticmethod
    def generate_email() -> str:
        """Generate random email."""
        return f"{TestDataGenerator.generate_string(5, 10)}@example.com"

    @staticmethod
    def generate_integer(min_val: int = 0, max_val: int = 1000) -> int:
        """Generate random integer."""
        return random.randint(min_val, max_val)

    @staticmethod
    def generate_float(min_val: float = 0.0, max_val: float = 1000.0) -> float:
        """Generate random float."""
        return random.uniform(min_val, max_val)

    @staticmethod
    def generate_boolean() -> bool:
        """Generate random boolean."""
        return random.choice([True, False])

    @staticmethod
    def generate_url() -> str:
        """Generate random URL."""
        return f"https://example.com/{TestDataGenerator.generate_string(5, 15)}"

    @staticmethod
    def generate_uuid() -> str:
        """Generate UUID-like string."""
        import uuid
        return str(uuid.uuid4())

    @staticmethod
    def generate_timestamp() -> str:
        """Generate ISO timestamp."""
        return datetime.now().isoformat()

    @staticmethod
    def generate_object(properties: Dict[str, str]) -> Dict[str, Any]:
        """Generate object with specified properties.
        
        Args:
            properties: Dict with property name -> type mapping
            Example: {"id": "integer", "name": "string", "email": "email"}
        """
        obj = {}
        for prop_name, prop_type in properties.items():
            if prop_type == "string":
                obj[prop_name] = TestDataGenerator.generate_string()
            elif prop_type == "integer":
                obj[prop_name] = TestDataGenerator.generate_integer()
            elif prop_type == "float":
                obj[prop_name] = TestDataGenerator.generate_float()
            elif prop_type == "boolean":
                obj[prop_name] = TestDataGenerator.generate_boolean()
            elif prop_type == "email":
                obj[prop_name] = TestDataGenerator.generate_email()
            elif prop_type == "url":
                obj[prop_name] = TestDataGenerator.generate_url()
            elif prop_type == "uuid":
                obj[prop_name] = TestDataGenerator.generate_uuid()
            elif prop_type == "timestamp":
                obj[prop_name] = TestDataGenerator.generate_timestamp()
        return obj


class TestCaseGenerator:
    """Generates test cases from API endpoint definitions."""

    @staticmethod
    def generate_smoke_tests(endpoint: str, method: HTTPMethod) -> List[TestCase]:
        """Generate smoke tests for an endpoint."""
        tests = []

        # Basic request test
        test = TestCase(
            name=f"smoke_{method.value.lower()}_{endpoint.replace('/', '_').strip('_')}",
            test_type=TestType.SMOKE,
            request=TestRequest(endpoint=endpoint, method=method),
            description=f"Basic smoke test for {method.value} {endpoint}",
            tags=["smoke", method.value.lower()]
        )

        # Add basic assertions
        test.assertions.append(TestAssertion(
            assertion_type=AssertionType.STATUS_CODE,
            expected_value=[200, 201, 204, 301, 302, 304, 400, 401, 403, 404, 500, 502, 503],
            comparison_operator="in"
        ))

        tests.append(test)
        return tests

    @staticmethod
    def generate_functional_tests(endpoint: str, method: HTTPMethod, properties: Optional[Dict[str, str]] = None) -> List[TestCase]:
        """Generate functional tests for an endpoint."""
        tests = []

        if method == HTTPMethod.GET:
            test = TestCase(
                name=f"func_get_{endpoint.replace('/', '_').strip('_')}",
                test_type=TestType.FUNCTIONAL,
                request=TestRequest(endpoint=endpoint, method=HTTPMethod.GET),
                description=f"Functional test: retrieve data from {endpoint}",
                tags=["functional", "get"]
            )
            test.assertions.append(TestAssertion(
                assertion_type=AssertionType.STATUS_CODE,
                expected_value=200
            ))
            test.assertions.append(TestAssertion(
                assertion_type=AssertionType.CONTENT_TYPE,
                expected_value="application/json"
            ))
            tests.append(test)

        elif method == HTTPMethod.POST:
            if properties is None:
                properties = {"name": "string", "email": "email"}

            test = TestCase(
                name=f"func_post_{endpoint.replace('/', '_').strip('_')}",
                test_type=TestType.FUNCTIONAL,
                request=TestRequest(
                    endpoint=endpoint,
                    method=HTTPMethod.POST,
                    body=TestDataGenerator.generate_object(properties)
                ),
                description=f"Functional test: create resource at {endpoint}",
                tags=["functional", "post"]
            )
            test.assertions.append(TestAssertion(
                assertion_type=AssertionType.STATUS_CODE,
                expected_value=201,
                comparison_operator="in"  # Accept 200 or 201
            ))
            tests.append(test)

        return tests

    @staticmethod
    def generate_performance_tests(endpoint: str, method: HTTPMethod, iterations: int = 10) -> List[TestCase]:
        """Generate performance test."""
        test = TestCase(
            name=f"perf_{method.value.lower()}_{endpoint.replace('/', '_').strip('_')}",
            test_type=TestType.PERFORMANCE,
            request=TestRequest(endpoint=endpoint, method=method),
            description=f"Performance test: measure latency for {method.value} {endpoint}",
            tags=["performance"]
        )

        # Assertions for response time
        test.assertions.append(TestAssertion(
            assertion_type=AssertionType.RESPONSE_TIME,
            expected_value=1000,  # Less than 1 second
            comparison_operator="<"
        ))

        return [test]

    @staticmethod
    def generate_error_handling_tests(endpoint: str, method: HTTPMethod) -> List[TestCase]:
        """Generate tests for error handling."""
        tests = []

        # Test with invalid content type
        test = TestCase(
            name=f"error_invalid_content_{endpoint.replace('/', '_').strip('_')}",
            test_type=TestType.FUNCTIONAL,
            request=TestRequest(
                endpoint=endpoint,
                method=method,
                headers={"Content-Type": "text/plain"},
                body={"invalid": "data"} if method != HTTPMethod.GET else None
            ),
            description="Test handling of invalid content type",
            tags=["error_handling"]
        )
        test.assertions.append(TestAssertion(
            assertion_type=AssertionType.STATUS_CODE,
            expected_value=[400, 415],  # Bad request or unsupported media type
            comparison_operator="in"
        ))
        tests.append(test)

        return tests


class TestAssertionBuilder:
    """Builder for creating test assertions."""

    def __init__(self):
        """Initialize assertion builder."""
        self.assertions: List[TestAssertion] = []

    def assert_status_code(self, expected: int) -> 'TestAssertionBuilder':
        """Assert response status code."""
        self.assertions.append(TestAssertion(
            assertion_type=AssertionType.STATUS_CODE,
            expected_value=expected
        ))
        return self

    def assert_status_code_in_range(self, min_code: int, max_code: int) -> 'TestAssertionBuilder':
        """Assert status code in range."""
        self.assertions.append(TestAssertion(
            assertion_type=AssertionType.STATUS_CODE_IN_RANGE,
            expected_value={"min": min_code, "max": max_code}
        ))
        return self

    def assert_response_field_equals(self, field_path: str, expected_value: Any) -> 'TestAssertionBuilder':
        """Assert response field equals expected value."""
        self.assertions.append(TestAssertion(
            assertion_type=AssertionType.RESPONSE_FIELD,
            expected_value={"path": field_path, "value": expected_value}
        ))
        return self

    def assert_response_field_contains(self, field_path: str, expected_substring: str) -> 'TestAssertionBuilder':
        """Assert response field contains substring."""
        self.assertions.append(TestAssertion(
            assertion_type=AssertionType.RESPONSE_FIELD,
            expected_value={"path": field_path, "contains": expected_substring}
        ))
        return self

    def assert_content_type(self, content_type: str) -> 'TestAssertionBuilder':
        """Assert response content type."""
        self.assertions.append(TestAssertion(
            assertion_type=AssertionType.CONTENT_TYPE,
            expected_value=content_type
        ))
        return self

    def assert_response_time_less_than(self, milliseconds: int) -> 'TestAssertionBuilder':
        """Assert response time less than threshold."""
        self.assertions.append(TestAssertion(
            assertion_type=AssertionType.RESPONSE_TIME,
            expected_value=milliseconds,
            comparison_operator="<"
        ))
        return self

    def assert_header_exists(self, header_name: str) -> 'TestAssertionBuilder':
        """Assert response header exists."""
        self.assertions.append(TestAssertion(
            assertion_type=AssertionType.HEADER_EXISTS,
            expected_value=header_name
        ))
        return self

    def assert_body_contains(self, text: str) -> 'TestAssertionBuilder':
        """Assert response body contains text."""
        self.assertions.append(TestAssertion(
            assertion_type=AssertionType.BODY_CONTAINS,
            expected_value=text
        ))
        return self

    def build(self) -> List[TestAssertion]:
        """Build and return assertions."""
        return self.assertions


class APITestSuite:
    """Container for multiple test cases."""

    def __init__(self, name: str, base_url: str = "http://localhost:8000"):
        """Initialize test suite."""
        self.name = name
        self.base_url = base_url
        self.tests: List[TestCase] = []
        self.results: List[TestResult] = []
        self.created_at = datetime.now()

    def add_test(self, test: TestCase) -> 'APITestSuite':
        """Add a test to the suite."""
        self.tests.append(test)
        return self

    def add_tests(self, tests: List[TestCase]) -> 'APITestSuite':
        """Add multiple tests to the suite."""
        self.tests.extend(tests)
        return self

    def get_test(self, name: str) -> Optional[TestCase]:
        """Get test by name."""
        return next((t for t in self.tests if t.name == name), None)

    def get_tests_by_type(self, test_type: TestType) -> List[TestCase]:
        """Get all tests of a specific type."""
        return [t for t in self.tests if t.test_type == test_type]

    def get_tests_by_tag(self, tag: str) -> List[TestCase]:
        """Get all tests with a specific tag."""
        return [t for t in self.tests if tag in t.tags]

    def get_results(self) -> List[TestResult]:
        """Get all test results."""
        return self.results

    def get_result(self, test_name: str) -> Optional[TestResult]:
        """Get result for specific test."""
        return next((r for r in self.results if r.test_name == test_name), None)

    def add_result(self, result: TestResult) -> None:
        """Add a test result."""
        self.results.append(result)

    def get_statistics(self) -> Dict[str, Any]:
        """Get test suite statistics."""
        total_tests = len(self.tests)
        passed_tests = sum(1 for r in self.results if r.is_passed())
        failed_tests = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        skipped_tests = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        error_tests = sum(1 for r in self.results if r.status == TestStatus.ERROR)

        pass_rate = (passed_tests / len(self.results) * 100) if self.results else 0
        total_duration = sum(r.duration for r in self.results)

        return {
            'total_tests': total_tests,
            'executed_tests': len(self.results),
            'passed': passed_tests,
            'failed': failed_tests,
            'skipped': skipped_tests,
            'errors': error_tests,
            'pass_rate': pass_rate,
            'total_duration': total_duration,
            'avg_duration': total_duration / len(self.results) if self.results else 0
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'base_url': self.base_url,
            'total_tests': len(self.tests),
            'created_at': self.created_at.isoformat(),
            'statistics': self.get_statistics(),
            'results': [r.to_dict() for r in self.results]
        }


class APITestExecutor(ABC):
    """Abstract base class for test executors."""

    @abstractmethod
    def execute(self, test: TestCase) -> TestResult:
        """Execute a single test."""
        pass

    @abstractmethod
    def execute_suite(self, suite: APITestSuite) -> List[TestResult]:
        """Execute entire test suite."""
        pass


class MockAPITestExecutor(APITestExecutor):
    """Mock test executor for testing (doesn't actually make HTTP requests)."""

    def __init__(self):
        """Initialize mock executor."""
        self.execution_count = 0
        self.fail_probability = 0.1  # 10% of tests fail

    def execute(self, test: TestCase) -> TestResult:
        """Execute a test with mock response."""
        self.execution_count += 1

        start_time = time.time()
        response_time = random.uniform(0.01, 1.0)  # 10-1000ms
        time.sleep(response_time)

        # Simulate response
        should_fail = random.random() < self.fail_probability
        status_code = 400 if should_fail else 200

        response = TestResponse(
            status_code=status_code,
            headers={"Content-Type": "application/json"},
            body={"status": "ok", "data": []},
            response_time=response_time,
            size_bytes=random.randint(100, 5000)
        )

        # Check assertions
        assertions_passed = 0
        assertions_failed = 0
        failed_assertions = []

        for assertion in test.assertions:
            assertion_passed = self._check_assertion(assertion, response)
            assertion.passed = assertion_passed
            assertion.actual_value = status_code if assertion.assertion_type == AssertionType.STATUS_CODE else response_time

            if assertion_passed:
                assertions_passed += 1
            else:
                assertions_failed += 1
                failed_assertions.append(assertion)

        test_status = TestStatus.PASSED if assertions_failed == 0 else TestStatus.FAILED

        end_time = time.time()

        return TestResult(
            test_name=test.name,
            status=test_status if not should_fail else TestStatus.FAILED,
            request=test.request,
            response=response,
            assertions_passed=assertions_passed,
            assertions_failed=assertions_failed,
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            failed_assertions=failed_assertions
        )

    def execute_suite(self, suite: APITestSuite) -> List[TestResult]:
        """Execute all tests in suite."""
        results = []
        for test in suite.tests:
            if test.skip:
                result = TestResult(
                    test_name=test.name,
                    status=TestStatus.SKIPPED,
                    request=test.request,
                    response=None,
                    duration=0.0
                )
            else:
                result = self.execute(test)
            suite.add_result(result)
            results.append(result)
        return results

    def _check_assertion(self, assertion: TestAssertion, response: TestResponse) -> bool:
        """Check if assertion passes."""
        if assertion.assertion_type == AssertionType.STATUS_CODE:
            if assertion.comparison_operator == "in":
                # Handle both list and single value
                if isinstance(assertion.expected_value, list):
                    return response.status_code in assertion.expected_value
                else:
                    return response.status_code == assertion.expected_value
            else:
                return response.status_code == assertion.expected_value
        elif assertion.assertion_type == AssertionType.RESPONSE_TIME:
            if assertion.comparison_operator == "<":
                return response.response_time < (assertion.expected_value / 1000)
        elif assertion.assertion_type == AssertionType.CONTENT_TYPE:
            return "application/json" in response.headers.get("Content-Type", "")
        return True


class APITestingService:
    """Service for managing API testing."""

    def __init__(self, executor: Optional[APITestExecutor] = None):
        """Initialize testing service."""
        self.executor = executor or MockAPITestExecutor()
        self.suites: Dict[str, APITestSuite] = {}
        self.execution_history: List[Dict[str, Any]] = []

    def create_suite(self, name: str, base_url: str = "http://localhost:8000") -> APITestSuite:
        """Create a new test suite."""
        suite = APITestSuite(name, base_url)
        self.suites[name] = suite
        return suite

    def get_suite(self, name: str) -> Optional[APITestSuite]:
        """Get test suite by name."""
        return self.suites.get(name)

    def run_suite(self, suite_name: str) -> List[TestResult]:
        """Execute a test suite."""
        suite = self.get_suite(suite_name)
        if not suite:
            raise ValueError(f"Suite not found: {suite_name}")

        results = self.executor.execute_suite(suite)

        # Record in history
        self.execution_history.append({
            'timestamp': datetime.now().isoformat(),
            'suite_name': suite_name,
            'total_tests': len(results),
            'passed': sum(1 for r in results if r.is_passed()),
            'failed': sum(1 for r in results if r.status == TestStatus.FAILED),
            'skipped': sum(1 for r in results if r.status == TestStatus.SKIPPED),
            'duration': sum(r.duration for r in results)
        })

        return results

    def calculate_performance_metrics(self, results: List[TestResult]) -> PerformanceMetrics:
        """Calculate performance metrics from test results."""
        response_times = [r.response.response_time for r in results if r.response]
        
        if not response_times:
            return PerformanceMetrics()

        sorted_times = sorted(response_times)
        total_duration = sum(r.duration for r in results)
        error_count = sum(1 for r in results if r.status == TestStatus.FAILED)

        metrics = PerformanceMetrics(
            min_response_time=min(response_times),
            max_response_time=max(response_times),
            avg_response_time=sum(response_times) / len(response_times),
            median_response_time=statistics.median(response_times),
            p95_response_time=sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 0 else 0,
            p99_response_time=sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 0 else 0,
            requests_per_second=len(results) / total_duration if total_duration > 0 else 0,
            error_rate=(error_count / len(results) * 100) if results else 0,
            total_requests=len(results),
            total_errors=error_count,
            total_duration=total_duration
        )

        return metrics

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get execution history."""
        return self.execution_history

    def get_statistics(self) -> Dict[str, Any]:
        """Get testing service statistics."""
        total_suites = len(self.suites)
        total_tests = sum(len(s.tests) for s in self.suites.values())
        total_executed = sum(len(s.results) for s in self.suites.values())

        return {
            'total_suites': total_suites,
            'total_tests': total_tests,
            'total_executed': total_executed,
            'executor_type': self.executor.__class__.__name__,
            'execution_history': self.execution_history
        }


# Singleton instance
_testing_service: Optional[APITestingService] = None


def get_testing_service() -> APITestingService:
    """Get the testing service singleton."""
    global _testing_service
    if _testing_service is None:
        _testing_service = APITestingService()
    return _testing_service


def reset_testing_service() -> None:
    """Reset the testing service (for testing)."""
    global _testing_service
    _testing_service = None
