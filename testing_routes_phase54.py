"""
Phase 54: API Testing Routes
FastAPI endpoints for test management, execution, and reporting.
"""

from fastapi import APIRouter, HTTPException, Query, Body, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from api_testing_framework import (
    get_testing_service,
    reset_testing_service,
    APITestingService,
    APITestSuite,
    TestCase,
    TestRequest,
    TestAssertion,
    HTTPMethod,
    TestType,
    AssertionType,
    TestDataGenerator,
    TestCaseGenerator,
    TestAssertionBuilder,
    PerformanceMetrics,
    TestResult,
    TestStatus,
)

router = APIRouter(prefix="/api/v1/testing", tags=["api-testing"])


# Pydantic Models for Request/Response
class AssertionRequest(BaseModel):
    """Request model for test assertion."""
    assertion_type: str
    expected_value: Any
    comparison_operator: str = "=="


class TestRequestModel(BaseModel):
    """Request model for API call in test."""
    endpoint: str
    method: str  # GET, POST, PUT, DELETE, etc.
    headers: Dict[str, str] = {}
    query_params: Dict[str, Any] = {}
    body: Optional[Dict[str, Any]] = None


class TestCaseRequest(BaseModel):
    """Request model for creating test case."""
    name: str
    test_type: str  # smoke, functional, integration, performance, security
    request: TestRequestModel
    assertions: List[AssertionRequest] = []
    description: str = ""
    tags: List[str] = []
    requires_auth: bool = False
    timeout: int = 30
    skip: bool = False


class TestSuiteRequest(BaseModel):
    """Request model for creating test suite."""
    name: str
    base_url: str = "http://localhost:8000"
    description: str = ""


class TestResultResponse(BaseModel):
    """Response model for test result."""
    test_name: str
    status: str
    duration: float
    assertions_passed: int
    assertions_failed: int
    error_message: str = ""
    timestamp: str


class TestSuiteResultResponse(BaseModel):
    """Response model for test suite execution."""
    suite_name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    pass_rate: float
    total_duration: float
    timestamp: str
    results: List[TestResultResponse]


class PerformanceMetricsResponse(BaseModel):
    """Response model for performance metrics."""
    min_response_time: float
    max_response_time: float
    avg_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    total_requests: int
    total_errors: int
    total_duration: float


# Helper functions
def convert_test_request_model(req: TestRequestModel) -> TestRequest:
    """Convert request model to domain object."""
    return TestRequest(
        endpoint=req.endpoint,
        method=HTTPMethod[req.method.upper()],
        headers=req.headers,
        query_params=req.query_params,
        body=req.body
    )


def test_result_to_response(result: TestResult) -> TestResultResponse:
    """Convert test result to response model."""
    return TestResultResponse(
        test_name=result.test_name,
        status=result.status.value,
        duration=result.duration,
        assertions_passed=result.assertions_passed,
        assertions_failed=result.assertions_failed,
        error_message=result.error_message,
        timestamp=datetime.now().isoformat()
    )


