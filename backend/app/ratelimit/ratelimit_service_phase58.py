"""
Phase 58: Rate Limiting & Throttling Service
Comprehensive rate limiting, throttling, quota management, and DDoS protection.
"""

import time
import threading
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
from collections import deque
import math


# ===================== ENUMS =====================

class RateLimitAlgorithm(Enum):
    """Rate limiting algorithms supported."""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"


class QuotaTier(Enum):
    """User quota tiers."""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class BlockType(Enum):
    """Types of IP blocks."""
    TEMPORARY = "temporary"
    PERMANENT = "permanent"
    WHITELIST = "whitelist"


class DDoSDetectionLevel(Enum):
    """DDoS detection severity levels."""
    NORMAL = "normal"
    SUSPICIOUS = "suspicious"
    ATTACK = "attack"
    CRITICAL = "critical"


# ===================== DATA CLASSES =====================

@dataclass
class RateLimit:
    """Rate limit configuration."""
    limit_type: str  # "user", "ip", "endpoint"
    requests: int  # Max requests
    window_seconds: int  # Time window in seconds
    burst_allowed: int = 0  # Burst capacity
    penalty_seconds: int = 60  # Penalty duration if exceeded
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self):
        return {
            "limit_type": self.limit_type,
            "requests": self.requests,
            "window_seconds": self.window_seconds,
            "burst_allowed": self.burst_allowed,
            "penalty_seconds": self.penalty_seconds,
            "algorithm": self.algorithm.value,
            "metadata": self.metadata
        }


@dataclass
class TokenBucket:
    """Token bucket implementation."""
    bucket_id: str
    max_tokens: float
    refill_rate: float  # tokens per second
    current_tokens: float
    last_refill_time: float
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self):
        return {
            "bucket_id": self.bucket_id,
            "max_tokens": self.max_tokens,
            "refill_rate": self.refill_rate,
            "current_tokens": self.current_tokens,
            "last_refill_time": self.last_refill_time,
            "created_at": self.created_at
        }


@dataclass
class SlidingWindowCounter:
    """Sliding window counter for rate limiting."""
    counter_id: str
    window_seconds: int
    max_requests: int
    request_times: deque = field(default_factory=lambda: deque(maxlen=10000))
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self):
        return {
            "counter_id": self.counter_id,
            "window_seconds": self.window_seconds,
            "max_requests": self.max_requests,
            "request_count": len(self.request_times),
            "created_at": self.created_at
        }


@dataclass
class UserQuota:
    """User quota configuration."""
    user_id: str
    tier: QuotaTier
    requests_per_day: int
    requests_per_hour: int
    requests_per_minute: int
    concurrent_requests: int
    storage_gb: float
    api_calls_used_today: int = 0
    api_calls_used_hour: int = 0
    api_calls_used_minute: int = 0
    concurrent_active: int = 0
    storage_used_gb: float = 0.0
    reset_hour: int = 0  # UTC hour
    created_at: float = field(default_factory=time.time)
    last_reset: float = field(default_factory=time.time)
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "tier": self.tier.value,
            "requests_per_day": self.requests_per_day,
            "requests_per_hour": self.requests_per_hour,
            "requests_per_minute": self.requests_per_minute,
            "concurrent_requests": self.concurrent_requests,
            "storage_gb": self.storage_gb,
            "api_calls_used_today": self.api_calls_used_today,
            "api_calls_used_hour": self.api_calls_used_hour,
            "api_calls_used_minute": self.api_calls_used_minute,
            "concurrent_active": self.concurrent_active,
            "storage_used_gb": self.storage_used_gb,
            "reset_hour": self.reset_hour,
            "created_at": self.created_at,
            "last_reset": self.last_reset
        }


@dataclass
class IPBlock:
    """IP block record."""
    ip_address: str
    block_type: BlockType
    reason: str
    blocked_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    request_count: int = 0
    last_request_time: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self):
        return {
            "ip_address": self.ip_address,
            "block_type": self.block_type.value,
            "reason": self.reason,
            "blocked_at": self.blocked_at,
            "expires_at": self.expires_at,
            "request_count": self.request_count,
            "last_request_time": self.last_request_time,
            "metadata": self.metadata
        }


