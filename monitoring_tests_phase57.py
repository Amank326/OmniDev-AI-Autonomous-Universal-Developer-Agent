"""
Phase 57: Monitoring & Observability - Verification Tests
Comprehensive test suite for health checks, metrics, tracing,
alerts, and observability system (15+ test cases).
"""

import sys
import pytest
import time
from typing import Dict, Any
from datetime import datetime, timedelta

from monitoring_service_phase57 import (
    get_health_check_service, reset_health_check_service, HealthStatus,
    get_metrics_collector, reset_metrics_collector, MetricType,
    get_distributed_tracer, reset_distributed_tracer, TraceLevel,
    get_alert_manager, reset_alert_manager, AlertSeverity
)


class TestHealthCheckService:
    """Test health check monitoring service."""
    
    def setup_method(self):
        """Setup before each test."""
        reset_health_check_service()
    
    def test_register_health_check(self):
        """Test registering health check."""
        service = get_health_check_service()
        
        def mock_check():
            return {
                'status': HealthStatus.HEALTHY,
                'message': 'All good'
            }
        
        success = service.register_check("test_service", mock_check)
        assert success is True
        assert "test_service" in service.checks
    
    def test_run_health_check(self):
        """Test running health check."""
        service = get_health_check_service()
        
        def mock_check():
            return {
                'status': HealthStatus.HEALTHY,
                'message': 'Service is healthy'
            }
        
        service.register_check("api_service", mock_check)
        result = service.run_check("api_service")
        
        assert result is not None
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time_ms >= 0
    
    def test_run_all_health_checks(self):
        """Test running all health checks."""
        service = get_health_check_service()
        
        def check1():
            return {'status': HealthStatus.HEALTHY}
        
        def check2():
            return {'status': HealthStatus.HEALTHY}
        
        service.register_check("service1", check1)
        service.register_check("service2", check2)
        
        results = service.run_all_checks()
        assert len(results) == 2
        assert "service1" in results
        assert "service2" in results
    
    def test_get_overall_status(self):
        """Test getting overall system health."""
        service = get_health_check_service()
        
        def healthy_check():
            return {'status': HealthStatus.HEALTHY}
        
        def degraded_check():
            return {'status': HealthStatus.DEGRADED}
        
        service.register_check("good_service", healthy_check)
        service.register_check("bad_service", degraded_check)
        
        service.run_all_checks()
        overall = service.get_overall_status()
        
        assert overall == HealthStatus.DEGRADED
    
    def test_health_check_exception_handling(self):
        """Test health check with exceptions."""
        service = get_health_check_service()
        
        def failing_check():
            raise Exception("Service unreachable")
        
        service.register_check("failing_service", failing_check)
        result = service.run_check("failing_service")
        
        assert result is not None
        assert result.status == HealthStatus.UNHEALTHY
        assert "Service unreachable" in result.message


class TestMetricsCollector:
    """Test metrics collection service."""
    
    def setup_method(self):
        """Setup before each test."""
        reset_metrics_collector()
    
    def test_record_metric(self):
        """Test recording metric."""
        collector = get_metrics_collector()
        
        success = collector.record_metric(
            "cpu_usage",
            75.5,
            MetricType.GAUGE,
            {"host": "server1"}
        )
        
        assert success is True
    
    def test_record_counter(self):
        """Test recording counter metric."""
        collector = get_metrics_collector()
        
        collector.record_counter("requests_total", 10)
        collector.record_counter("requests_total", 5)
        
        summary = collector.get_metric_summary("requests_total")
        assert summary is not None
        assert summary['count'] == 2
        assert summary['sum'] == 15
    
    def test_record_gauge(self):
        """Test recording gauge metric."""
        collector = get_metrics_collector()
        
        collector.record_gauge("memory_usage", 60.0)
        collector.record_gauge("memory_usage", 70.0)
        collector.record_gauge("memory_usage", 65.0)
        
        summary = collector.get_metric_summary("memory_usage")
        assert summary is not None
        assert summary['count'] == 3
        assert summary['min'] == 60.0
        assert summary['max'] == 70.0
    
    def test_record_timer(self):
        """Test recording timer metric."""
        collector = get_metrics_collector()
        
        collector.record_timer("request_duration", 100.5)
        collector.record_timer("request_duration", 150.2)
        collector.record_timer("request_duration", 120.3)
        
        summary = collector.get_metric_summary("request_duration")
        assert summary is not None
        assert summary['count'] == 3
        assert abs(summary['avg'] - 123.67) < 1
    
    def test_metric_percentiles(self):
        """Test metric percentile calculations."""
        collector = get_metrics_collector()
        
        for i in range(1, 101):
            collector.record_metric("response_time", float(i))
        
        summary = collector.get_metric_summary("response_time")
        assert summary is not None
        assert summary['p50'] > 40
        assert summary['p95'] > 90
        assert summary['p99'] > 98
    
    def test_get_metric_summary(self):
        """Test getting metric summary."""
        collector = get_metrics_collector()
        
        collector.record_gauge("test_metric", 10.0)
        collector.record_gauge("test_metric", 20.0)
        collector.record_gauge("test_metric", 30.0)
        
        summary = collector.get_metric_summary("test_metric")
        assert summary is not None
        assert summary['count'] == 3
        assert summary['avg'] == 20.0
        assert summary['min'] == 10.0
        assert summary['max'] == 30.0


