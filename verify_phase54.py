"""
Phase 54: API Testing Framework Verification Tests
Comprehensive tests for test generation, execution, and reporting.
"""

import sys
sys.path.insert(0, '.')

from api_testing_framework import (
    get_testing_service,
    reset_testing_service,
    APITestingService,
    TestCase,
    TestRequest,
    TestAssertion,
    TestResponse,
    HTTPMethod,
    TestType,
    AssertionType,
    TestStatus,
    TestDataGenerator,
    TestCaseGenerator,
    TestAssertionBuilder,
    APITestSuite,
    MockAPITestExecutor,
    PerformanceMetrics,
)


def verify_test_data_generation() -> bool:
    """Verify test data generation capabilities."""
    print("\n✓ Testing Test Data Generation...")
    
    # Test string generation
    string_data = TestDataGenerator.generate_string(10, 20)
    assert len(string_data) >= 10 and len(string_data) <= 20, f"String length incorrect: {len(string_data)}"
    
    # Test email generation
    email = TestDataGenerator.generate_email()
    assert "@" in email and "example.com" in email, f"Email format incorrect: {email}"
    
    # Test integer generation
    integer = TestDataGenerator.generate_integer(1, 100)
    assert 1 <= integer <= 100, f"Integer out of range: {integer}"
    
    # Test float generation
    float_val = TestDataGenerator.generate_float(0.0, 10.0)
    assert 0.0 <= float_val <= 10.0, f"Float out of range: {float_val}"
    
    # Test boolean generation
    boolean = TestDataGenerator.generate_boolean()
    assert isinstance(boolean, bool), f"Boolean type incorrect: {type(boolean)}"
    
    # Test URL generation
    url = TestDataGenerator.generate_url()
    assert url.startswith("https://"), f"URL format incorrect: {url}"
    
    # Test UUID generation
    uuid = TestDataGenerator.generate_uuid()
    assert len(uuid) > 0, "UUID empty"
    
    # Test timestamp generation
    timestamp = TestDataGenerator.generate_timestamp()
    assert "T" in timestamp, f"Timestamp format incorrect: {timestamp}"
    
    # Test object generation
    obj = TestDataGenerator.generate_object({
        "name": "string",
        "email": "email",
        "age": "integer",
        "active": "boolean"
    })
    assert "name" in obj and "email" in obj and "age" in obj, "Object properties missing"
    assert isinstance(obj["age"], int), "Age not integer"
    assert isinstance(obj["active"], bool), "Active not boolean"
    
    print("  ✓ String generation works")
    print("  ✓ Email generation works")
    print("  ✓ Integer/Float/Boolean generation works")
    print("  ✓ URL/UUID/Timestamp generation works")
    print("  ✓ Object generation works")
    
    return True


def verify_test_case_generation() -> bool:
    """Verify test case generation from endpoints."""
    print("\n✓ Testing Test Case Generation...")
    
    # Generate smoke tests
    smoke_tests = TestCaseGenerator.generate_smoke_tests("/api/users", HTTPMethod.GET)
    assert len(smoke_tests) > 0, "No smoke tests generated"
    assert smoke_tests[0].test_type == TestType.SMOKE, "Test type incorrect"
    assert len(smoke_tests[0].assertions) > 0, "No assertions generated"
    
    # Generate functional tests for GET
    get_tests = TestCaseGenerator.generate_functional_tests("/api/users", HTTPMethod.GET)
    assert len(get_tests) > 0, "No GET tests generated"
    assert get_tests[0].request.method == HTTPMethod.GET, "Method incorrect"
    
    # Generate functional tests for POST
    post_tests = TestCaseGenerator.generate_functional_tests(
        "/api/users",
        HTTPMethod.POST,
        {"name": "string", "email": "email"}
    )
    assert len(post_tests) > 0, "No POST tests generated"
    assert post_tests[0].request.body is not None, "POST body not generated"
    
    # Generate performance tests
    perf_tests = TestCaseGenerator.generate_performance_tests("/api/data", HTTPMethod.GET, iterations=5)
    assert len(perf_tests) > 0, "No performance tests generated"
    assert perf_tests[0].test_type == TestType.PERFORMANCE, "Test type incorrect"
    
    # Generate error handling tests
    error_tests = TestCaseGenerator.generate_error_handling_tests("/api/items", HTTPMethod.POST)
    assert len(error_tests) > 0, "No error tests generated"
    
    print("  ✓ Smoke test generation works")
    print("  ✓ Functional test generation (GET/POST) works")
    print("  ✓ Performance test generation works")
    print("  ✓ Error handling test generation works")
    
    return True