@dataclass
class DDoSIndicator:
    """DDoS attack indicator."""
    indicator_id: str
    ip_address: str
    detection_level: DDoSDetectionLevel
    request_rate: float  # requests per second
    failed_requests: int
    unique_endpoints: int
    burst_detected: bool
    temporal_score: float  # 0-1 anomaly score
    spatial_score: float  # 0-1 geographic anomaly
    detected_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self):
        return {
            "indicator_id": self.indicator_id,
            "ip_address": self.ip_address,
            "detection_level": self.detection_level.value,
            "request_rate": self.request_rate,
            "failed_requests": self.failed_requests,
            "unique_endpoints": self.unique_endpoints,
            "burst_detected": self.burst_detected,
            "temporal_score": self.temporal_score,
            "spatial_score": self.spatial_score,
            "detected_at": self.detected_at,
            "last_updated": self.last_updated,
            "metadata": self.metadata
        }


# ===================== SERVICES =====================

class RateLimiterService:
    """Rate limiting service with multiple algorithms."""
    
    def __init__(self):
        self._token_buckets: Dict[str, TokenBucket] = {}
        self._sliding_windows: Dict[str, SlidingWindowCounter] = {}
        self._rate_limits: Dict[str, RateLimit] = {}
        self._lock = threading.Lock()
        self._statistics = {
            "total_requests": 0,
            "throttled_requests": 0,
            "burst_allowed": 0,
            "buckets_count": 0,
            "windows_count": 0
        }
    
    def configure_rate_limit(self, limit_id: str, rate_limit: RateLimit) -> None:
        """Configure a rate limit."""
        with self._lock:
            self._rate_limits[limit_id] = rate_limit
    
    def check_rate_limit(self, limit_id: str, tokens: int = 1, burst: bool = False) -> Tuple[bool, Dict]:
        """Check if request is allowed under rate limit. Returns (allowed, details)."""
        with self._lock:
            if limit_id not in self._rate_limits:
                return True, {"allowed": True, "reason": "no_limit_configured"}
            
            rate_limit = self._rate_limits[limit_id]
            self._statistics["total_requests"] += 1
            
            if rate_limit.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                return self._check_token_bucket(limit_id, tokens, burst)
            elif rate_limit.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
                return self._check_sliding_window(limit_id, tokens)
            elif rate_limit.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
                return self._check_fixed_window(limit_id)
            else:
                return True, {"allowed": True, "reason": "unknown_algorithm"}
    
    def _check_token_bucket(self, bucket_id: str, tokens: int, burst: bool) -> Tuple[bool, Dict]:
        """Token bucket algorithm implementation."""
        if bucket_id not in self._token_buckets:
            rate_limit = self._rate_limits[bucket_id]
            self._token_buckets[bucket_id] = TokenBucket(
                bucket_id=bucket_id,
                max_tokens=float(rate_limit.requests + rate_limit.burst_allowed),
                refill_rate=rate_limit.requests / rate_limit.window_seconds,
                current_tokens=float(rate_limit.requests)
            )
            self._statistics["buckets_count"] += 1
        
        bucket = self._token_buckets[bucket_id]
        
        # Refill tokens
        current_time = time.time()
        elapsed = current_time - bucket.last_refill_time
        tokens_to_add = elapsed * bucket.refill_rate
        bucket.current_tokens = min(bucket.max_tokens, bucket.current_tokens + tokens_to_add)
        bucket.last_refill_time = current_time
        
        # Check if request can proceed
        if bucket.current_tokens >= tokens:
            bucket.current_tokens -= tokens
            return True, {
                "allowed": True,
                "tokens_remaining": int(bucket.current_tokens),
                "algorithm": "token_bucket"
            }
        else:
            if burst and bucket.current_tokens > 0:
                bucket.current_tokens = 0
                self._statistics["burst_allowed"] += 1
                return True, {
                    "allowed": True,
                    "burst_used": True,
                    "algorithm": "token_bucket"
                }
            else:
                self._statistics["throttled_requests"] += 1
                retry_after = (tokens - bucket.current_tokens) / bucket.refill_rate
                return False, {
                    "allowed": False,
                    "reason": "insufficient_tokens",
                    "tokens_needed": tokens,
                    "tokens_available": int(bucket.current_tokens),
                    "retry_after_seconds": max(1, int(math.ceil(retry_after)))
                }
    
    def _check_sliding_window(self, window_id: str, tokens: int) -> Tuple[bool, Dict]:
        """Sliding window counter algorithm."""
        if window_id not in self._sliding_windows:
            rate_limit = self._rate_limits[window_id]
            self._sliding_windows[window_id] = SlidingWindowCounter(
                counter_id=window_id,
                window_seconds=rate_limit.window_seconds,
                max_requests=rate_limit.requests
            )
            self._statistics["windows_count"] += 1
        
        counter = self._sliding_windows[window_id]
        current_time = time.time()
        
        # Remove old requests outside window
        while counter.request_times and (current_time - counter.request_times[0]) > counter.window_seconds:
            counter.request_times.popleft()
        
        # Check if within limit
        if len(counter.request_times) + tokens <= counter.max_requests:
            for _ in range(tokens):
                counter.request_times.append(current_time)
            return True, {
                "allowed": True,
                "requests_used": len(counter.request_times),
                "requests_limit": counter.max_requests,
                "algorithm": "sliding_window"
            }
        else:
            self._statistics["throttled_requests"] += 1
            oldest_request = counter.request_times[0] if counter.request_times else current_time
            retry_after = counter.window_seconds - (current_time - oldest_request)
            return False, {
                "allowed": False,
                "reason": "window_limit_exceeded",
                "requests_used": len(counter.request_times),
                "requests_limit": counter.max_requests,
                "retry_after_seconds": max(1, int(math.ceil(retry_after)))
            }
    
    def _check_fixed_window(self, window_id: str) -> Tuple[bool, Dict]:
        """Fixed window counter algorithm."""
        if window_id not in self._sliding_windows:
            rate_limit = self._rate_limits[window_id]
            self._sliding_windows[window_id] = SlidingWindowCounter(
                counter_id=window_id,
                window_seconds=rate_limit.window_seconds,
                max_requests=rate_limit.requests
            )
            self._statistics["windows_count"] += 1
        
        counter = self._sliding_windows[window_id]
        current_time = time.time()
        
        # Check if window expired
        if counter.request_times and (current_time - counter.request_times[0]) > counter.window_seconds:
            counter.request_times.clear()
        
        # Check limit
        if len(counter.request_times) < counter.max_requests:
            counter.request_times.append(current_time)
            return True, {
                "allowed": True,
                "requests_used": len(counter.request_times),
                "requests_limit": counter.max_requests
            }
        else:
            self._statistics["throttled_requests"] += 1
            reset_time = counter.request_times[0] + counter.window_seconds if counter.request_times else current_time + counter.window_seconds
            retry_after = reset_time - current_time
            return False, {
                "allowed": False,
                "reason": "fixed_window_exceeded",
                "retry_after_seconds": max(1, int(math.ceil(retry_after)))
            }
    
    def reset_limit(self, limit_id: str) -> None:
        """Reset rate limit for an ID."""
        with self._lock:
            if limit_id in self._token_buckets:
                del self._token_buckets[limit_id]
            if limit_id in self._sliding_windows:
                del self._sliding_windows[limit_id]
    
    def get_statistics(self) -> Dict:
        """Get rate limiter statistics."""
        with self._lock:
            return {
                "total_requests": self._statistics["total_requests"],
                "throttled_requests": self._statistics["throttled_requests"],
                "throttle_rate": (
                    self._statistics["throttled_requests"] / max(1, self._statistics["total_requests"])
                ),
                "burst_allowed": self._statistics["burst_allowed"],
                "active_buckets": len(self._token_buckets),
                "active_windows": len(self._sliding_windows),
                "configured_limits": len(self._rate_limits)
            }


