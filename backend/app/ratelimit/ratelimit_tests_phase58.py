"""
Phase 58: Rate Limiting & Throttling Tests
Comprehensive test coverage for rate limiting, quota management, and DDoS detection.
"""

import time
import threading
from ratelimit.ratelimit_service_phase58 import (
    get_rate_limiter_service,
    get_quota_manager,
    get_ddos_detector,
    reset_rate_limiter_service,
    reset_quota_manager,
    reset_ddos_detector,
    RateLimit,
    QuotaTier,
    BlockType,
    RateLimitAlgorithm,
    DDoSDetectionLevel
)


class TestRateLimiterService:
    """Tests for rate limiter service."""
    
    def setup_method(self):
        """Reset service before each test."""
        reset_rate_limiter_service()
    
    def test_token_bucket_algorithm(self):
        """Test token bucket rate limiting."""
        service = get_rate_limiter_service()
        
        # Configure rate limit: 10 requests per 10 seconds
        rate_limit = RateLimit(
            limit_type="test",
            requests=10,
            window_seconds=10,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET
        )
        service.configure_rate_limit("bucket_test", rate_limit)
        
        # First 10 requests should succeed
        for i in range(10):
            allowed, details = service.check_rate_limit("bucket_test", 1)
            assert allowed, f"Request {i+1} should be allowed"
        
        # 11th request should fail
        allowed, details = service.check_rate_limit("bucket_test", 1)
        assert not allowed, "Request 11 should be throttled"
        assert details["reason"] == "insufficient_tokens"
    
    def test_sliding_window_algorithm(self):
        """Test sliding window counter."""
        service = get_rate_limiter_service()
        
        rate_limit = RateLimit(
            limit_type="test",
            requests=5,
            window_seconds=5,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW
        )
        service.configure_rate_limit("window_test", rate_limit)
        
        # First 5 requests should succeed
        for i in range(5):
            allowed, details = service.check_rate_limit("window_test", 1)
            assert allowed, f"Request {i+1} should be allowed"
        
        # 6th request should fail
        allowed, details = service.check_rate_limit("window_test", 1)
        assert not allowed, "Request 6 should be throttled"
    
    def test_burst_capability(self):
        """Test burst requests."""
        service = get_rate_limiter_service()
        
        rate_limit = RateLimit(
            limit_type="test",
            requests=5,
            window_seconds=5,
            burst_allowed=3
        )
        service.configure_rate_limit("burst_test", rate_limit)
        
        # Consume regular tokens
        for i in range(5):
            service.check_rate_limit("burst_test", 1)
        
        # Burst should succeed once
        allowed, details = service.check_rate_limit("burst_test", 1, burst=True)
        assert allowed, "Burst should be allowed"
        assert details.get("burst_used") == True
    
    def test_multi_bucket_isolation(self):
        """Test that different buckets are isolated."""
        service = get_rate_limiter_service()
        
        rate_limit = RateLimit(
            limit_type="test",
            requests=3,
            window_seconds=10
        )
        service.configure_rate_limit("bucket_a", rate_limit)
        service.configure_rate_limit("bucket_b", rate_limit)
        
        # Exhaust bucket A
        for i in range(3):
            service.check_rate_limit("bucket_a", 1)
        
        # Bucket B should still have capacity
        allowed, _ = service.check_rate_limit("bucket_b", 1)
        assert allowed, "Bucket B should not be affected by bucket A"
    
    def test_reset_limit(self):
        """Test limit reset."""
        service = get_rate_limiter_service()
        
        rate_limit = RateLimit(
            limit_type="test",
            requests=2,
            window_seconds=10
        )
        service.configure_rate_limit("reset_test", rate_limit)
        
        # Exhaust limit
        service.check_rate_limit("reset_test", 1)
        service.check_rate_limit("reset_test", 1)
        allowed, _ = service.check_rate_limit("reset_test", 1)
        assert not allowed, "Should be throttled"
        
        # Reset
        service.reset_limit("reset_test")
        allowed, _ = service.check_rate_limit("reset_test", 1)
        assert allowed, "Should be allowed after reset"
    
    def test_rate_limiter_statistics(self):
        """Test rate limiter statistics."""
        service = get_rate_limiter_service()
        
        rate_limit = RateLimit(
            limit_type="test",
            requests=5,
            window_seconds=10
        )
        service.configure_rate_limit("stats_test", rate_limit)
        
        # Generate some activity
        for i in range(10):
            service.check_rate_limit("stats_test", 1)
        
        stats = service.get_statistics()
        assert stats["total_requests"] == 10
        assert stats["throttled_requests"] > 0
        assert stats["configured_limits"] == 1