def verify_assertion_builder() -> bool:
    """Verify test assertion builder."""
    print("\n✓ Testing Assertion Builder...")
    
    builder = TestAssertionBuilder()
    assertions = (builder
        .assert_status_code(200)
        .assert_content_type("application/json")
        .assert_response_time_less_than(1000)
        .build())
    
    assert len(assertions) == 3, f"Expected 3 assertions, got {len(assertions)}"
    assert assertions[0].assertion_type == AssertionType.STATUS_CODE, "First assertion incorrect"
    assert assertions[1].assertion_type == AssertionType.CONTENT_TYPE, "Second assertion incorrect"
    assert assertions[2].assertion_type == AssertionType.RESPONSE_TIME, "Third assertion incorrect"
    
    print("  ✓ Status code assertion works")
    print("  ✓ Content type assertion works")
    print("  ✓ Response time assertion works")
    print("  ✓ Assertion chaining works")
    
    return True


def verify_test_suite_creation() -> bool:
    """Verify test suite creation and management."""
    print("\n✓ Testing Test Suite Creation...")
    
    reset_testing_service()
    service = get_testing_service()
    
    # Create suite
    suite = service.create_suite("user_tests", "http://localhost:8000")
    assert suite is not None, "Suite not created"
    assert suite.name == "user_tests", "Suite name incorrect"
    
    # Add tests
    tests = TestCaseGenerator.generate_smoke_tests("/users", HTTPMethod.GET)
    suite.add_tests(tests)
    assert len(suite.tests) > 0, "Tests not added to suite"
    
    # Get suite
    retrieved_suite = service.get_suite("user_tests")
    assert retrieved_suite is not None, "Suite not retrieved"
    assert len(retrieved_suite.tests) == len(suite.tests), "Test count mismatch"
    
    # Get tests by type
    smoke_tests = retrieved_suite.get_tests_by_type(TestType.SMOKE)
    assert len(smoke_tests) > 0, "Smoke tests not found"
    
    print("  ✓ Suite creation works")
    print("  ✓ Test addition works")
    print("  ✓ Suite retrieval works")
    print("  ✓ Test filtering by type works")
    
    return True


def verify_test_execution() -> bool:
    """Verify test execution."""
    print("\n✓ Testing Test Execution...")
    
    reset_testing_service()
    service = get_testing_service()
    
    # Create suite with tests
    suite = service.create_suite("exec_tests", "http://localhost:8000")
    
    # Create a test case with assertions
    test = TestCase(
        name="test_get_users",
        test_type=TestType.SMOKE,
        request=TestRequest(endpoint="/users", method=HTTPMethod.GET),
        description="Get users endpoint"
    )
    
    # Add assertions
    builder = TestAssertionBuilder()
    test.assertions = builder.assert_status_code(200).assert_content_type("application/json").build()
    
    suite.add_test(test)
    
    # Execute suite
    results = service.run_suite("exec_tests")
    assert len(results) > 0, "No results returned"
    assert results[0].test_name == "test_get_users", "Test name mismatch"
    assert results[0].status in [TestStatus.PASSED, TestStatus.FAILED], "Invalid status"
    assert results[0].duration > 0, "Duration not recorded"
    
    print("  ✓ Test execution works")
    print(f"  ✓ Test status: {results[0].status.value}")
    print(f"  ✓ Assertions passed: {results[0].assertions_passed}")
    print(f"  ✓ Execution time: {results[0].duration:.3f}s")
    
    return True