class TestDistributedTracer:
    """Test distributed tracing service."""
    
    def setup_method(self):
        """Setup before each test."""
        reset_distributed_tracer()
    
    def test_start_trace(self):
        """Test starting trace."""
        tracer = get_distributed_tracer()
        
        trace_id = tracer.start_trace()
        assert trace_id is not None
        assert trace_id.startswith("trace_")
    
    def test_start_trace_with_id(self):
        """Test starting trace with specific ID."""
        tracer = get_distributed_tracer()
        
        trace_id = tracer.start_trace("custom_trace_123")
        assert trace_id == "custom_trace_123"
    
    def test_add_span(self):
        """Test adding span to trace."""
        tracer = get_distributed_tracer()
        
        trace_id = tracer.start_trace()
        span_id = tracer.add_span(
            trace_id=trace_id,
            operation="db_query",
            service="database"
        )
        
        assert span_id is not None
        assert span_id.startswith("span_")
    
    def test_end_span(self):
        """Test ending span."""
        tracer = get_distributed_tracer()
        
        trace_id = tracer.start_trace()
        span_id = tracer.add_span(trace_id, "api_call", "api_service")
        
        success = tracer.end_span(trace_id, span_id, "success")
        assert success is True
        
        span = tracer.get_trace(trace_id)[0]
        assert span.end_time is not None
        assert span.duration_ms is not None
    
    def test_add_span_log(self):
        """Test adding log to span."""
        tracer = get_distributed_tracer()
        
        trace_id = tracer.start_trace()
        span_id = tracer.add_span(trace_id, "operation", "service")
        
        success = tracer.add_span_log(trace_id, span_id, "Operation started", TraceLevel.INFO)
        assert success is True
        
        span = tracer.get_trace(trace_id)[0]
        assert len(span.logs) > 0
        assert "Operation started" in span.logs[0]['message']
    
    def test_get_trace(self):
        """Test retrieving complete trace."""
        tracer = get_distributed_tracer()
        
        trace_id = tracer.start_trace()
        span1_id = tracer.add_span(trace_id, "operation1", "service1")
        span2_id = tracer.add_span(trace_id, "operation2", "service2", span1_id)
        
        spans = tracer.get_trace(trace_id)
        assert spans is not None
        assert len(spans) == 2
        assert spans[1].parent_span_id == span1_id
    
    def test_trace_with_tags(self):
        """Test trace with tags."""
        tracer = get_distributed_tracer()
        
        trace_id = tracer.start_trace()
        span_id = tracer.add_span(
            trace_id,
            "request",
            "api",
            tags={"http.method": "GET", "http.status_code": 200}
        )
        
        span = tracer.get_trace(trace_id)[0]
        assert span.tags["http.method"] == "GET"
        assert span.tags["http.status_code"] == 200