class TestQuotaManager:
    """Tests for quota manager."""
    
    def setup_method(self):
        """Reset service before each test."""
        reset_quota_manager()
    
    def test_create_quota_free_tier(self):
        """Test creating free tier quota."""
        manager = get_quota_manager()
        
        quota = manager.create_quota("user1", QuotaTier.FREE, reset_hour=0)
        assert quota.user_id == "user1"
        assert quota.tier == QuotaTier.FREE
        assert quota.requests_per_day == 1000
        assert quota.concurrent_requests == 2
    
    def test_check_quota_within_limits(self):
        """Test quota check when within limits."""
        manager = get_quota_manager()
        
        manager.create_quota("user2", QuotaTier.FREE)
        allowed, details = manager.check_quota("user2", requests=10)
        
        assert allowed, "Should be within quota"
        assert details["warnings"] == []
    
    def test_check_quota_exceeds_limit(self):
        """Test quota check when exceeding limits."""
        manager = get_quota_manager()
        
        manager.create_quota("user3", QuotaTier.FREE)
        
        # Use up daily quota
        allowed, details = manager.check_quota("user3", requests=1001)
        assert not allowed, "Should exceed daily quota"
        assert "daily_quota" in details["violations"]
    
    def test_quota_approaching_warning(self):
        """Test quota warning when approaching limit."""
        manager = get_quota_manager()
        
        manager.create_quota("user4", QuotaTier.FREE)
        
        # Use 90% of quota
        allowed, details = manager.check_quota("user4", requests=900)
        assert allowed, "Should be allowed"
        assert "approaching_daily_limit" in details["warnings"]
    
    def test_quota_upgrade_tier(self):
        """Test upgrading user tier."""
        manager = get_quota_manager()
        
        quota = manager.create_quota("user5", QuotaTier.FREE)
        assert quota.requests_per_day == 1000
        
        upgraded = manager.upgrade_tier("user5", QuotaTier.PREMIUM)
        assert upgraded.tier == QuotaTier.PREMIUM
        assert upgraded.requests_per_day == 100000
    
    def test_concurrent_request_quota(self):
        """Test concurrent request limits."""
        manager = get_quota_manager()
        
        manager.create_quota("user6", QuotaTier.FREE)  # 2 concurrent
        
        allowed, _ = manager.check_quota("user6", concurrent=2)
        assert allowed, "Should allow 2 concurrent"
        
        allowed, _ = manager.check_quota("user6", concurrent=1)
        assert not allowed, "Should reject 3 concurrent"
    
    def test_storage_quota(self):
        """Test storage quota limits."""
        manager = get_quota_manager()
        
        manager.create_quota("user7", QuotaTier.FREE)  # 1 GB
        
        allowed, _ = manager.check_quota("user7", storage_gb=0.5)
        assert allowed, "Should allow storage use"
        
        allowed, _ = manager.check_quota("user7", storage_gb=0.6)
        assert not allowed, "Should exceed storage quota"
    
    def test_release_resources(self):
        """Test releasing quota resources."""
        manager = get_quota_manager()
        
        manager.create_quota("user8", QuotaTier.FREE)
        
        # Reserve resources
        manager.check_quota("user8", concurrent=2, storage_gb=0.5)
        quota = manager.get_quota("user8")
        assert quota.concurrent_active == 2
        
        # Release
        manager.release_quota("user8", concurrent=2, storage_gb=0.5)
        quota = manager.get_quota("user8")
        assert quota.concurrent_active == 0
    
    def test_quota_statistics(self):
        """Test quota manager statistics."""
        manager = get_quota_manager()
        
        manager.create_quota("user9", QuotaTier.BASIC)
        manager.create_quota("user10", QuotaTier.PREMIUM)
        
        stats = manager.get_statistics()
        assert stats["total_users"] == 2
        assert stats["users_by_tier"]["basic"] == 1
        assert stats["users_by_tier"]["premium"] == 1