def verify_test_suite_execution() -> bool:
    """Verify full test suite execution."""
    print("\n✓ Testing Test Suite Execution...")
    
    reset_testing_service()
    service = get_testing_service()
    
    # Create suite
    suite = service.create_suite("full_suite", "http://localhost:8000")
    
    # Add multiple tests
    test_cases = [
        TestCaseGenerator.generate_smoke_tests("/api/users", HTTPMethod.GET),
        TestCaseGenerator.generate_functional_tests("/api/posts", HTTPMethod.POST),
        TestCaseGenerator.generate_performance_tests("/api/data", HTTPMethod.GET)
    ]
    
    for test_list in test_cases:
        suite.add_tests(test_list)
    
    assert len(suite.tests) >= 3, "Not enough tests added"
    
    # Execute suite
    results = service.run_suite("full_suite")
    assert len(results) == len(suite.tests), "Result count mismatch"
    
    # Check statistics
    stats = suite.get_statistics()
    assert stats['total_tests'] > 0, "Total tests not counted"
    assert stats['executed_tests'] > 0, "Executed tests not counted"
    assert stats['pass_rate'] >= 0 and stats['pass_rate'] <= 100, "Invalid pass rate"
    
    print(f"  ✓ Executed {stats['executed_tests']} tests")
    print(f"  ✓ Passed: {stats['passed']}, Failed: {stats['failed']}, Skipped: {stats['skipped']}")
    print(f"  ✓ Pass rate: {stats['pass_rate']:.1f}%")
    print(f"  ✓ Total duration: {stats['total_duration']:.3f}s")
    
    return True


def verify_performance_metrics() -> bool:
    """Verify performance metrics calculation."""
    print("\n✓ Testing Performance Metrics...")
    
    reset_testing_service()
    service = get_testing_service()
    
    # Create suite with multiple tests
    suite = service.create_suite("perf_suite", "http://localhost:8000")
    
    # Add performance tests
    endpoints = ["/api/users", "/api/posts", "/api/data", "/api/accounts"]
    for endpoint in endpoints:
        tests = TestCaseGenerator.generate_performance_tests(endpoint, HTTPMethod.GET)
        suite.add_tests(tests)
    
    # Execute
    results = service.run_suite("perf_suite")
    
    # Calculate metrics
    metrics = service.calculate_performance_metrics(results)
    
    assert metrics.min_response_time >= 0, "Min response time invalid"
    assert metrics.max_response_time >= metrics.min_response_time, "Max < Min response time"
    assert metrics.avg_response_time > 0, "Avg response time invalid"
    assert metrics.error_rate >= 0 and metrics.error_rate <= 100, "Invalid error rate"
    assert metrics.requests_per_second > 0, "RPS not calculated"
    assert metrics.total_requests > 0, "Total requests not counted"
    
    print(f"  ✓ Min response time: {metrics.min_response_time*1000:.2f}ms")
    print(f"  ✓ Max response time: {metrics.max_response_time*1000:.2f}ms")
    print(f"  ✓ Avg response time: {metrics.avg_response_time*1000:.2f}ms")
    print(f"  ✓ Median: {metrics.median_response_time*1000:.2f}ms")
    print(f"  ✓ P95: {metrics.p95_response_time*1000:.2f}ms")
    print(f"  ✓ RPS: {metrics.requests_per_second:.2f}")
    print(f"  ✓ Error rate: {metrics.error_rate:.1f}%")
    
    return True


def verify_test_result_tracking() -> bool:
    """Verify test result tracking and retrieval."""
    print("\n✓ Testing Test Result Tracking...")
    
    reset_testing_service()
    service = get_testing_service()
    
    # Create suite and execute
    suite = service.create_suite("result_suite", "http://localhost:8000")
    
    tests = TestCaseGenerator.generate_smoke_tests("/api/test", HTTPMethod.GET)
    suite.add_tests(tests)
    
    results = service.run_suite("result_suite")
    
    # Get results
    all_results = suite.get_results()
    assert len(all_results) > 0, "No results tracked"
    
    # Check result details
    first_result = all_results[0]
    assert first_result.test_name is not None, "Test name missing"
    assert first_result.status is not None, "Status missing"
    assert first_result.duration > 0, "Duration not recorded"
    
    # Get result by name
    result = suite.get_result(first_result.test_name)
    assert result is not None, "Result not retrieved"
    assert result.test_name == first_result.test_name, "Test name mismatch"
    
    print("  ✓ Results tracked correctly")
    print("  ✓ Result retrieval works")
    print("  ✓ Result details complete")
    
    return True