class QuotaManager:
    """Manages user quotas and resource consumption."""
    
    def __init__(self):
        self._quotas: Dict[str, UserQuota] = {}
        self._quota_tiers = {
            QuotaTier.FREE: {
                "requests_per_day": 1000,
                "requests_per_hour": 100,
                "requests_per_minute": 10,
                "concurrent_requests": 2,
                "storage_gb": 1.0
            },
            QuotaTier.BASIC: {
                "requests_per_day": 10000,
                "requests_per_hour": 1000,
                "requests_per_minute": 100,
                "concurrent_requests": 5,
                "storage_gb": 10.0
            },
            QuotaTier.PREMIUM: {
                "requests_per_day": 100000,
                "requests_per_hour": 10000,
                "requests_per_minute": 1000,
                "concurrent_requests": 20,
                "storage_gb": 100.0
            },
            QuotaTier.ENTERPRISE: {
                "requests_per_day": 1000000,
                "requests_per_hour": 100000,
                "requests_per_minute": 10000,
                "concurrent_requests": 100,
                "storage_gb": 1000.0
            }
        }
        self._lock = threading.Lock()
        self._statistics = {
            "total_users": 0,
            "users_by_tier": {},
            "quota_violations": 0,
            "quota_warnings": 0
        }
    
    def create_quota(self, user_id: str, tier: QuotaTier, reset_hour: int = 0) -> UserQuota:
        """Create user quota."""
        with self._lock:
            tier_limits = self._quota_tiers[tier]
            quota = UserQuota(
                user_id=user_id,
                tier=tier,
                requests_per_day=tier_limits["requests_per_day"],
                requests_per_hour=tier_limits["requests_per_hour"],
                requests_per_minute=tier_limits["requests_per_minute"],
                concurrent_requests=tier_limits["concurrent_requests"],
                storage_gb=tier_limits["storage_gb"],
                reset_hour=reset_hour
            )
            self._quotas[user_id] = quota
            self._statistics["total_users"] += 1
            self._statistics["users_by_tier"][tier.value] = self._statistics["users_by_tier"].get(tier.value, 0) + 1
            return quota
    
    def get_quota(self, user_id: str) -> Optional[UserQuota]:
        """Get user quota."""
        with self._lock:
            return self._quotas.get(user_id)
    
    def check_quota(self, user_id: str, requests: int = 1, concurrent: int = 0, storage_gb: float = 0) -> Tuple[bool, Dict]:
        """Check if quota allows operation."""
        with self._lock:
            if user_id not in self._quotas:
                return True, {"allowed": True, "reason": "quota_not_configured"}
            
            quota = self._quotas[user_id]
            current_time = time.time()
            
            # Check if need to reset
            self._check_quota_reset(quota, current_time)
            
            violations = []
            warnings = []
            
            # Check daily quota
            if quota.api_calls_used_today + requests > quota.requests_per_day:
                violations.append("daily_quota")
            elif quota.api_calls_used_today + requests > int(quota.requests_per_day * 0.9):
                warnings.append("approaching_daily_limit")
            
            # Check hourly quota
            if quota.api_calls_used_hour + requests > quota.requests_per_hour:
                violations.append("hourly_quota")
            elif quota.api_calls_used_hour + requests > int(quota.requests_per_hour * 0.9):
                warnings.append("approaching_hourly_limit")
            
            # Check minute quota
            if quota.api_calls_used_minute + requests > quota.requests_per_minute:
                violations.append("minute_quota")
            elif quota.api_calls_used_minute + requests > int(quota.requests_per_minute * 0.9):
                warnings.append("approaching_minute_limit")
            
            # Check concurrent requests
            if quota.concurrent_active + concurrent > quota.concurrent_requests:
                violations.append("concurrent_limit")
            
            # Check storage
            if quota.storage_used_gb + storage_gb > quota.storage_gb:
                violations.append("storage_quota")
            elif quota.storage_used_gb + storage_gb > quota.storage_gb * 0.9:
                warnings.append("approaching_storage_limit")
            
            if violations:
                self._statistics["quota_violations"] += 1
                return False, {
                    "allowed": False,
                    "violations": violations,
                    "quota_status": quota.to_dict()
                }
            
            if warnings:
                self._statistics["quota_warnings"] += 1
            
            # Update quota usage
            quota.api_calls_used_today += requests
            quota.api_calls_used_hour += requests
            quota.api_calls_used_minute += requests
            quota.concurrent_active += concurrent
            quota.storage_used_gb += storage_gb
            
            return True, {
                "allowed": True,
                "warnings": warnings,
                "quota_remaining": {
                    "daily": quota.requests_per_day - quota.api_calls_used_today,
                    "hourly": quota.requests_per_hour - quota.api_calls_used_hour,
                    "minute": quota.requests_per_minute - quota.api_calls_used_minute
                }
            }
    
    def _check_quota_reset(self, quota: UserQuota, current_time: float) -> None:
        """Check and reset quota counters if period expired."""
        last_reset = quota.last_reset
        
        # Minute reset (every 60 seconds)
        if current_time - last_reset > 60:
            quota.api_calls_used_minute = 0
        
        # Hour reset
        current_hour = int(current_time / 3600)
        last_hour = int(last_reset / 3600)
        if current_hour != last_hour:
            quota.api_calls_used_hour = 0
        
        # Day reset (at configured hour)
        current_day = int(current_time / 86400)
        last_day = int(last_reset / 86400)
        if current_day != last_day:
            quota.api_calls_used_today = 0
            quota.last_reset = current_time
    
    def release_quota(self, user_id: str, concurrent: int = 0, storage_gb: float = 0) -> None:
        """Release quota resources."""
        with self._lock:
            if user_id in self._quotas:
                quota = self._quotas[user_id]
                quota.concurrent_active = max(0, quota.concurrent_active - concurrent)
                quota.storage_used_gb = max(0.0, quota.storage_used_gb - storage_gb)
    
    def upgrade_tier(self, user_id: str, new_tier: QuotaTier) -> Optional[UserQuota]:
        """Upgrade user to new tier."""
        with self._lock:
            if user_id not in self._quotas:
                return None
            
            old_tier = self._quotas[user_id].tier
            quota = self._quotas[user_id]
            tier_limits = self._quota_tiers[new_tier]
            
            quota.tier = new_tier
            quota.requests_per_day = tier_limits["requests_per_day"]
            quota.requests_per_hour = tier_limits["requests_per_hour"]
            quota.requests_per_minute = tier_limits["requests_per_minute"]
            quota.concurrent_requests = tier_limits["concurrent_requests"]
            quota.storage_gb = tier_limits["storage_gb"]
            
            self._statistics["users_by_tier"][old_tier.value] = max(0, self._statistics["users_by_tier"].get(old_tier.value, 1) - 1)
            self._statistics["users_by_tier"][new_tier.value] = self._statistics["users_by_tier"].get(new_tier.value, 0) + 1
            
            return quota
    
    def get_statistics(self) -> Dict:
        """Get quota statistics."""
        with self._lock:
            return {
                "total_users": self._statistics["total_users"],
                "users_by_tier": self._statistics["users_by_tier"],
                "quota_violations": self._statistics["quota_violations"],
                "quota_warnings": self._statistics["quota_warnings"],
                "average_storage_used_gb": self._calculate_avg_storage()
            }
    
    def _calculate_avg_storage(self) -> float:
        """Calculate average storage used."""
        if not self._quotas:
            return 0.0
        total = sum(quota.storage_used_gb for quota in self._quotas.values())
        return total / len(self._quotas)