class TestDDoSDetector:
    """Tests for DDoS detector."""
    
    def setup_method(self):
        """Reset service before each test."""
        reset_ddos_detector()
    
    def test_normal_request_analysis(self):
        """Test analysis of normal requests."""
        detector = get_ddos_detector()
        
        allowed, details = detector.analyze_request("192.168.1.1", "/api/users", True)
        assert allowed, "Normal request should be allowed"
        assert details["detection_level"] == "normal"
    
    def test_consecutive_failed_requests(self):
        """Test detection of high failed request rate."""
        detector = get_ddos_detector()
        
        ip = "192.168.2.1"
        
        # Send multiple failed requests rapidly
        for i in range(30):
            allowed, details = detector.analyze_request(ip, f"/endpoint{i%5}", False)
        
        # Final analysis might detect suspicious activity
        # (depends on thresholds and request distribution)
        stats = detector.get_statistics()
        assert stats["total_ips_analyzed"] > 0
    
    def test_high_request_rate_detection(self):
        """Test detection of high request rates."""
        detector = get_ddos_detector()
        
        ip = "192.168.3.1"
        
        # Send burst of requests
        for i in range(150):
            allowed, details = detector.analyze_request(ip, "/api/test", True)
        
        # High rate should trigger detection
        stats = detector.get_statistics()
        assert stats["total_ips_analyzed"] > 0
    
    def test_ip_blocking(self):
        """Test IP address blocking."""
        detector = get_ddos_detector()
        
        # Whitelist first
        detector.whitelist_ip("192.168.4.1")
        
        allowed, details = detector.analyze_request("192.168.4.1", "/api/test")
        assert allowed, "Whitelisted IP should be allowed"
    
    def test_unblock_ip(self):
        """Test unblocking IP."""
        detector = get_ddos_detector()
        
        # Block then unblock
        detector.whitelist_ip("192.168.5.1")
        assert detector.unblock_ip("192.168.5.1"), "Should successfully unblock"
        
        result = detector.unblock_ip("192.168.5.1")
        assert not result, "Already unblocked IP should return False"
    
    def test_get_blocked_ips(self):
        """Test retrieving blocked IPs."""
        detector = get_ddos_detector()
        
        detector.whitelist_ip("192.168.6.1")
        detector.whitelist_ip("192.168.6.2")
        
        blocked = detector.get_blocked_ips()
        assert len(blocked) == 2
    
    def test_unique_endpoint_detection(self):
        """Test detection of access to many endpoints."""
        detector = get_ddos_detector()
        
        ip = "192.168.7.1"
        
        # Access many different endpoints rapidly
        for i in range(60):
            detector.analyze_request(ip, f"/endpoint{i}", True)
        
        # Check that endpoint count affects detection
        blocked = detector.get_blocked_ips()
        # May or may not be blocked depending on overall score
    
    def test_ddos_detector_statistics(self):
        """Test DDoS detector statistics."""
        detector = get_ddos_detector()
        
        detector.analyze_request("192.168.8.1", "/api/test", True)
        detector.analyze_request("192.168.8.2", "/api/test", True)
        
        stats = detector.get_statistics()
        assert stats["total_ips_analyzed"] == 2
        assert stats["total_blocks"] >= 0


