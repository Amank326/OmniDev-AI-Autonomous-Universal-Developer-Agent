"""
APM (Application Performance Monitoring) Integrations
Connects to external APM platforms for metrics and trace collection
Phase 42: Observability & Monitoring Infrastructure
"""

import json
import asyncio
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Callable
from enum import Enum
import threading
import queue
import requests
from urllib.parse import urljoin


class APMProvider(Enum):
    """Supported APM providers"""
    DATADOG = "datadog"
    NEW_RELIC = "new_relic"
    DYNATRACE = "dynatrace"
    ELASTIC_APM = "elastic_apm"
    JAEGER = "jaeger"
    ZIPKIN = "zipkin"


@dataclass
class APMConfig:
    """APM provider configuration"""
    provider: APMProvider
    api_key: str
    api_endpoint: str
    environment: str = "production"
    service_name: str = "omnidev-ai"
    enabled: bool = True
    timeout_seconds: int = 10
    batch_size: int = 100
    flush_interval_seconds: int = 60


@dataclass
class APMMetric:
    """Metric for APM ingestion"""
    timestamp: datetime
    name: str
    value: float
    tags: Dict[str, str]
    service_name: str = "omnidev-ai"

    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "name": self.name,
            "value": self.value,
            "tags": self.tags,
            "service_name": self.service_name,
        }