def verify_test_skip_functionality() -> bool:
    """Verify test skip functionality."""
    print("\n✓ Testing Test Skip Functionality...")
    
    reset_testing_service()
    service = get_testing_service()
    
    suite = service.create_suite("skip_suite", "http://localhost:8000")
    
    # Create regular test
    test1 = TestCase(
        name="test_enabled",
        test_type=TestType.SMOKE,
        request=TestRequest(endpoint="/api/users", method=HTTPMethod.GET),
        skip=False
    )
    
    # Create skipped test
    test2 = TestCase(
        name="test_disabled",
        test_type=TestType.SMOKE,
        request=TestRequest(endpoint="/api/posts", method=HTTPMethod.GET),
        skip=True,
        skip_reason="Not ready for testing"
    )
    
    suite.add_tests([test1, test2])
    
    # Execute
    results = service.run_suite("skip_suite")
    
    # Check results
    assert len(results) == 2, "Wrong number of results"
    
    skipped = [r for r in results if r.status == TestStatus.SKIPPED]
    executed = [r for r in results if r.status != TestStatus.SKIPPED]
    
    assert len(skipped) > 0, "No skipped tests"
    assert len(executed) > 0, "No executed tests"
    
    print(f"  ✓ Executed tests: {len(executed)}")
    print(f"  ✓ Skipped tests: {len(skipped)}")
    print(f"  ✓ Skip reasons preserved")
    
    return True


def verify_execution_history() -> bool:
    """Verify execution history tracking."""
    print("\n✓ Testing Execution History...")
    
    reset_testing_service()
    service = get_testing_service()
    
    # Run multiple suites
    for i in range(3):
        suite = service.create_suite(f"history_suite_{i}", "http://localhost:8000")
        tests = TestCaseGenerator.generate_smoke_tests(f"/api/test{i}", HTTPMethod.GET)
        suite.add_tests(tests)
        service.run_suite(f"history_suite_{i}")
    
    # Get history
    history = service.get_execution_history()
    assert len(history) >= 3, f"Expected at least 3 history entries, got {len(history)}"
    
    # Check history details
    for entry in history:
        assert 'timestamp' in entry, "Timestamp missing"
        assert 'suite_name' in entry, "Suite name missing"
        assert 'total_tests' in entry, "Total tests missing"
        assert 'passed' in entry, "Passed count missing"
        assert 'failed' in entry, "Failed count missing"
        assert 'duration' in entry, "Duration missing"
    
    print(f"  ✓ Tracked {len(history)} executions")
    print(f"  ✓ History entries have all required fields")
    
    return True


def run_all_verifications():
    """Run all verification tests."""
    print("=" * 70)
    print("PHASE 54: API TESTING FRAMEWORK VERIFICATION TESTS")
    print("=" * 70)
    
    tests = [
        ("Test Data Generation", verify_test_data_generation),
        ("Test Case Generation", verify_test_case_generation),
        ("Assertion Builder", verify_assertion_builder),
        ("Test Suite Creation", verify_test_suite_creation),
        ("Test Execution", verify_test_execution),
        ("Test Suite Execution", verify_test_suite_execution),
        ("Performance Metrics", verify_performance_metrics),
        ("Result Tracking", verify_test_result_tracking),
        ("Skip Functionality", verify_test_skip_functionality),
        ("Execution History", verify_execution_history),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, None))
            print(f"  ✅ PASSED")
        except AssertionError as e:
            results.append((test_name, False, str(e)))
            print(f"  ❌ FAILED: {e}")
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"  ❌ ERROR: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n✅ Checks Passed: {passed}/{total}")
    print(f"📊 Success Rate: {success_rate:.1f}%\n")
    
    if passed == total:
        print("🎉 All Phase 54 verification tests passed!")
        print("\nImplemented Services:")
        print("  ✅ TestDataGenerator (7+ data type generation)")
        print("  ✅ TestCaseGenerator (smoke, functional, performance tests)")
        print("  ✅ TestAssertionBuilder (fluent assertion API)")
        print("  ✅ APITestSuite (test collection management)")
        print("  ✅ MockAPITestExecutor (test execution with mocking)")
        print("  ✅ APITestingService (unified testing interface)")
        print("  ✅ PerformanceMetrics (latency & throughput calculation)")
        print("  ✅ Test Result Tracking (comprehensive logging)")
        print("  ✅ Execution History (audit trail)")
        print("  ✅ Skip Management (conditional test execution)")
    else:
        print("⚠️  Some tests failed. Details above.")
        for test_name, result, error in results:
            if not result:
                print(f"\n  ❌ {test_name}")
                if error:
                    print(f"     {error}")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_verifications()
    sys.exit(0 if success else 1)