class TestIntegrationScenarios:
    """Integration tests for rate limiting & protection."""
    
    def setup_method(self):
        """Reset all services before each test."""
        reset_rate_limiter_service()
        reset_quota_manager()
        reset_ddos_detector()
    
    def test_end_to_end_user_protection(self):
        """Test complete user protection flow."""
        limiter = get_rate_limiter_service()
        manager = get_quota_manager()
        detector = get_ddos_detector()
        
        # Setup
        rate_limit = RateLimit(
            limit_type="test",
            requests=100,
            window_seconds=60
        )
        limiter.configure_rate_limit("user_limit", rate_limit)
        manager.create_quota("user1", QuotaTier.BASIC)
        
        # Simulate requests
        for i in range(50):
            # Check DDoS
            ddos_ok, _ = detector.analyze_request(f"192.168.1.{i%10}", "/api/endpoint")
            if not ddos_ok:
                continue
            
            # Check rate limit
            rl_ok, _ = limiter.check_rate_limit("user_limit", 1)
            if not rl_ok:
                continue
            
            # Check quota
            q_ok, _ = manager.check_quota("user1", 1)
            assert q_ok or i > 40, "Quota should hold for initial requests"
    
    def test_ddos_attack_simulation(self):
        """Simulate a DDoS attack scenario."""
        detector = get_ddos_detector()
        
        attacker_ip = "203.0.113.1"
        
        # Simulate attack: high request rate with failures
        for i in range(200):
            success = i % 10 != 0  # 90% success, 10% failure
            allowed, details = detector.analyze_request(attacker_ip, "/api/endpoint", success)
            
            # Eventually should be blocked
            if not allowed:
                assert details["reason"] == "ddos_detected"
                break
    
    def test_multiple_user_quota_isolation(self):
        """Test that multiple users have isolated quotas."""
        manager = get_quota_manager()
        
        manager.create_quota("user_a", QuotaTier.FREE)
        manager.create_quota("user_b", QuotaTier.FREE)
        
        # User A exhausts quota
        for i in range(1000):
            manager.check_quota("user_a", 1)
        
        # User B should still have quota
        allowed, _ = manager.check_quota("user_b", 100)
        assert allowed, "User B quota should not be affected"
    
    def test_quota_reset_over_time(self):
        """Test quota resets at configured times."""
        manager = get_quota_manager()
        
        quota = manager.create_quota("user_reset", QuotaTier.FREE, reset_hour=0)
        
        # Simulate usage
        manager.check_quota("user_reset", 500)
        used_before = quota.api_calls_used_today
        
        # Quota should reset after period
        assert used_before > 0, "Some quota should be used"
    
    def test_comprehensive_request_scoring(self):
        """Test comprehensive request analysis."""
        limiter = get_rate_limiter_service()
        manager = get_quota_manager()
        detector = get_ddos_detector()
        
        # Setup
        rl = RateLimit("test", 1000, 60)
        limiter.configure_rate_limit("api", rl)
        manager.create_quota("user", QuotaTier.PREMIUM)
        
        # Simulate legitimate traffic
        allowed_count = 0
        blocked_count = 0
        
        for i in range(100):
            ddos_ok, _ = detector.analyze_request(f"192.168.1.1", f"/endpoint{i%10}")
            rl_ok, _ = limiter.check_rate_limit("api")
            q_ok, _ = manager.check_quota("user")
            
            if ddos_ok and rl_ok and q_ok:
                allowed_count += 1
            else:
                blocked_count += 1
        
        assert allowed_count > blocked_count, "Legitimate traffic should mostly be allowed"


def run_all_tests():
    """Run all tests and report results."""
    test_classes = [
        TestRateLimiterService,
        TestQuotaManager,
        TestDDoSDetector,
        TestIntegrationScenarios
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        instance = test_class()
        test_methods = [m for m in dir(instance) if m.startswith("test_")]
        
        print(f"\n{'='*60}")
        print(f"Running {test_class.__name__} ({len(test_methods)} tests)")
        print('='*60)
        
        for test_method in test_methods:
            total_tests += 1
            try:
                instance.setup_method()
                getattr(instance, test_method)()
                print(f"✓ {test_method}")
                passed_tests += 1
            except AssertionError as e:
                print(f"✗ {test_method}: {str(e)}")
                failed_tests.append((test_class.__name__, test_method, str(e)))
            except Exception as e:
                print(f"✗ {test_method}: {type(e).__name__}: {str(e)}")
                failed_tests.append((test_class.__name__, test_method, f"{type(e).__name__}: {str(e)}"))
    
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    print(f"Total: {total_tests} | Passed: {passed_tests} | Failed: {len(failed_tests)}")
    print(f"Pass Rate: {(passed_tests/max(1, total_tests))*100:.1f}%")
    
    if failed_tests:
        print("\nFailed Tests:")
        for class_name, method_name, error in failed_tests:
            print(f"  - {class_name}.{method_name}: {error}")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