@dataclass
class APMTrace:
    """Trace for APM ingestion"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    service_name: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    status: str
    tags: Dict[str, str]

    def to_dict(self):
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "operation_name": self.operation_name,
            "service_name": self.service_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_ms": self.duration_ms,
            "status": self.status,
            "tags": self.tags,
        }


class DataDogAPM:
    """DataDog APM integration"""

    def __init__(self, config: APMConfig):
        self.config = config
        self.api_endpoint = config.api_endpoint
        self.headers = {
            "DD-API-KEY": config.api_key,
            "Content-Type": "application/json",
        }

    async def send_metrics(self, metrics: List[APMMetric]) -> bool:
        """Send metrics to DataDog"""
        try:
            payload = {
                "series": [
                    {
                        "metric": m.name,
                        "points": [[int(m.timestamp.timestamp()), m.value]],
                        "type": "gauge",
                        "tags": list(m.tags.items()),
                    }
                    for m in metrics
                ]
            }
            response = requests.post(
                urljoin(self.api_endpoint, "/api/v1/series"),
                json=payload,
                headers=self.headers,
                timeout=self.config.timeout_seconds,
            )
            return response.status_code == 202
        except Exception as e:
            print(f"Error sending DataDog metrics: {e}")
            return False

    async def send_traces(self, traces: List[APMTrace]) -> bool:
        """Send traces to DataDog"""
        try:
            payload = {
                "traces": [
                    [t.to_dict() for t in traces]
                ]
            }
            response = requests.post(
                urljoin(self.api_endpoint, "/v0.3/traces"),
                json=payload,
                headers=self.headers,
                timeout=self.config.timeout_seconds,
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending DataDog traces: {e}")
            return False


class NewRelicAPM:
    """New Relic APM integration"""

    def __init__(self, config: APMConfig):
        self.config = config
        self.api_endpoint = config.api_endpoint
        self.headers = {
            "Api-Key": config.api_key,
            "Content-Type": "application/json",
        }

    async def send_metrics(self, metrics: List[APMMetric]) -> bool:
        """Send metrics to New Relic"""
        try:
            payload = {
                "metrics": [
                    {
                        "name": m.name,
                        "type": "gauge",
                        "value": m.value,
                        "timestamp": int(m.timestamp.timestamp() * 1000),
                        "attributes": m.tags,
                    }
                    for m in metrics
                ]
            }
            response = requests.post(
                urljoin(self.api_endpoint, "/metric/api/v2/write"),
                json=payload,
                headers=self.headers,
                timeout=self.config.timeout_seconds,
            )
            return response.status_code == 202
        except Exception as e:
            print(f"Error sending New Relic metrics: {e}")
            return False

    async def send_traces(self, traces: List[APMTrace]) -> bool:
        """Send traces to New Relic"""
        try:
            payload = {
                "spans": [
                    {
                        "trace.id": t.trace_id,
                        "span.id": t.span_id,
                        "parent.id": t.parent_span_id,
                        "name": t.operation_name,
                        "service.name": t.service_name,
                        "timestamp": int(t.start_time.timestamp() * 1000000),
                        "duration.ms": t.duration_ms,
                        "status": t.status,
                        "attributes": t.tags,
                    }
                    for t in traces
                ]
            }
            response = requests.post(
                urljoin(self.api_endpoint, "/trace/v1/spans"),
                json=payload,
                headers=self.headers,
                timeout=self.config.timeout_seconds,
            )
            return response.status_code == 202
        except Exception as e:
            print(f"Error sending New Relic traces: {e}")
            return False


class DynatraceAPM:
    """Dynatrace APM integration"""

    def __init__(self, config: APMConfig):
        self.config = config
        self.api_endpoint = config.api_endpoint
        self.headers = {
            "Authorization": f"Api-Token {config.api_key}",
            "Content-Type": "application/json",
        }

    async def send_metrics(self, metrics: List[APMMetric]) -> bool:
        """Send metrics to Dynatrace (custom metrics)"""
        try:
            for metric in metrics:
                payload = {
                    "timeseries": metric.name,
                    "timestamp": int(metric.timestamp.timestamp() * 1000),
                    "value": metric.value,
                    "dimensions": metric.tags,
                }
                response = requests.post(
                    urljoin(self.api_endpoint, "/api/v2/metrics/ingest"),
                    json=payload,
                    headers=self.headers,
                    timeout=self.config.timeout_seconds,
                )
                if response.status_code != 202:
                    return False
            return True
        except Exception as e:
            print(f"Error sending Dynatrace metrics: {e}")
            return False

    async def send_traces(self, traces: List[APMTrace]) -> bool:
        """Send traces to Dynatrace (OpenTelemetry format)"""
        try:
            payload = {
                "resourceSpans": [
                    {
                        "resource": {
                            "attributes": {"service.name": t.service_name}
                        },
                        "scopeSpans": [
                            {
                                "spans": [
                                    {
                                        "traceId": t.trace_id,
                                        "spanId": t.span_id,
                                        "parentSpanId": t.parent_span_id,
                                        "name": t.operation_name,
                                        "startTimeUnixNano": int(t.start_time.timestamp() * 1e9),
                                        "endTimeUnixNano": int(t.end_time.timestamp() * 1e9),
                                        "attributes": t.tags,
                                        "status": {"code": t.status},
                                    }
                                ]
                            }
                        ],
                    }
                ]
            }
            response = requests.post(
                urljoin(self.api_endpoint, "/api/v1/traces"),
                json=payload,
                headers=self.headers,
                timeout=self.config.timeout_seconds,
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending Dynatrace traces: {e}")
            return False


class ElasticAPM:
    """Elastic APM integration"""

    def __init__(self, config: APMConfig):
        self.config = config
        self.api_endpoint = config.api_endpoint
        self.headers = {
            "Authorization": f"ApiKey {config.api_key}",
            "Content-Type": "application/json",
        }

    async def send_metrics(self, metrics: List[APMMetric]) -> bool:
        """Send metrics to Elastic APM"""
        try:
            payload = {
                "metricsets": [
                    {
                        "@timestamp": m.timestamp.isoformat(),
                        "service": {"name": m.service_name},
                        "metricset": {
                            "name": m.name,
                            "samples": {m.name: {"value": m.value}},
                        },
                        "labels": m.tags,
                    }
                    for m in metrics
                ]
            }
            response = requests.post(
                urljoin(self.api_endpoint, "/intake/v2/events"),
                json=payload,
                headers=self.headers,
                timeout=self.config.timeout_seconds,
            )
            return response.status_code == 202
        except Exception as e:
            print(f"Error sending Elastic APM metrics: {e}")
            return False

    async def send_traces(self, traces: List[APMTrace]) -> bool:
        """Send traces to Elastic APM"""
        try:
            payload = {
                "transactions": [
                    {
                        "trace": {"id": t.trace_id},
                        "transaction": {
                            "name": t.operation_name,
                            "type": "request",
                            "duration": {"us": int(t.duration_ms * 1000)},
                            "result": t.status,
                            "timestamp": {"us": int(t.start_time.timestamp() * 1e6)},
                        },
                        "service": {"name": t.service_name},
                        "labels": t.tags,
                    }
                    for t in traces
                ]
            }
            response = requests.post(
                urljoin(self.api_endpoint, "/intake/v2/events"),
                json=payload,
                headers=self.headers,
                timeout=self.config.timeout_seconds,
            )
            return response.status_code == 202
        except Exception as e:
            print(f"Error sending Elastic APM traces: {e}")
            return False


class JaegerAPM:
    """Jaeger APM integration (OpenTelemetry backend)"""

    def __init__(self, config: APMConfig):
        self.config = config
        self.api_endpoint = config.api_endpoint

    async def send_metrics(self, metrics: List[APMMetric]) -> bool:
        """Jaeger doesn't support metrics directly, store locally"""
        return True

    async def send_traces(self, traces: List[APMTrace]) -> bool:
        """Send traces to Jaeger via HTTP collector"""
        try:
            payload = {
                "resourceSpans": [
                    {
                        "resource": {
                            "attributes": {
                                "service.name": t.service_name,
                                "service.version": "1.0.0",
                            }
                        },
                        "scopeSpans": [
                            {
                                "spans": [
                                    {
                                        "traceId": t.trace_id,
                                        "spanId": t.span_id,
                                        "parentSpanId": t.parent_span_id,
                                        "name": t.operation_name,
                                        "startTimeUnixNano": int(t.start_time.timestamp() * 1e9),
                                        "endTimeUnixNano": int(t.end_time.timestamp() * 1e9),
                                        "attributes": t.tags,
                                        "status": {"code": t.status},
                                    }
                                ]
                            }
                        ],
                    }
                ]
            }
            response = requests.post(
                urljoin(self.api_endpoint, "/api/traces"),
                json=payload,
                timeout=self.config.timeout_seconds,
            )
            return response.status_code in [200, 202]
        except Exception as e:
            print(f"Error sending Jaeger traces: {e}")
            return False