@router.post("/suites", response_model=Dict[str, Any])
async def create_test_suite(request: TestSuiteRequest) -> Dict[str, Any]:
    """
    Create a new test suite.
    
    A test suite is a collection of test cases that can be executed together.
    """
    try:
        service = get_testing_service()
        suite = service.create_suite(request.name, request.base_url)
        
        return {
            "status": "success",
            "message": f"Test suite '{request.name}' created",
            "suite_name": request.name,
            "base_url": request.base_url,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suites")
async def list_test_suites() -> Dict[str, Any]:
    """List all test suites."""
    service = get_testing_service()
    suites = service.suites
    
    return {
        "total_suites": len(suites),
        "suites": [
            {
                "name": name,
                "base_url": suite.base_url,
                "test_count": len(suite.tests),
                "result_count": len(suite.results),
                "created_at": suite.created_at.isoformat()
            }
            for name, suite in suites.items()
        ],
        "timestamp": datetime.now().isoformat()
    }


@router.post("/suites/{suite_name}/tests")
async def add_test_to_suite(
    suite_name: str,
    test: TestCaseRequest
) -> Dict[str, Any]:
    """
    Add a test case to a test suite.
    
    Define individual test cases with assertions to validate API behavior.
    """
    try:
        service = get_testing_service()
        suite = service.get_suite(suite_name)
        
        if not suite:
            raise HTTPException(status_code=404, detail=f"Suite not found: {suite_name}")
        
        # Convert request to domain objects
        test_request = convert_test_request_model(test.request)
        
        # Build assertions
        assertions = []
        for assertion in test.assertions:
            try:
                assertion_type = AssertionType[assertion.assertion_type.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid assertion type: {assertion.assertion_type}"
                )
            
            assertions.append(TestAssertion(
                assertion_type=assertion_type,
                expected_value=assertion.expected_value,
                comparison_operator=assertion.comparison_operator
            ))
        
        # Create test case
        try:
            test_type = TestType[test.test_type.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid test type: {test.test_type}"
            )
        
        test_case = TestCase(
            name=test.name,
            test_type=test_type,
            request=test_request,
            assertions=assertions,
            description=test.description,
            tags=test.tags,
            requires_auth=test.requires_auth,
            timeout=test.timeout,
            skip=test.skip
        )
        
        suite.add_test(test_case)
        
        return {
            "status": "success",
            "message": f"Test '{test.name}' added to suite '{suite_name}'",
            "test_name": test.name,
            "total_tests_in_suite": len(suite.tests),
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suites/{suite_name}/tests")
async def get_suite_tests(suite_name: str) -> Dict[str, Any]:
    """Get all tests in a suite."""
    service = get_testing_service()
    suite = service.get_suite(suite_name)
    
    if not suite:
        raise HTTPException(status_code=404, detail=f"Suite not found: {suite_name}")
    
    return {
        "suite_name": suite_name,
        "total_tests": len(suite.tests),
        "tests": [
            {
                "name": t.name,
                "type": t.test_type.value,
                "method": t.request.method.value,
                "endpoint": t.request.endpoint,
                "assertions_count": len(t.assertions),
                "skip": t.skip,
                "tags": t.tags
            }
            for t in suite.tests
        ],
        "timestamp": datetime.now().isoformat()
    }


@router.post("/suites/{suite_name}/execute")
async def execute_test_suite(suite_name: str, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Execute all tests in a suite.
    
    Runs all test cases and collects results with performance metrics.
    """
    try:
        service = get_testing_service()
        suite = service.get_suite(suite_name)
        
        if not suite:
            raise HTTPException(status_code=404, detail=f"Suite not found: {suite_name}")
        
        if not suite.tests:
            raise HTTPException(status_code=400, detail="No tests in suite")
        
        # Execute suite
        results = service.run_suite(suite_name)
        
        # Calculate metrics
        metrics = service.calculate_performance_metrics(results)
        
        # Get statistics
        stats = suite.get_statistics()
        
        return {
            "status": "success",
            "suite_name": suite_name,
            "execution_summary": {
                "total_tests": stats['total_tests'],
                "executed": len(results),
                "passed": stats['passed'],
                "failed": stats['failed'],
                "skipped": stats['skipped'],
                "pass_rate": f"{stats['pass_rate']:.1f}%",
                "total_duration": stats['total_duration']
            },
            "performance_metrics": metrics.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suites/{suite_name}/results")
async def get_suite_results(
    suite_name: str,
    status: Optional[str] = Query(None, description="Filter by test status (passed, failed, skipped)")
) -> Dict[str, Any]:
    """Get all test results from a suite execution."""
    service = get_testing_service()
    suite = service.get_suite(suite_name)
    
    if not suite:
        raise HTTPException(status_code=404, detail=f"Suite not found: {suite_name}")
    
    results = suite.get_results()
    
    # Filter by status if provided
    if status:
        try:
            status_enum = TestStatus[status.upper()]
            results = [r for r in results if r.status == status_enum]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    return {
        "suite_name": suite_name,
        "total_results": len(results),
        "results": [
            {
                "test_name": r.test_name,
                "status": r.status.value,
                "duration": r.duration,
                "assertions_passed": r.assertions_passed,
                "assertions_failed": r.assertions_failed,
                "response_time": r.response.response_time if r.response else 0
            }
            for r in results
        ],
        "timestamp": datetime.now().isoformat()
    }


@router.post("/generate-tests")
async def generate_tests(
    endpoint: str = Query(..., description="API endpoint to test"),
    method: str = Query("GET", description="HTTP method"),
    test_types: List[str] = Query(["smoke", "functional"], description="Types of tests to generate")
) -> Dict[str, Any]:
    """
    Auto-generate test cases for an endpoint.
    
    Generates smoke, functional, and performance tests based on endpoint definition.
    """
    try:
        # Validate method
        try:
            http_method = HTTPMethod[method.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid HTTP method: {method}")
        
        generated_tests = []
        
        for test_type in test_types:
            if test_type.lower() == "smoke":
                generated_tests.extend(TestCaseGenerator.generate_smoke_tests(endpoint, http_method))
            elif test_type.lower() == "functional":
                generated_tests.extend(TestCaseGenerator.generate_functional_tests(endpoint, http_method))
            elif test_type.lower() == "performance":
                generated_tests.extend(TestCaseGenerator.generate_performance_tests(endpoint, http_method))
            elif test_type.lower() == "error":
                generated_tests.extend(TestCaseGenerator.generate_error_handling_tests(endpoint, http_method))
        
        return {
            "status": "success",
            "endpoint": endpoint,
            "method": method,
            "generated_tests": len(generated_tests),
            "tests": [
                {
                    "name": t.name,
                    "type": t.test_type.value,
                    "description": t.description,
                    "assertions": len(t.assertions)
                }
                for t in generated_tests
            ],
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-test-data")
async def generate_test_data(
    properties: Dict[str, str] = Body(..., description="Properties to generate: {name: type}")
) -> Dict[str, Any]:
    """
    Generate test data for API requests.
    
    Supports: string, integer, float, boolean, email, url, uuid, timestamp
    """
    try:
        if not properties:
            raise HTTPException(status_code=400, detail="Properties cannot be empty")
        
        # Generate test data
        test_data = TestDataGenerator.generate_object(properties)
        
        return {
            "status": "success",
            "generated_data": test_data,
            "data_types": properties,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-data-types")
async def get_test_data_types() -> Dict[str, Any]:
    """Get available test data types."""
    return {
        "available_types": {
            "string": "Random string (1-100 chars)",
            "integer": "Random integer (0-1000)",
            "float": "Random float (0.0-1000.0)",
            "boolean": "Random boolean (true/false)",
            "email": "Random email address",
            "url": "Random URL",
            "uuid": "Random UUID",
            "timestamp": "ISO timestamp"
        },
        "example": {
            "name": "string",
            "email": "email",
            "age": "integer",
            "active": "boolean"
        },
        "timestamp": datetime.now().isoformat()
    }


@router.get("/assertion-types")
async def get_assertion_types() -> Dict[str, Any]:
    """Get available assertion types."""
    return {
        "assertion_types": [
            {
                "type": "status_code",
                "description": "Verify HTTP status code",
                "example": {"assertion_type": "status_code", "expected_value": 200}
            },
            {
                "type": "response_field",
                "description": "Verify response field value",
                "example": {"assertion_type": "response_field", "expected_value": {"path": "data.id", "value": 123}}
            },
            {
                "type": "response_time",
                "description": "Verify response time (in milliseconds)",
                "example": {"assertion_type": "response_time", "expected_value": 1000, "comparison_operator": "<"}
            },
            {
                "type": "content_type",
                "description": "Verify response content type",
                "example": {"assertion_type": "content_type", "expected_value": "application/json"}
            },
            {
                "type": "header_exists",
                "description": "Verify response header exists",
                "example": {"assertion_type": "header_exists", "expected_value": "X-Request-ID"}
            },
            {
                "type": "body_contains",
                "description": "Verify response body contains text",
                "example": {"assertion_type": "body_contains", "expected_value": "success"}
            }
        ],
        "timestamp": datetime.now().isoformat()
    }


@router.get("/statistics")
async def get_testing_statistics() -> Dict[str, Any]:
    """Get testing service statistics."""
    service = get_testing_service()
    stats = service.get_statistics()
    
    return {
        "total_suites": stats['total_suites'],
        "total_tests": stats['total_tests'],
        "total_executed": stats['total_executed'],
        "executor_type": stats['executor_type'],
        "execution_history": stats['execution_history'],
        "timestamp": datetime.now().isoformat()
    }


@router.post("/clear")
async def clear_testing_data() -> Dict[str, str]:
    """Clear all test suites and results."""
    reset_testing_service()
    return {
        "status": "success",
        "message": "All test data cleared",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/health")
async def health() -> Dict[str, Any]:
    """Health check for testing service."""
    service = get_testing_service()
    stats = service.get_statistics()
    
    return {
        "status": "healthy",
        "service": "API Testing Service",
        "version": "1.0.0",
        "test_suites": stats['total_suites'],
        "total_tests": stats['total_tests'],
        "timestamp": datetime.now().isoformat()
    }


# Export router
__all__ = ['router']