class DDoSDetector:
    """Detects and mitigates DDoS attacks."""
    
    def __init__(self):
        self._ip_blocks: Dict[str, IPBlock] = {}
        self._indicators: Dict[str, DDoSIndicator] = {}
        self._ip_request_history: Dict[str, deque] = {}
        self._endpoint_access: Dict[str, Dict[str, int]] = {}  # endpoint -> {ip -> count}
        self._geographic_data: Dict[str, str] = {}  # ip -> country
        self._lock = threading.Lock()
        self._thresholds = {
            "requests_per_second": 100,
            "failed_requests_ratio": 0.5,
            "unique_endpoints": 50,
            "burst_window_seconds": 5
        }
        self._statistics = {
            "total_ips_analyzed": 0,
            "total_blocks": 0,
            "attacks_detected": 0,
            "false_positives": 0
        }
    
    def analyze_request(self, ip_address: str, endpoint: str, success: bool = True) -> Tuple[bool, Dict]:
        """Analyze incoming request for DDoS. Returns (allowed, details)."""
        with self._lock:
            # Check if IP is blocked
            if ip_address in self._ip_blocks:
                block = self._ip_blocks[ip_address]
                if block.block_type == BlockType.PERMANENT:
                    return False, {
                        "allowed": False,
                        "reason": "permanently_blocked",
                        "block_reason": block.reason
                    }
                elif block.block_type == BlockType.TEMPORARY and block.expires_at:
                    if time.time() < block.expires_at:
                        return False, {
                            "allowed": False,
                            "reason": "temporarily_blocked",
                            "expires_at": block.expires_at
                        }
                    else:
                        # Block expired
                        del self._ip_blocks[ip_address]
                else:
                    # Whitelist
                    pass
            
            # Add to history
            if ip_address not in self._ip_request_history:
                self._ip_request_history[ip_address] = deque(maxlen=10000)
                self._endpoint_access[ip_address] = {}
            
            current_time = time.time()
            self._ip_request_history[ip_address].append((current_time, success))
            self._endpoint_access[ip_address][endpoint] = self._endpoint_access[ip_address].get(endpoint, 0) + 1
            
            # Analyze patterns
            detection_level, scores = self._detect_anomalies(ip_address, current_time)
            
            if detection_level in [DDoSDetectionLevel.ATTACK, DDoSDetectionLevel.CRITICAL]:
                self._block_ip(ip_address, f"DDoS: {detection_level.value}", BlockType.TEMPORARY, 3600)
                self._statistics["attacks_detected"] += 1
                return False, {
                    "allowed": False,
                    "reason": "ddos_detected",
                    "detection_level": detection_level.value,
                    "scores": scores
                }
            elif detection_level == DDoSDetectionLevel.SUSPICIOUS:
                return True, {
                    "allowed": True,
                    "warning": "suspicious_activity_detected",
                    "detection_level": detection_level.value,
                    "scores": scores
                }
            
            return True, {
                "allowed": True,
                "detection_level": detection_level.value
            }
    
    def _detect_anomalies(self, ip_address: str, current_time: float) -> Tuple[DDoSDetectionLevel, Dict]:
        """Detect anomalies in request patterns."""
        history = self._ip_request_history.get(ip_address, deque())
        endpoint_map = self._endpoint_access.get(ip_address, {})
        
        # Temporal analysis: request rate
        recent = [(t, s) for t, s in history if current_time - t < 5]  # Last 5 seconds
        request_rate = len(recent) / 5.0 if recent else 0
        temporal_score = min(1.0, request_rate / self._thresholds["requests_per_second"])
        
        # Failed requests ratio
        if recent:
            failed = sum(1 for t, s in recent if not s)
            failed_ratio = failed / len(recent)
            failed_score = min(1.0, failed_ratio / self._thresholds["failed_requests_ratio"])
        else:
            failed_score = 0.0
        
        # Unique endpoints
        unique_endpoints = len(endpoint_map)
        endpoint_score = min(1.0, unique_endpoints / self._thresholds["unique_endpoints"])
        
        # Burst detection
        if len(recent) > self._thresholds["requests_per_second"] * 0.8:
            burst_score = 1.0
        else:
            burst_score = 0.0
        
        # Geographic anomaly (simplified)
        spatial_score = 0.1  # Placeholder
        
        # Calculate overall scores and level
        temporal_weighted = temporal_score * 0.4
        failed_weighted = failed_score * 0.2
        endpoint_weighted = endpoint_score * 0.2
        burst_weighted = burst_score * 0.2
        
        overall_score = temporal_weighted + failed_weighted + endpoint_weighted + burst_weighted
        
        if overall_score >= 0.8:
            level = DDoSDetectionLevel.CRITICAL
        elif overall_score >= 0.6:
            level = DDoSDetectionLevel.ATTACK
        elif overall_score >= 0.4:
            level = DDoSDetectionLevel.SUSPICIOUS
        else:
            level = DDoSDetectionLevel.NORMAL
        
        return level, {
            "temporal_score": round(temporal_score, 3),
            "failed_score": round(failed_score, 3),
            "endpoint_score": round(endpoint_score, 3),
            "burst_score": round(burst_score, 3),
            "overall_score": round(overall_score, 3),
            "request_rate": round(request_rate, 2),
            "unique_endpoints": unique_endpoints,
            "recent_requests": len(recent)
        }
    
    def _block_ip(self, ip_address: str, reason: str, block_type: BlockType, duration_seconds: int = 0) -> None:
        """Block an IP address."""
        expires_at = None if block_type == BlockType.PERMANENT else time.time() + duration_seconds
        self._ip_blocks[ip_address] = IPBlock(
            ip_address=ip_address,
            block_type=block_type,
            reason=reason,
            expires_at=expires_at
        )
        self._statistics["total_blocks"] += 1
    
    def whitelist_ip(self, ip_address: str) -> None:
        """Add IP to whitelist."""
        self._ip_blocks[ip_address] = IPBlock(
            ip_address=ip_address,
            block_type=BlockType.WHITELIST,
            reason="whitelisted"
        )
    
    def unblock_ip(self, ip_address: str) -> bool:
        """Unblock an IP address."""
        if ip_address in self._ip_blocks:
            del self._ip_blocks[ip_address]
            return True
        return False
    
    def get_blocked_ips(self) -> List[Dict]:
        """Get all blocked IPs."""
        with self._lock:
            return [block.to_dict() for block in self._ip_blocks.values()]
    
    def get_statistics(self) -> Dict:
        """Get DDoS detector statistics."""
        with self._lock:
            return {
                "total_ips_analyzed": len(self._ip_request_history),
                "total_blocks": self._statistics["total_blocks"],
                "active_blocks": len(self._ip_blocks),
                "attacks_detected": self._statistics["attacks_detected"],
                "indicators_count": len(self._indicators)
            }


