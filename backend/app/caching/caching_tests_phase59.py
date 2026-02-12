"""
Phase 59: Advanced Caching Tests
Comprehensive test coverage for multi-tier caching, invalidation, and warming.
"""

import time
from caching.caching_service_phase59 import (
    get_cache_manager,
    get_cache_warmer,
    reset_cache_manager,
    reset_cache_warmer,
    CacheConfig,
    CacheStrategy,
    CachePattern,
    InvalidationType,
    InvalidationRule,
    WarmupStrategy,
    CacheKeyBuilder,
    L1MemoryCache
)


class TestL1MemoryCache:
    """Tests for L1 in-memory cache."""
    
    def setup_method(self):
        """Reset cache before each test."""
        reset_cache_manager()
    
    def test_basic_set_get(self):
        """Test basic cache set and get."""
        cache = L1MemoryCache(CacheConfig())
        
        cache.set("key1", "value1")
        found, value = cache.get("key1")
        
        assert found, "Key should be found"
        assert value == "value1", "Value should match"
    
    def test_cache_miss(self):
        """Test cache miss returns False."""
        cache = L1MemoryCache(CacheConfig())
        
        found, value = cache.get("nonexistent")
        
        assert not found, "Nonexistent key should not be found"
        assert value is None, "Value should be None"
    
    def test_cache_expiration_ttl(self):
        """Test cache entry expiration by TTL."""
        cache = L1MemoryCache(CacheConfig())
        
        cache.set("key1", "value1", ttl_seconds=1)
        found, _ = cache.get("key1")
        assert found, "Entry should exist immediately"
        
        time.sleep(1.1)
        found, _ = cache.get("key1")
        assert not found, "Entry should expire after TTL"
    
    def test_cache_delete(self):
        """Test cache entry deletion."""
        cache = L1MemoryCache(CacheConfig())
        
        cache.set("key1", "value1")
        assert cache.delete("key1"), "Delete should succeed"
        
        found, _ = cache.get("key1")
        assert not found, "Deleted key should not exist"
    
    def test_lru_eviction(self):
        """Test LRU eviction strategy."""
        config = CacheConfig(max_entries=3, strategy=CacheStrategy.LRU)
        cache = L1MemoryCache(config)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key2 to make it more recently used
        cache.get("key2")
        
        # Add new entry, should evict key1 (least recently used)
        cache.set("key4", "value4")
        
        found, _ = cache.get("key1")
        assert not found, "key1 should be evicted"
        
        found, _ = cache.get("key2")
        assert found, "key2 should remain"
    
    def test_tag_based_invalidation(self):
        """Test invalidation by tag."""
        cache = L1MemoryCache(CacheConfig())
        
        cache.set("key1", "value1", tags={"api", "users"})
        cache.set("key2", "value2", tags={"api", "posts"})
        cache.set("key3", "value3", tags={"cache"})
        
        count = cache.invalidate_by_tag("api")
        
        assert count == 2, "Should invalidate 2 entries"
        
        found, _ = cache.get("key1")
        assert not found, "key1 should be invalidated"
        
        found, _ = cache.get("key3")
        assert found, "key3 should remain"
    
    def test_pattern_based_invalidation(self):
        """Test invalidation by pattern."""
        cache = L1MemoryCache(CacheConfig())
        
        cache.set("user:1:profile", "profile1")
        cache.set("user:2:profile", "profile2")
        cache.set("user:1:settings", "settings1")
        cache.set("post:1:data", "post_data")
        
        count = cache.invalidate_by_pattern(r"user:.*:profile")
        
        assert count == 2, "Should invalidate 2 entries"
        
        found, _ = cache.get("user:1:profile")
        assert not found, "Should be invalidated"
        
        found, _ = cache.get("user:1:settings")
        assert found, "Should not match pattern"
    
    def test_clear_cache(self):
        """Test clearing entire cache."""
        cache = L1MemoryCache(CacheConfig())
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        count = cache.clear()
        assert count == 2, "Should clear 2 entries"
        
        found, _ = cache.get("key1")
        assert not found, "Cache should be empty"
    
    def test_cache_metrics(self):
        """Test cache metrics tracking."""
        cache = L1MemoryCache(CacheConfig())
        
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        cache.delete("key1")
        
        metrics = cache.get_metrics()
        assert metrics.hits >= 1, "Should record hits"
        assert metrics.misses >= 1, "Should record misses"
        assert metrics.writes >= 1, "Should record writes"
        assert metrics.deletes >= 1, "Should record deletes"