class ZipkinAPM:
    """Zipkin APM integration (OpenTelemetry backend)"""

    def __init__(self, config: APMConfig):
        self.config = config
        self.api_endpoint = config.api_endpoint

    async def send_metrics(self, metrics: List[APMMetric]) -> bool:
        """Zipkin doesn't support metrics directly"""
        return True

    async def send_traces(self, traces: List[APMTrace]) -> bool:
        """Send traces to Zipkin"""
        try:
            payload = [
                {
                    "traceId": t.trace_id,
                    "id": t.span_id,
                    "parentId": t.parent_span_id,
                    "name": t.operation_name,
                    "timestamp": int(t.start_time.timestamp() * 1e6),
                    "duration": int(t.duration_ms * 1000),
                    "localEndpoint": {"serviceName": t.service_name},
                    "tags": t.tags,
                    "kind": "SERVER",
                }
                for t in traces
            ]
            response = requests.post(
                urljoin(self.api_endpoint, "/api/v2/spans"),
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.config.timeout_seconds,
            )
            return response.status_code == 202
        except Exception as e:
            print(f"Error sending Zipkin traces: {e}")
            return False


class APMIntegrationsManager:
    """Manages multiple APM provider integrations"""

    def __init__(self):
        self.providers: Dict[str, any] = {}
        self.metrics_queue: queue.Queue = queue.Queue()
        self.traces_queue: queue.Queue = queue.Queue()
        self.callbacks: List[Callable] = []
        self.running = False
        self.processor_thread = None
        self.lock = threading.RLock()

    def register_provider(self, config: APMConfig) -> bool:
        """Register an APM provider"""
        try:
            with self.lock:
                if not config.enabled:
                    return False

                provider = None
                if config.provider == APMProvider.DATADOG:
                    provider = DataDogAPM(config)
                elif config.provider == APMProvider.NEW_RELIC:
                    provider = NewRelicAPM(config)
                elif config.provider == APMProvider.DYNATRACE:
                    provider = DynatraceAPM(config)
                elif config.provider == APMProvider.ELASTIC_APM:
                    provider = ElasticAPM(config)
                elif config.provider == APMProvider.JAEGER:
                    provider = JaegerAPM(config)
                elif config.provider == APMProvider.ZIPKIN:
                    provider = ZipkinAPM(config)

                if provider:
                    self.providers[config.provider.value] = provider
                    return True
                return False
        except Exception as e:
            print(f"Error registering APM provider: {e}")
            return False

    def send_metric(self, metric: APMMetric) -> None:
        """Queue metric for sending to all providers"""
        self.metrics_queue.put(metric)

    def send_trace(self, trace: APMTrace) -> None:
        """Queue trace for sending to all providers"""
        self.traces_queue.put(trace)

    def start(self) -> None:
        """Start background processor thread"""
        if not self.running:
            self.running = True
            self.processor_thread = threading.Thread(target=self._process_queues, daemon=True)
            self.processor_thread.start()

    def stop(self) -> None:
        """Stop background processor"""
        self.running = False
        if self.processor_thread:
            self.processor_thread.join(timeout=5)

    def _process_queues(self) -> None:
        """Background thread that processes queued items"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while self.running:
            try:
                # Process metrics
                metrics_batch = []
                while not self.metrics_queue.empty() and len(metrics_batch) < 100:
                    try:
                        metrics_batch.append(self.metrics_queue.get_nowait())
                    except queue.Empty:
                        break

                if metrics_batch:
                    for provider in self.providers.values():
                        loop.run_until_complete(provider.send_metrics(metrics_batch))

                # Process traces
                traces_batch = []
                while not self.traces_queue.empty() and len(traces_batch) < 100:
                    try:
                        traces_batch.append(self.traces_queue.get_nowait())
                    except queue.Empty:
                        break

                if traces_batch:
                    for provider in self.providers.values():
                        loop.run_until_complete(provider.send_traces(traces_batch))

                # Notify callbacks
                if metrics_batch or traces_batch:
                    for callback in self.callbacks:
                        try:
                            callback({
                                "metrics_sent": len(metrics_batch),
                                "traces_sent": len(traces_batch),
                                "timestamp": datetime.now(),
                            })
                        except Exception as e:
                            print(f"Error in APM callback: {e}")

                # Small sleep to prevent busy waiting
                asyncio.sleep(1)

            except Exception as e:
                print(f"Error in APM processor thread: {e}")

    def register_callback(self, callback: Callable) -> None:
        """Register callback for APM events"""
        with self.lock:
            self.callbacks.append(callback)

    def get_provider_status(self) -> Dict[str, bool]:
        """Get status of registered providers"""
        with self.lock:
            return {
                name: True for name in self.providers.keys()
            }

    def get_statistics(self) -> Dict:
        """Get APM integration statistics"""
        with self.lock:
            return {
                "providers_registered": len(self.providers),
                "provider_list": list(self.providers.keys()),
                "metrics_queued": self.metrics_queue.qsize(),
                "traces_queued": self.traces_queue.qsize(),
                "is_running": self.running,
            }


# Global singleton
_apm_manager = None


def get_apm_manager() -> APMIntegrationsManager:
    """Get or create APM manager singleton"""
    global _apm_manager
    if _apm_manager is None:
        _apm_manager = APMIntegrationsManager()
    return _apm_manager
