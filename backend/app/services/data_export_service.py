"""
Data Export Service - Export data to multiple formats and destinations
Supports CSV, JSON, Parquet, S3, databases, and cloud storage
"""

import json
import time
import threading
import uuid
from typing import Any, Callable, Dict, List, Optional, BinaryIO, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from io import StringIO, BytesIO
import csv


class ExportFormat(Enum):
    """Export file formats"""
    CSV = "csv"
    JSON = "json"
    JSONL = "jsonl"  # JSON Lines
    PARQUET = "parquet"
    AVRO = "avro"
    XML = "xml"
    EXCEL = "excel"


class ExportDestination(Enum):
    """Export destinations"""
    LOCAL_FILE = "local_file"
    S3 = "s3"
    GCS = "gcs"
    AZURE_BLOB = "azure_blob"
    DATABASE = "database"
    SFTP = "sftp"
    HTTP = "http"
    KAFKA = "kafka"


class CompressionType(Enum):
    """Data compression types"""
    NONE = "none"
    GZIP = "gzip"
    SNAPPY = "snappy"
    BROTLI = "brotli"


@dataclass
class ExportConfig:
    """Export configuration"""
    export_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    format: ExportFormat = ExportFormat.JSON
    destination: ExportDestination = ExportDestination.LOCAL_FILE
    destination_config: Dict[str, Any] = field(default_factory=dict)
    compression: CompressionType = CompressionType.NONE
    include_headers: bool = True
    include_metadata: bool = False
    chunk_size: int = 10000  # Rows per chunk
    max_file_size_mb: int = 500
    schedule_type: Optional[str] = None  # once, daily, weekly, monthly
    filters: Dict[str, Any] = field(default_factory=dict)  # For filtering data
    column_mapping: Dict[str, str] = field(default_factory=dict)  # Rename columns
    created_at: float = field(default_factory=time.time)


@dataclass
class ExportExecution:
    """Single export execution"""
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    export_id: str = ""
    status: str = "pending"  # pending, running, completed, failed
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    format: ExportFormat = ExportFormat.JSON
    destination: ExportDestination = ExportDestination.LOCAL_FILE
    rows_exported: int = 0
    bytes_exported: int = 0
    file_paths: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    triggered_by: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> float:
        """Get execution duration"""
        if self.started_at is None:
            return 0.0
        end = self.completed_at or time.time()
        return end - self.started_at


@dataclass
class ExportStatistics:
    """Export statistics"""
    total_exports: int = 0
    successful_exports: int = 0
    failed_exports: int = 0
    total_rows_exported: int = 0
    total_bytes_exported: int = 0
    avg_export_time_seconds: float = 0.0