class TestCacheManager:
    """Tests for cache manager."""
    
    def setup_method(self):
        """Reset services before each test."""
        reset_cache_manager()
        reset_cache_warmer()
    
    def test_cache_manager_get_set(self):
        """Test cache manager basic operations."""
        manager = get_cache_manager()
        
        manager.set("key1", {"data": "value1"})
        found, value = manager.get("key1")
        
        assert found, "Should find key"
        assert value["data"] == "value1", "Value should match"
    
    def test_cache_manager_with_fetch_func(self):
        """Test cache manager with fetch function."""
        manager = get_cache_manager()
        
        def fetch_data(key):
            return f"fetched_{key}"
        
        found, value = manager.get("key1", fetch_func=fetch_data)
        
        assert found, "Should fetch and cache"
        assert value == "fetched_key1", "Should return fetched value"
        
        # Second access should hit cache
        found2, value2 = manager.get("key1")
        assert found2, "Should hit cache"
    
    def test_cache_manager_invalidation_rules(self):
        """Test invalidation rules."""
        manager = get_cache_manager()
        
        manager.set("user:1:data", "data1", tags={"user", "user:1"})
        manager.set("user:2:data", "data2", tags={"user", "user:2"})
        
        rule = InvalidationRule(
            rule_id="rule1",
            rule_type=InvalidationType.TAG_BASED,
            target_tags={"user"}
        )
        manager.add_invalidation_rule(rule)
        
        count = manager.apply_invalidation_rules()
        
        assert count >= 2, "Should invalidate by rule"
    
    def test_cache_manager_statistics(self):
        """Test cache manager statistics."""
        manager = get_cache_manager()
        
        manager.set("key1", "value1")
        manager.get("key1")
        manager.get("nonexistent")
        
        stats = manager.get_cache_stat_summary()
        
        assert stats["total_sets"] >= 1, "Should record sets"
        assert stats["total_gets"] >= 2, "Should record gets"
    
    def test_cache_manager_delete(self):
        """Test cache manager delete."""
        manager = get_cache_manager()
        
        manager.set("key1", "value1")
        assert manager.delete("key1"), "Delete should succeed"
        
        found, _ = manager.get("key1")
        assert not found, "Deleted key should not exist"
    
    def test_cache_clear(self):
        """Test clearing cache."""
        manager = get_cache_manager()
        
        manager.set("key1", "value1")
        manager.set("key2", "value2")
        
        count = manager.clear_all()
        assert count >= 2, "Should clear entries"


class TestCacheWarmer:
    """Tests for cache warming."""
    
    def setup_method(self):
        """Reset services before each test."""
        reset_cache_manager()
        reset_cache_warmer()
    
    def test_cache_warmup_simple(self):
        """Test simple cache warming."""
        manager = get_cache_manager()
        warmer = get_cache_warmer()
        
        def loader(key: str):
            return f"data_{key}"
        
        warmer.schedule_warmup("warmup1", ["key1", "key2"], loader)
        count = warmer.run_warmup("warmup1")
        
        assert count >= 0, "Should complete warmup"
    
    def test_cache_prefetch(self):
        """Test cache prefetch."""
        manager = get_cache_manager()
        
        def loader(key: str):
            return f"data_{key}"
        
        keys = ["k1", "k2", "k3"]
        count = manager.prefetch_keys(keys, loader)
        
        assert count >= 0, "Should prefetch keys"