# ===================== SINGLETON SERVICES =====================

_rate_limiter_instance: Optional[RateLimiterService] = None
_quota_manager_instance: Optional[QuotaManager] = None
_ddos_detector_instance: Optional[DDoSDetector] = None


def get_rate_limiter_service() -> RateLimiterService:
    """Get rate limiter singleton."""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = RateLimiterService()
    return _rate_limiter_instance


def get_quota_manager() -> QuotaManager:
    """Get quota manager singleton."""
    global _quota_manager_instance
    if _quota_manager_instance is None:
        _quota_manager_instance = QuotaManager()
    return _quota_manager_instance


def get_ddos_detector() -> DDoSDetector:
    """Get DDoS detector singleton."""
    global _ddos_detector_instance
    if _ddos_detector_instance is None:
        _ddos_detector_instance = DDoSDetector()
    return _ddos_detector_instance


def reset_rate_limiter_service() -> None:
    """Reset rate limiter for testing."""
    global _rate_limiter_instance
    _rate_limiter_instance = RateLimiterService()


def reset_quota_manager() -> None:
    """Reset quota manager for testing."""
    global _quota_manager_instance
    _quota_manager_instance = QuotaManager()


def reset_ddos_detector() -> None:
    """Reset DDoS detector for testing."""
    global _ddos_detector_instance
    _ddos_detector_instance = DDoSDetector()