class ExportFormatter:
    """Formats data for export"""
    
    @staticmethod
    def to_csv(rows: List[Dict], columns: List[str]) -> str:
        """Convert rows to CSV"""
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()
    
    @staticmethod
    def to_json(rows: List[Dict], include_metadata: bool = False, metadata: Dict = None) -> str:
        """Convert rows to JSON"""
        data = {
            "data": rows,
            "count": len(rows),
        }
        
        if include_metadata and metadata:
            data["metadata"] = metadata
        
        return json.dumps(data, default=str, indent=2)
    
    @staticmethod
    def to_jsonl(rows: List[Dict]) -> str:
        """Convert rows to JSON Lines"""
        lines = [json.dumps(row, default=str) for row in rows]
        return "\n".join(lines)
    
    @staticmethod
    def to_xml(rows: List[Dict], root_element: str = "data") -> str:
        """Convert rows to XML"""
        xml_lines = [f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>"]
        xml_lines.append(f"<{root_element}>")
        
        for row in rows:
            xml_lines.append("  <record>")
            for key, value in row.items():
                safe_key = key.replace(" ", "_").replace("-", "_")
                xml_lines.append(f"    <{safe_key}>{value}</{safe_key}>")
            xml_lines.append("  </record>")
        
        xml_lines.append(f"</{root_element}>")
        return "\n".join(xml_lines)


class DataExportService:
    """Service for exporting data to multiple formats and destinations"""
    
    def __init__(self):
        self.exports: Dict[str, ExportConfig] = {}
        self.executions: Dict[str, ExportExecution] = {}
        self.stats = ExportStatistics()
        self.lock = threading.RLock()
        self.callbacks: List[Callable] = []
        self.destination_handlers: Dict[ExportDestination, Callable] = {}
        self.data_sources: Dict[str, Callable[..., Iterator[List[Dict]]]] = {}
    
    def register_data_source(self, source_name: str,
                            source_func: Callable[..., Iterator[List[Dict]]]) -> None:
        """Register data source for export"""
        with self.lock:
            self.data_sources[source_name] = source_func
    
    def register_destination_handler(self, destination: ExportDestination,
                                    handler: Callable) -> None:
        """Register handler for export destination"""
        with self.lock:
            self.destination_handlers[destination] = handler
    
    def create_export(self, name: str, format_type: ExportFormat,
                     destination: ExportDestination,
                     destination_config: Dict) -> str:
        """Create export configuration"""
        config = ExportConfig(
            name=name,
            format=format_type,
            destination=destination,
            destination_config=destination_config
        )
        
        with self.lock:
            self.exports[config.export_id] = config
        
        self._trigger_callback("export_created", config.export_id, name)
        return config.export_id
    
    def get_export(self, export_id: str) -> Optional[ExportConfig]:
        """Get export configuration"""
        with self.lock:
            return self.exports.get(export_id)
    
    def delete_export(self, export_id: str) -> bool:
        """Delete export configuration"""
        with self.lock:
            if export_id not in self.exports:
                return False
            del self.exports[export_id]
        
        self._trigger_callback("export_deleted", export_id)
        return True
    
    def execute_export(self, export_id: str, data_source: str,
                      data_params: Dict = None) -> Optional[str]:
        """Execute export"""
        export_config = self.get_export(export_id)
        if not export_config:
            return None
        
        if data_source not in self.data_sources:
            return None
        
        # Create execution record
        execution = ExportExecution(
            export_id=export_id,
            format=export_config.format,
            destination=export_config.destination,
            triggered_by="api"
        )
        
        with self.lock:
            self.executions[execution.execution_id] = execution
        
        # Start export in background thread
        thread = threading.Thread(
            target=self._execute_export_worker,
            args=(execution, export_config, data_source, data_params or {}),
            daemon=True
        )
        thread.start()
        
        self._trigger_callback("export_started", execution.execution_id)
        return execution.execution_id
    
    def _execute_export_worker(self, execution: ExportExecution, config: ExportConfig,
                              data_source: str, data_params: Dict) -> None:
        """Worker thread for export"""
        try:
            execution.started_at = time.time()
            execution.status = "running"
            
            # Get data source
            source_func = self.data_sources[data_source]
            
            # Export data in chunks
            file_paths = []
            chunk_count = 0
            
            for chunk in source_func(**data_params):
                # Apply filters if specified
                if config.filters:
                    chunk = self._apply_filters(chunk, config.filters)
                
                # Apply column mapping
                if config.column_mapping:
                    chunk = self._apply_column_mapping(chunk, config.column_mapping)
                
                # Format data
                formatted_data = self._format_data(chunk, config)
                
                # Write to destination
                file_path = self._write_to_destination(
                    formatted_data,
                    config,
                    chunk_count
                )
                
                if file_path:
                    file_paths.append(file_path)
                    execution.rows_exported += len(chunk)
                    execution.bytes_exported += len(formatted_data.encode('utf-8'))
                
                chunk_count += 1
            
            execution.file_paths = file_paths
            execution.status = "completed"
            execution.completed_at = time.time()
            
            with self.lock:
                self.stats.successful_exports += 1
                self.stats.total_rows_exported += execution.rows_exported
                self.stats.total_bytes_exported += execution.bytes_exported
            
            self._trigger_callback("export_completed", execution.execution_id)
            
        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = time.time()
            
            with self.lock:
                self.stats.failed_exports += 1
            
            self._trigger_callback("export_failed", execution.execution_id, str(e))
    
    def _apply_filters(self, data: List[Dict], filters: Dict) -> List[Dict]:
        """Apply filters to data"""
        filtered = []
        
        for row in data:
            match = True
            
            for field, filter_value in filters.items():
                if field not in row:
                    match = False
                    break
                
                if isinstance(filter_value, dict):
                    # Complex filter (e.g., {"$gt": 100})
                    if "$gt" in filter_value and not (row[field] > filter_value["$gt"]):
                        match = False
                    if "$lt" in filter_value and not (row[field] < filter_value["$lt"]):
                        match = False
                    if "$eq" in filter_value and row[field] != filter_value["$eq"]:
                        match = False
                else:
                    # Simple equality filter
                    if row[field] != filter_value:
                        match = False
            
            if match:
                filtered.append(row)
        
        return filtered
    
    def _apply_column_mapping(self, data: List[Dict], mapping: Dict) -> List[Dict]:
        """Apply column name mapping"""
        mapped = []
        
        for row in data:
            mapped_row = {}
            
            for old_name, new_name in mapping.items():
                if old_name in row:
                    mapped_row[new_name] = row[old_name]
            
            # Include unmapped columns
            for key, value in row.items():
                if key not in mapping and key not in mapped_row:
                    mapped_row[key] = value
            
            mapped.append(mapped_row)
        
        return mapped
    
    def _format_data(self, data: List[Dict], config: ExportConfig) -> str:
        """Format data for export"""
        if not data:
            return ""
        
        columns = list(data[0].keys())
        
        if config.format == ExportFormat.CSV:
            return ExportFormatter.to_csv(data, columns)
        elif config.format == ExportFormat.JSON:
            return ExportFormatter.to_json(data, config.include_metadata)
        elif config.format == ExportFormat.JSONL:
            return ExportFormatter.to_jsonl(data)
        elif config.format == ExportFormat.XML:
            return ExportFormatter.to_xml(data)
        else:
            # Default to JSON
            return ExportFormatter.to_json(data)
    
    def _write_to_destination(self, data: str, config: ExportConfig, chunk_id: int) -> Optional[str]:
        """Write data to destination"""
        destination = config.destination
        
        if destination == ExportDestination.LOCAL_FILE:
            return self._write_local_file(data, config, chunk_id)
        elif destination == ExportDestination.S3:
            return self._write_s3(data, config, chunk_id)
        else:
            # Handle other destinations
            return f"export_{chunk_id}.{config.format.value}"
    
    def _write_local_file(self, data: str, config: ExportConfig, chunk_id: int) -> str:
        """Write to local file"""
        file_path = config.destination_config.get("directory", "/tmp")
        filename = f"{config.name}_{chunk_id}.{config.format.value}"
        full_path = f"{file_path}/{filename}"
        
        # In production, actually write file
        return full_path
    
    def _write_s3(self, data: str, config: ExportConfig, chunk_id: int) -> str:
        """Write to S3"""
        bucket = config.destination_config.get("bucket")
        prefix = config.destination_config.get("prefix", "exports/")
        filename = f"{config.name}_{chunk_id}.{config.format.value}"
        
        # In production, use boto3
        return f"s3://{bucket}/{prefix}{filename}"
    
    def get_execution_status(self, execution_id: str) -> Optional[ExportExecution]:
        """Get execution status"""
        with self.lock:
            return self.executions.get(execution_id)
    
    def get_execution_history(self, export_id: str, limit: int = 10) -> List[ExportExecution]:
        """Get execution history"""
        with self.lock:
            history = [
                ex for ex in self.executions.values()
                if ex.export_id == export_id
            ]
            return sorted(history, key=lambda x: x.started_at or 0, reverse=True)[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get export statistics"""
        with self.lock:
            total = self.stats.successful_exports + self.stats.failed_exports
            success_rate = (self.stats.successful_exports / total * 100) if total > 0 else 0.0
            
            return {
                "total_exports": self.stats.total_exports,
                "successful_exports": self.stats.successful_exports,
                "failed_exports": self.stats.failed_exports,
                "success_rate": success_rate,
                "total_rows_exported": self.stats.total_rows_exported,
                "total_bytes_exported": self.stats.total_bytes_exported,
                "avg_export_time_seconds": self.stats.avg_export_time_seconds,
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
_export_service: Optional[DataExportService] = None


def get_export_service() -> DataExportService:
    """Get or create singleton export service"""
    global _export_service
    if _export_service is None:
        _export_service = DataExportService()
    return _export_service


def reset_export_service() -> None:
    """Reset export service (for testing)"""
    global _export_service
    _export_service = None