class TestAlertManager:
    """Test alert management service."""
    
    def setup_method(self):
        """Setup before each test."""
        reset_alert_manager()
    
    def test_create_alert(self):
        """Test creating alert."""
        manager = get_alert_manager()
        
        alert = manager.create_alert(
            service="api",
            severity=AlertSeverity.CRITICAL,
            message="High error rate detected",
            metric_name="error_rate",
            threshold=0.05,
            current_value=0.10
        )
        
        assert alert.alert_id is not None
        assert alert.service == "api"
        assert alert.severity == AlertSeverity.CRITICAL
    
    def test_get_active_alerts(self):
        """Test getting active alerts."""
        manager = get_alert_manager()
        
        alert1 = manager.create_alert(
            "service1", AlertSeverity.CRITICAL, "Alert 1",
            "metric1", 50, 60
        )
        alert2 = manager.create_alert(
            "service2", AlertSeverity.WARNING, "Alert 2",
            "metric2", 70, 75
        )
        
        active = manager.get_active_alerts()
        assert len(active) == 2
        
        critical_only = manager.get_active_alerts(AlertSeverity.CRITICAL)
        assert len(critical_only) == 1
    
    def test_resolve_alert(self):
        """Test resolving alert."""
        manager = get_alert_manager()
        
        alert = manager.create_alert(
            "service", AlertSeverity.WARNING, "Test alert",
            "metric", 50, 60
        )
        
        success = manager.resolve_alert(alert.alert_id)
        assert success is True
        
        active = manager.get_active_alerts()
        assert len(active) == 0
    
    def test_alert_history(self):
        """Test alert history tracking."""
        manager = get_alert_manager()
        
        manager.create_alert("s1", AlertSeverity.CRITICAL, "A1", "m1", 10, 20)
        manager.create_alert("s2", AlertSeverity.WARNING, "A2", "m2", 30, 40)
        manager.create_alert("s3", AlertSeverity.INFO, "A3", "m3", 50, 60)
        
        history = manager.get_alert_history()
        assert len(history) >= 3
    
    def test_alert_statistics(self):
        """Test alert statistics."""
        manager = get_alert_manager()
        
        manager.create_alert("s1", AlertSeverity.CRITICAL, "A1", "m1", 10, 20)
        manager.create_alert("s2", AlertSeverity.CRITICAL, "A2", "m2", 30, 40)
        manager.create_alert("s3", AlertSeverity.WARNING, "A3", "m3", 50, 60)
        
        stats = manager.get_statistics()
        assert stats['active_alerts'] == 3
        assert stats['critical_alerts'] == 2
        assert stats['warning_alerts'] == 1


class TestIntegrationScenarios:
    """Test integrated monitoring scenarios."""
    
    def setup_method(self):
        """Setup before each test."""
        reset_health_check_service()
        reset_metrics_collector()
        reset_distributed_tracer()
        reset_alert_manager()
    
    def test_end_to_end_monitoring(self):
        """Test complete monitoring workflow."""
        # Step 1: Register and run health check
        health_service = get_health_check_service()
        
        def api_health():
            return {'status': HealthStatus.HEALTHY}
        
        health_service.register_check("api", api_health)
        health_service.run_check("api")
        
        # Step 2: Record metrics
        metrics = get_metrics_collector()
        metrics.record_timer("api.response_time", 100)
        metrics.record_counter("api.requests", 5)
        
        # Step 3: Start trace
        tracer = get_distributed_tracer()
        trace_id = tracer.start_trace()
        span_id = tracer.add_span(trace_id, "handle_request", "api")
        tracer.end_span(trace_id, span_id)
        
        # Step 4: Check alerts
        alerts = get_alert_manager()
        alert = alerts.create_alert(
            "api", AlertSeverity.INFO, "Request processed",
            "requests", 5, 5
        )
        
        # Verify all components
        assert health_service.get_overall_status() == HealthStatus.HEALTHY
        assert metrics.get_metric_summary("api.response_time") is not None
        assert tracer.get_trace(trace_id) is not None
        assert alert.alert_id is not None
    
    def test_performance_under_load(self):
        """Test monitoring system under metrics load."""
        collector = get_metrics_collector()
        
        # Record many metrics
        for i in range(100):
            collector.record_metric(f"metric_{i % 10}", float(i), MetricType.GAUGE)
        
        stats = collector.get_statistics()
        assert stats['total_data_points'] == 100
        assert stats['metric_names'] == 10
    
    def test_trace_depth(self):
        """Test deep trace hierarchies."""
        tracer = get_distributed_tracer()
        
        trace_id = tracer.start_trace()
        parent_id = None
        
        # Create 10-level deep trace
        for level in range(10):
            span_id = tracer.add_span(
                trace_id,
                f"level_{level}",
                "service",
                parent_id
            )
            parent_id = span_id
        
        spans = tracer.get_trace(trace_id)
        assert len(spans) == 10
        assert spans[-1].parent_span_id == spans[-2].span_id


# ===================== TEST EXECUTION =====================

def run_all_tests():
    """Run all tests and report results."""
    test_classes = [
        TestHealthCheckService,
        TestMetricsCollector,
        TestDistributedTracer,
        TestAlertManager,
        TestIntegrationScenarios
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        instance = test_class()
        methods = [m for m in dir(instance) if m.startswith("test_")]
        
        for method in methods:
            total_tests += 1
            try:
                instance.setup_method()
                getattr(instance, method)()
                passed_tests += 1
                print(f"✓ {test_class.__name__}.{method}")
            except Exception as e:
                failed_tests.append((test_class.__name__, method, str(e)))
                print(f"✗ {test_class.__name__}.{method}: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"Test Summary: {passed_tests}/{total_tests} passed")
    print(f"{'='*60}")
    
    if failed_tests:
        print("\nFailed Tests:")
        for class_name, method, error in failed_tests:
            print(f"  - {class_name}.{method}")
            print(f"    Error: {error}")
        return False
    else:
        print("\n🎉 All tests passed!")
        return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
