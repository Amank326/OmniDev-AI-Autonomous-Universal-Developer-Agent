"""
Data Pipeline Builder - Visual pipeline design and orchestration
Supports ETL workflows, transformations, data routing, scheduling
"""

import json
import time
import threading
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import dateutil.parser


class PipelineNodeType(Enum):
    """Pipeline node types"""
    SOURCE = "source"  # Input source (files, APIs, streams)
    TRANSFORM = "transform"  # Data transformation
    FILTER = "filter"  # Conditional filtering
    AGGREGATE = "aggregate"  # Data aggregation
    JOIN = "join"  # Data joining
    SINK = "sink"  # Output destination
    BRANCH = "branch"  # Branching logic
    LOOP = "loop"  # Looping construct
    CONDITIONAL = "conditional"  # If/else logic


class ExecutionStatus(Enum):
    """Pipeline execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class ScheduleType(Enum):
    """Pipeline schedule types"""
    ONCE = "once"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"
    ON_DEMAND = "on_demand"


@dataclass
class PipelineNodeConfig:
    """Configuration for pipeline node"""
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_type: PipelineNodeType = PipelineNodeType.TRANSFORM
    name: str = ""
    description: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    input_mapping: Dict[str, str] = field(default_factory=dict)  # input name -> source field
    output_mapping: Dict[str, str] = field(default_factory=dict)  # output field -> column name
    error_handling: str = "fail"  # fail, skip, log
    timeout_seconds: int = 300
    retry_count: int = 0
    retry_delay_seconds: int = 60
    enabled: bool = True
    dependencies: List[str] = field(default_factory=list)  # Node IDs this depends on


@dataclass
class PipelineEdge:
    """Connection between pipeline nodes"""
    edge_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_node_id: str = ""
    target_node_id: str = ""
    condition: Optional[Dict[str, Any]] = None  # For conditional edges
    transform_func: Optional[str] = None  # Optional transform on edge
    pass_through_columns: List[str] = field(default_factory=list)
    filter_expression: Optional[str] = None  # For filter edges


@dataclass
class PipelineExecution:
    """Single execution of a pipeline"""
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_id: str = ""
    status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    node_executions: Dict[str, Dict] = field(default_factory=dict)  # node_id -> execution details
    total_records_processed: int = 0
    total_records_failed: int = 0
    error_message: Optional[str] = None
    triggered_by: str = "system"  # user, schedule, api
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> float:
        """Get execution duration"""
        if self.started_at is None:
            return 0.0
        end = self.completed_at or time.time()
        return end - self.started_at


@dataclass
class PipelineSchedule:
    """Pipeline execution schedule"""
    schedule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_id: str = ""
    schedule_type: ScheduleType = ScheduleType.ON_DEMAND
    cron_expression: Optional[str] = None  # For cron schedules
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    timezone: str = "UTC"
    is_active: bool = True
    last_triggered: Optional[float] = None
    next_trigger: Optional[float] = None


@dataclass
class PipelineStatistics:
    """Pipeline statistics"""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_records_processed: int = 0
    total_records_failed: int = 0
    avg_execution_time_seconds: float = 0.0
    success_rate: float = 100.0


class DataPipeline:
    """Represents a single data pipeline"""
    
    def __init__(self, pipeline_id: str, name: str):
        self.pipeline_id = pipeline_id
        self.name = name
        self.description = ""
        self.nodes: Dict[str, PipelineNodeConfig] = {}
        self.edges: Dict[str, PipelineEdge] = {}
        self.variables: Dict[str, Any] = {}
        self.created_at = time.time()
        self.updated_at = time.time()
        self.lock = threading.RLock()
    
    def add_node(self, config: PipelineNodeConfig) -> bool:
        """Add node to pipeline"""
        with self.lock:
            if config.node_id in self.nodes:
                return False
            self.nodes[config.node_id] = config
            self.updated_at = time.time()
            return True
    
    def remove_node(self, node_id: str) -> bool:
        """Remove node from pipeline"""
        with self.lock:
            if node_id not in self.nodes:
                return False
            
            del self.nodes[node_id]
            
            # Remove edges involving this node
            edges_to_remove = [
                eid for eid, edge in self.edges.items()
                if edge.source_node_id == node_id or edge.target_node_id == node_id
            ]
            for eid in edges_to_remove:
                del self.edges[eid]
            
            self.updated_at = time.time()
            return True
    
    def add_edge(self, edge: PipelineEdge) -> bool:
        """Add connection between nodes"""
        with self.lock:
            if edge.source_node_id not in self.nodes or edge.target_node_id not in self.nodes:
                return False
            
            self.edges[edge.edge_id] = edge
            self.updated_at = time.time()
            return True
    
    def remove_edge(self, edge_id: str) -> bool:
        """Remove connection"""
        with self.lock:
            if edge_id not in self.edges:
                return False
            del self.edges[edge_id]
            self.updated_at = time.time()
            return True
    
    def get_node_inputs(self, node_id: str) -> List[str]:
        """Get input nodes for a node"""
        inputs = []
        for edge in self.edges.values():
            if edge.target_node_id == node_id:
                inputs.append(edge.source_node_id)
        return inputs
    
    def get_node_outputs(self, node_id: str) -> List[str]:
        """Get output nodes from a node"""
        outputs = []
        for edge in self.edges.values():
            if edge.source_node_id == node_id:
                outputs.append(edge.target_node_id)
        return outputs
    
    def get_execution_order(self) -> Optional[List[str]]:
        """Get topological sort of nodes for execution"""
        # Simple topological sort
        visited: Set[str] = set()
        order = []
        temp_mark: Set[str] = set()
        
        def visit(node_id: str) -> bool:
            if node_id in temp_mark:
                return False  # Cycle detected
            if node_id in visited:
                return True
            
            temp_mark.add(node_id)
            for input_id in self.get_node_inputs(node_id):
                if not visit(input_id):
                    return False
            
            temp_mark.remove(node_id)
            visited.add(node_id)
            order.append(node_id)
            return True
        
        for node_id in self.nodes.keys():
            if not visit(node_id):
                return None  # Cycle detected
        
        return order
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate pipeline integrity"""
        errors = []
        
        # Check for cycles
        if self.get_execution_order() is None:
            errors.append("Pipeline contains circular dependencies")
        
        # Check all edges reference valid nodes
        for edge in self.edges.values():
            if edge.source_node_id not in self.nodes:
                errors.append(f"Edge references non-existent source node: {edge.source_node_id}")
            if edge.target_node_id not in self.nodes:
                errors.append(f"Edge references non-existent target node: {edge.target_node_id}")
        
        # Check source nodes
        source_nodes = [n for n in self.nodes.values() if n.node_type == PipelineNodeType.SOURCE]
        if not source_nodes:
            errors.append("Pipeline must have at least one source node")
        
        # Check sink nodes
        sink_nodes = [n for n in self.nodes.values() if n.node_type == PipelineNodeType.SINK]
        if not sink_nodes:
            errors.append("Pipeline must have at least one sink node")
        
        return len(errors) == 0, errors
    
    def to_dict(self) -> Dict:
        """Convert pipeline to dictionary"""
        return {
            "pipeline_id": self.pipeline_id,
            "name": self.name,
            "description": self.description,
            "nodes": {nid: {
                "node_id": n.node_id,
                "type": n.node_type.value,
                "name": n.name,
                "config": n.config,
            } for nid, n in self.nodes.items()},
            "edges": {eid: {
                "source": e.source_node_id,
                "target": e.target_node_id,
            } for eid, e in self.edges.items()},
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class DataPipelineBuilder:
    """Builder for creating and managing data pipelines"""
    
    def __init__(self):
        self.pipelines: Dict[str, DataPipeline] = {}
        self.executions: Dict[str, PipelineExecution] = {}
        self.schedules: Dict[str, PipelineSchedule] = {}
        self.statistics: Dict[str, PipelineStatistics] = {}
        self.lock = threading.RLock()
        self.callbacks: List[Callable] = []
        self.execution_threads: Dict[str, threading.Thread] = {}
    
    def create_pipeline(self, name: str, description: str = "") -> DataPipeline:
        """Create new pipeline"""
        with self.lock:
            pipeline_id = str(uuid.uuid4())
            pipeline = DataPipeline(pipeline_id, name)
            pipeline.description = description
            self.pipelines[pipeline_id] = pipeline
            self.statistics[pipeline_id] = PipelineStatistics()
            
            self._trigger_callback("pipeline_created", pipeline_id, name)
            return pipeline
    
    def get_pipeline(self, pipeline_id: str) -> Optional[DataPipeline]:
        """Get pipeline"""
        with self.lock:
            return self.pipelines.get(pipeline_id)
    
    def delete_pipeline(self, pipeline_id: str) -> bool:
        """Delete pipeline"""
        with self.lock:
            if pipeline_id not in self.pipelines:
                return False
            
            del self.pipelines[pipeline_id]
            if pipeline_id in self.statistics:
                del self.statistics[pipeline_id]
            
            self._trigger_callback("pipeline_deleted", pipeline_id)
            return True
    
    def list_pipelines(self) -> List[DataPipeline]:
        """List all pipelines"""
        with self.lock:
            return list(self.pipelines.values())
    
    def add_source_node(self, pipeline_id: str, source_type: str,
                       source_config: Dict) -> Optional[str]:
        """Add source node to pipeline"""
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            return None
        
        config = PipelineNodeConfig(
            node_type=PipelineNodeType.SOURCE,
            name=f"Source: {source_type}",
            config={"source_type": source_type, **source_config}
        )
        
        if pipeline.add_node(config):
            self._trigger_callback("node_added", pipeline_id, config.node_id)
            return config.node_id
        return None
    
    def add_transform_node(self, pipeline_id: str, transform_func: str,
                          output_schema: Dict) -> Optional[str]:
        """Add transformation node"""
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            return None
        
        config = PipelineNodeConfig(
            node_type=PipelineNodeType.TRANSFORM,
            name="Transform",
            config={"function": transform_func, "output_schema": output_schema}
        )
        
        if pipeline.add_node(config):
            self._trigger_callback("node_added", pipeline_id, config.node_id)
            return config.node_id
        return None
    
    def add_sink_node(self, pipeline_id: str, sink_type: str,
                     sink_config: Dict) -> Optional[str]:
        """Add sink (output) node"""
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            return None
        
        config = PipelineNodeConfig(
            node_type=PipelineNodeType.SINK,
            name=f"Sink: {sink_type}",
            config={"sink_type": sink_type, **sink_config}
        )
        
        if pipeline.add_node(config):
            self._trigger_callback("node_added", pipeline_id, config.node_id)
            return config.node_id
        return None
    
    def connect_nodes(self, pipeline_id: str, source_node_id: str,
                     target_node_id: str) -> Optional[str]:
        """Connect two nodes"""
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            return None
        
        edge = PipelineEdge(
            source_node_id=source_node_id,
            target_node_id=target_node_id
        )
        
        if pipeline.add_edge(edge):
            self._trigger_callback("nodes_connected", pipeline_id, edge.edge_id)
            return edge.edge_id
        return None
    
    def execute_pipeline(self, pipeline_id: str, variables: Optional[Dict] = None,
                        triggered_by: str = "api") -> Optional[str]:
        """Execute pipeline"""
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            return None
        
        # Validate pipeline
        is_valid, errors = pipeline.validate()
        if not is_valid:
            self._trigger_callback("pipeline_validation_failed", pipeline_id, errors)
            return None
        
        # Create execution record
        execution = PipelineExecution(
            pipeline_id=pipeline_id,
            triggered_by=triggered_by,
            metadata={"variables": variables or {}}
        )
        
        with self.lock:
            self.executions[execution.execution_id] = execution
        
        # Start execution in background thread
        thread = threading.Thread(
            target=self._execute_pipeline_worker,
            args=(execution.execution_id, pipeline_id, variables or {}),
            daemon=True
        )
        self.execution_threads[execution.execution_id] = thread
        thread.start()
        
        self._trigger_callback("pipeline_execution_started", execution.execution_id)
        return execution.execution_id
    
    def _execute_pipeline_worker(self, execution_id: str, pipeline_id: str, variables: Dict) -> None:
        """Worker thread for pipeline execution"""
        execution = self.executions[execution_id]
        pipeline = self.pipelines[pipeline_id]
        
        try:
            execution.started_at = time.time()
            execution.status = ExecutionStatus.RUNNING
            
            # Get execution order
            node_order = pipeline.get_execution_order()
            if not node_order:
                raise ValueError("Pipeline contains circular dependencies")
            
            # Execute nodes in order
            node_outputs = {}
            for node_id in node_order:
                node = pipeline.nodes[node_id]
                
                # Get node inputs
                inputs = {}
                for input_node_id in pipeline.get_node_inputs(node_id):
                    if input_node_id in node_outputs:
                        inputs[input_node_id] = node_outputs[input_node_id]
                
                # Simulate node execution
                result = self._execute_node(node, inputs, variables)
                node_outputs[node_id] = result
                
                execution.node_executions[node_id] = {
                    "status": "completed",
                    "start_time": time.time(),
                    "duration_seconds": 0.1,
                    "records_processed": result.get("records", 0),
                }
            
            execution.total_records_processed = sum(
                ne.get("records_processed", 0) 
                for ne in execution.node_executions.values()
            )
            execution.status = ExecutionStatus.SUCCESS
            
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.total_records_failed += 1
        
        finally:
            execution.completed_at = time.time()
            self._trigger_callback("pipeline_execution_completed", execution_id, execution.status)
    
    def _execute_node(self, node: PipelineNodeConfig, inputs: Dict, variables: Dict) -> Dict:
        """Execute a single node"""
        # Simulate node execution
        if node.node_type == PipelineNodeType.SOURCE:
            return {"records": 100, "data": []}
        elif node.node_type == PipelineNodeType.TRANSFORM:
            input_records = sum(inp.get("records", 0) for inp in inputs.values())
            return {"records": input_records, "data": []}
        elif node.node_type == PipelineNodeType.FILTER:
            input_records = sum(inp.get("records", 0) for inp in inputs.values())
            return {"records": int(input_records * 0.8), "data": []}
        elif node.node_type == PipelineNodeType.AGGREGATE:
            return {"records": 1, "data": []}
        else:
            return {"records": 0, "data": []}
    
    def get_execution_status(self, execution_id: str) -> Optional[PipelineExecution]:
        """Get execution status"""
        with self.lock:
            return self.executions.get(execution_id)
    
    def get_execution_history(self, pipeline_id: str, limit: int = 10) -> List[PipelineExecution]:
        """Get execution history for pipeline"""
        with self.lock:
            history = [
                ex for ex in self.executions.values()
                if ex.pipeline_id == pipeline_id
            ]
            return sorted(history, key=lambda x: x.started_at or 0, reverse=True)[:limit]
    
    def create_schedule(self, pipeline_id: str, schedule_type: ScheduleType) -> Optional[str]:
        """Create execution schedule"""
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            return None
        
        schedule = PipelineSchedule(
            pipeline_id=pipeline_id,
            schedule_type=schedule_type
        )
        
        with self.lock:
            self.schedules[schedule.schedule_id] = schedule
        
        self._trigger_callback("schedule_created", schedule.schedule_id)
        return schedule.schedule_id
    
    def get_pipeline_statistics(self, pipeline_id: str) -> Optional[Dict]:
        """Get pipeline statistics"""
        with self.lock:
            if pipeline_id not in self.statistics:
                return None
            
            stats = self.statistics[pipeline_id]
            return {
                "total_executions": stats.total_executions,
                "successful_executions": stats.successful_executions,
                "failed_executions": stats.failed_executions,
                "success_rate": stats.success_rate,
                "avg_execution_time": stats.avg_execution_time_seconds,
                "total_records_processed": stats.total_records_processed,
            }
    
    def register_callback(self, callback: Callable[[str, ...], None]) -> None:
        """Register event callback"""
        with self.lock:
            self.callbacks.append(callback)
    
    def _trigger_callback(self, event_type: str, *args, **kwargs) -> None:
        """Trigger callbacks"""
        for callback in self.callbacks:
            try:
                callback(event_type, *args, **kwargs)
            except Exception:
                pass


# Singleton instance
_pipeline_builder: Optional[DataPipelineBuilder] = None


def get_pipeline_builder() -> DataPipelineBuilder:
    """Get or create singleton pipeline builder"""
    global _pipeline_builder
    if _pipeline_builder is None:
        _pipeline_builder = DataPipelineBuilder()
    return _pipeline_builder


def reset_pipeline_builder() -> None:
    """Reset pipeline builder (for testing)"""
    global _pipeline_builder
    _pipeline_builder = None
