"""
Automated Test Runner Service
Orchestrates and manages test execution across backend and frontend
Phase 41: CI/CD Pipeline & Automated Deployment
"""

import logging
import asyncio
import subprocess
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Callable
from datetime import datetime
from threading import Thread, RLock
import time

logger = logging.getLogger(__name__)


class TestType(Enum):
    """Types of tests"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


class TestEnvironment(Enum):
    """Test environment"""
    LOCAL = "local"
    CI = "ci"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class TestCase:
    """Individual test case"""
    name: str
    test_type: TestType
    file_path: str
    duration_ms: float = 0.0
    status: TestStatus = TestStatus.PENDING
    error_message: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TestSuite:
    """Collection of related test cases"""
    name: str
    environment: TestEnvironment
    test_type: TestType
    test_cases: List[TestCase] = field(default_factory=list)
    total_duration_ms: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: TestStatus = TestStatus.PENDING

    def get_stats(self) -> Dict:
        """Get test suite statistics"""
        if not self.test_cases:
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "pass_rate": 0.0,
                "duration_ms": 0.0
            }
        
        total = len(self.test_cases)
        passed = sum(1 for t in self.test_cases if t.status == TestStatus.PASSED)
        failed = sum(1 for t in self.test_cases if t.status == TestStatus.FAILED)
        skipped = sum(1 for t in self.test_cases if t.status == TestStatus.SKIPPED)
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": (passed / total * 100) if total > 0 else 0.0,
            "duration_ms": self.total_duration_ms
        }


@dataclass
class TestRun:
    """Complete test run across all suites"""
    run_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    environment: TestEnvironment = TestEnvironment.LOCAL
    suites: List[TestSuite] = field(default_factory=list)
    total_duration_ms: float = 0.0
    status: TestStatus = TestStatus.PENDING
    metadata: Dict = field(default_factory=dict)

    def get_summary(self) -> Dict:
        """Get test run summary"""
        all_cases = [case for suite in self.suites for case in suite.test_cases]
        
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "environment": self.environment.value,
            "total_suites": len(self.suites),
            "total_tests": len(all_cases),
            "passed": sum(1 for c in all_cases if c.status == TestStatus.PASSED),
            "failed": sum(1 for c in all_cases if c.status == TestStatus.FAILED),
            "skipped": sum(1 for c in all_cases if c.status == TestStatus.SKIPPED),
            "pass_rate": (sum(1 for c in all_cases if c.status == TestStatus.PASSED) / len(all_cases) * 100) if all_cases else 0.0,
            "total_duration_ms": self.total_duration_ms,
            "status": self.status.value
        }


class TestRunner:
    """Executes tests and tracks results"""

    def __init__(self, timeout_seconds: int = 3600):
        self.timeout_seconds = timeout_seconds
        self.test_runs: List[TestRun] = []
        self.current_run: Optional[TestRun] = None
        self.lock = RLock()
        self.callbacks: List[Callable] = []

    def create_run(self, environment: TestEnvironment = TestEnvironment.LOCAL) -> TestRun:
        """Create a new test run"""
        import uuid
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        
        with self.lock:
            run = TestRun(
                run_id=run_id,
                environment=environment
            )
            self.current_run = run
            self.test_runs.append(run)
            return run

    def run_backend_tests(self, test_type: TestType = TestType.UNIT) -> TestSuite:
        """Run backend tests"""
        logger.info(f"Starting backend {test_type.value} tests")
        
        suite = TestSuite(
            name="Backend Tests",
            environment=self.current_run.environment if self.current_run else TestEnvironment.LOCAL,
            test_type=test_type,
            start_time=datetime.utcnow()
        )
        
        try:
            # Run pytest
            cmd = ["pytest", "backend/app/tests/", "-v", "--tb=short"]
            
            if test_type == TestType.UNIT:
                cmd.append("unit/")
            elif test_type == TestType.INTEGRATION:
                cmd.append("integration_tests.py")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )
            
            # Parse output and create test cases
            suite = self._parse_pytest_output(result.stdout, suite, "backend")
            suite.end_time = datetime.utcnow()
            
            if result.returncode == 0:
                suite.status = TestStatus.PASSED
            else:
                suite.status = TestStatus.FAILED
                logger.error(f"Backend tests failed: {result.stderr}")
            
        except subprocess.TimeoutExpired:
            suite.status = TestStatus.TIMEOUT
            logger.error(f"Backend tests timeout after {self.timeout_seconds}s")
        except Exception as e:
            suite.status = TestStatus.FAILED
            logger.error(f"Backend tests error: {e}")
        
        with self.lock:
            if self.current_run:
                self.current_run.suites.append(suite)
            self._trigger_callbacks(suite)
        
        return suite

    def run_frontend_tests(self, test_type: TestType = TestType.UNIT) -> TestSuite:
        """Run frontend tests"""
        logger.info(f"Starting frontend {test_type.value} tests")
        
        suite = TestSuite(
            name="Frontend Tests",
            environment=self.current_run.environment if self.current_run else TestEnvironment.LOCAL,
            test_type=test_type,
            start_time=datetime.utcnow()
        )
        
        try:
            # Run npm test
            cmd = ["npm", "test", "--", "--coverage", "--watchAll=false"]
            
            result = subprocess.run(
                cmd,
                cwd="frontend",
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )
            
            # Parse output and create test cases
            suite = self._parse_jest_output(result.stdout, suite, "frontend")
            suite.end_time = datetime.utcnow()
            
            if result.returncode == 0:
                suite.status = TestStatus.PASSED
            else:
                suite.status = TestStatus.FAILED
                logger.error(f"Frontend tests failed: {result.stderr}")
            
        except subprocess.TimeoutExpired:
            suite.status = TestStatus.TIMEOUT
            logger.error(f"Frontend tests timeout after {self.timeout_seconds}s")
        except Exception as e:
            suite.status = TestStatus.FAILED
            logger.error(f"Frontend tests error: {e}")
        
        with self.lock:
            if self.current_run:
                self.current_run.suites.append(suite)
            self._trigger_callbacks(suite)
        
        return suite

    def run_security_tests(self) -> TestSuite:
        """Run security scanning"""
        logger.info("Starting security tests")
        
        suite = TestSuite(
            name="Security Tests",
            environment=self.current_run.environment if self.current_run else TestEnvironment.LOCAL,
            test_type=TestType.SECURITY,
            start_time=datetime.utcnow()
        )
        
        try:
            # Run bandit for Python security
            cmd = ["bandit", "-r", "backend/app", "-f", "json"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                suite.status = TestStatus.PASSED
            else:
                suite.status = TestStatus.FAILED
                logger.warning(f"Security issues found: {result.stdout}")
            
            suite.end_time = datetime.utcnow()
            
        except Exception as e:
            suite.status = TestStatus.FAILED
            logger.error(f"Security tests error: {e}")
        
        with self.lock:
            if self.current_run:
                self.current_run.suites.append(suite)
            self._trigger_callbacks(suite)
        
        return suite

    def run_all_tests(self, environment: TestEnvironment = TestEnvironment.LOCAL) -> TestRun:
        """Run all tests"""
        run = self.create_run(environment)
        logger.info(f"Starting test run {run.run_id}")
        
        start_time = time.time()
        
        # Run test suites
        self.run_backend_tests(TestType.UNIT)
        self.run_backend_tests(TestType.INTEGRATION)
        self.run_frontend_tests(TestType.UNIT)
        self.run_security_tests()
        
        # Calculate total duration
        run.total_duration_ms = (time.time() - start_time) * 1000
        
        # Determine overall status
        if all(suite.status == TestStatus.PASSED for suite in run.suites):
            run.status = TestStatus.PASSED
        elif any(suite.status == TestStatus.FAILED for suite in run.suites):
            run.status = TestStatus.FAILED
        else:
            run.status = TestStatus.SKIPPED
        
        logger.info(f"Test run completed: {run.get_summary()}")
        return run

    def register_callback(self, callback: Callable[[TestSuite], None]) -> None:
        """Register callback for test completion"""
        with self.lock:
            self.callbacks.append(callback)

    def get_test_history(self, limit: int = 50) -> List[TestRun]:
        """Get test run history"""
        with self.lock:
            return sorted(
                self.test_runs,
                key=lambda r: r.timestamp,
                reverse=True
            )[:limit]

    def get_test_statistics(self) -> Dict:
        """Get aggregated test statistics"""
        with self.lock:
            if not self.test_runs:
                return {
                    "total_runs": 0,
                    "passed_runs": 0,
                    "failed_runs": 0,
                    "average_duration_ms": 0.0,
                    "pass_rate": 0.0
                }
            
            passed = sum(1 for r in self.test_runs if r.status == TestStatus.PASSED)
            total_duration = sum(r.total_duration_ms for r in self.test_runs)
            
            return {
                "total_runs": len(self.test_runs),
                "passed_runs": passed,
                "failed_runs": len(self.test_runs) - passed,
                "average_duration_ms": total_duration / len(self.test_runs),
                "pass_rate": (passed / len(self.test_runs) * 100) if self.test_runs else 0.0
            }

    def _parse_pytest_output(self, output: str, suite: TestSuite, component: str) -> TestSuite:
        """Parse pytest output into test cases"""
        try:
            lines = output.split('\n')
            for line in lines:
                if 'PASSED' in line or 'FAILED' in line:
                    test_name = line.split('::')[-1].split(' ')[0] if '::' in line else 'test'
                    status = TestStatus.PASSED if 'PASSED' in line else TestStatus.FAILED
                    
                    case = TestCase(
                        name=test_name,
                        test_type=suite.test_type,
                        file_path=f"{component}/{test_name}",
                        status=status
                    )
                    suite.test_cases.append(case)
        except Exception as e:
            logger.warning(f"Error parsing pytest output: {e}")
        
        return suite

    def _parse_jest_output(self, output: str, suite: TestSuite, component: str) -> TestSuite:
        """Parse Jest output into test cases"""
        try:
            lines = output.split('\n')
            for line in lines:
                if '✓' in line or '✕' in line:
                    test_name = line.split('✓')[-1].split('✕')[-1].strip()[:50]
                    status = TestStatus.PASSED if '✓' in line else TestStatus.FAILED
                    
                    case = TestCase(
                        name=test_name,
                        test_type=suite.test_type,
                        file_path=f"{component}/{test_name}",
                        status=status
                    )
                    suite.test_cases.append(case)
        except Exception as e:
            logger.warning(f"Error parsing Jest output: {e}")
        
        return suite

    def _trigger_callbacks(self, suite: TestSuite) -> None:
        """Trigger registered callbacks"""
        for callback in self.callbacks:
            try:
                callback(suite)
            except Exception as e:
                logger.error(f"Callback error: {e}")


# Global test runner instance
_runner: Optional[TestRunner] = None


def get_test_runner(timeout_seconds: int = 3600) -> TestRunner:
    """Get or create test runner instance"""
    global _runner
    if _runner is None:
        _runner = TestRunner(timeout_seconds)
    return _runner


def run_tests_async(environment: TestEnvironment = TestEnvironment.LOCAL) -> TestRun:
    """Run tests asynchronously"""
    runner = get_test_runner()
    return runner.run_all_tests(environment)