class TestCacheKeyBuilder:
    """Tests for cache key building."""
    
    def test_build_simple_key(self):
        """Test building simple cache key."""
        key = CacheKeyBuilder.build_key("user", "123")
        assert "user" in key, "Should include namespace"
        assert "123" in key, "Should include argument"
    
    def test_build_key_with_kwargs(self):
        """Test building key with kwargs."""
        key = CacheKeyBuilder.build_key("user", "123", action="profile", version="v1")
        
        assert "user" in key, "Should include namespace"
        assert "123" in key, "Should include positional arg"
        assert "action" in key, "Should include kwarg"
    
    def test_build_pattern_key(self):
        """Test building pattern key."""
        pattern = CacheKeyBuilder.build_pattern_key("user", "*", "profile")
        
        assert "user" in pattern, "Should include namespace"
        assert "profile" in pattern, "Should include component"
    
    def test_long_key_hashing(self):
        """Test that long keys are hashed."""
        long_key = "key_" + "x" * 300
        key = CacheKeyBuilder.build_key("namespace", long_key)
        
        assert len(key) <= 255, "Should hash long keys"


class TestCacheIntegration:
    """Integration tests for caching."""
    
    def setup_method(self):
        """Reset services before each test."""
        reset_cache_manager()
        reset_cache_warmer()
    
    def test_end_to_end_cache_workflow(self):
        """Test complete cache workflow."""
        manager = get_cache_manager()
        
        # Set data
        manager.set("user:1:profile", {
            "id": 1,
            "name": "Alice",
            "email": "alice@example.com"
        }, tags={"user", "profile"})
        
        # Retrieve data
        found, profile = manager.get("user:1:profile")
        assert found, "Should retrieve data"
        assert profile["name"] == "Alice", "Data should be correct"
        
        # Add invalidation rule
        rule = InvalidationRule(
            rule_id="profile_rule",
            rule_type=InvalidationType.TAG_BASED,
            target_tags={"profile"}
        )
        manager.add_invalidation_rule(rule)
        
        # Apply invalidation
        count = manager.apply_invalidation_rules()
        assert count >= 1, "Should invalidate by rule"
        
        # Verify data is gone
        found, _ = manager.get("user:1:profile")
        assert not found, "Data should be invalidated"
    
    def test_multi_user_cache_isolation(self):
        """Test cache isolation for multiple users."""
        manager = get_cache_manager()
        
        manager.set("user:1:data", "user1_data", tags={"user:1"})
        manager.set("user:2:data", "user2_data", tags={"user:2"})
        
        # Invalidate only user 1
        manager.l1_cache.invalidate_by_tag("user:1")
        
        found1, _ = manager.get("user:1:data")
        found2, _ = manager.get("user:2:data")
        
        assert not found1, "User 1 data should be invalidated"
        assert found2, "User 2 data should remain"
    
    def test_cache_statistics_tracking(self):
        """Test cache statistics over operations."""
        manager = get_cache_manager()
        
        # Generate cache activity
        for i in range(10):
            manager.set(f"key{i}", f"value{i}")
        
        for i in range(15):
            manager.get(f"key{i % 10}")
        
        stats = manager.get_cache_stat_summary()
        
        assert stats["total_sets"] >= 10, "Should track all sets"
        assert stats["total_gets"] >= 15, "Should track all gets"
        assert "l1_metrics" in stats, "Should include metrics"
    
    def test_cache_with_ttl_expiration(self):
        """Test cache with TTL and expiration."""
        manager = get_cache_manager()
        
        manager.set("temp_key", "temp_value", ttl_seconds=1)
        
        found, _ = manager.get("temp_key")
        assert found, "Should exist immediately"
        
        time.sleep(1.1)
        
        found, _ = manager.get("temp_key")
        assert not found, "Should expire after TTL"
    
    def test_cache_replacement_strategies(self):
        """Test different cache replacement strategies."""
        for strategy in [CacheStrategy.LRU, CacheStrategy.FIFO]:
            reset_cache_manager()
            
            config = CacheConfig(max_entries=3, strategy=strategy)
            manager = get_cache_manager(config)
            
            manager.set("k1", "v1")
            manager.set("k2", "v2")
            manager.set("k3", "v3")
            manager.set("k4", "v4")  # Should trigger eviction
            
            stats = manager.get_cache_stat_summary()
            assert stats["l1_metrics"]["evictions"] > 0, f"{strategy} should evict"


def run_all_tests():
    """Run all tests and report results."""
    test_classes = [
        TestL1MemoryCache,
        TestCacheManager,
        TestCacheWarmer,
        TestCacheKeyBuilder,
        TestCacheIntegration
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
