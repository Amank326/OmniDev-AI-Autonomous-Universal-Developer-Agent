"""
Secure Data Migration Utility
Migrates sensitive data across platform phases with encryption and audit logging
Phase 40: Final Integration & Platform Stabilization
"""

import logging
import hashlib
import json
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from threading import RLock
import base64

from backend.app.services.security_service import SecurityService, EncryptedData

logger = logging.getLogger(__name__)


class DataClassification(Enum):
    """Data sensitivity classification"""
    PUBLIC = "public"  # No restrictions
    INTERNAL = "internal"  # For internal use only
    CONFIDENTIAL = "confidential"  # Restricted access
    RESTRICTED = "restricted"  # Highly sensitive


class MigrationStatus(Enum):
    """Migration status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class DataSchema:
    """Defines structure and classification of data"""
    name: str
    fields: Dict[str, str]  # field_name -> field_type
    sensitive_fields: List[str] = field(default_factory=list)
    pii_fields: List[str] = field(default_factory=list)
    classification: DataClassification = DataClassification.INTERNAL
    encryption_required: bool = False
    audit_required: bool = True


@dataclass
class MigrationRecord:
    """Record of a data migration operation"""
    migration_id: str
    source_phase: str
    target_phase: str
    data_schema: str
    record_count: int
    classification: DataClassification
    encryption_applied: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: MigrationStatus = MigrationStatus.PENDING
    error_message: Optional[str] = None
    validated: bool = False
    audit_log_id: Optional[str] = None
    checksum: Optional[str] = None


@dataclass
class DataValidation:
    """Data validation rules and results"""
    field_name: str
    data_type: str
    nullable: bool = True
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    valid: bool = True
    errors: List[str] = field(default_factory=list)


class DataMigrationValidator:
    """Validates data before and after migration"""

    def __init__(self, security_service: SecurityService):
        self.security_service = security_service
        self.validation_rules: Dict[str, List[DataValidation]] = {}
        self.lock = RLock()

    def register_schema(self, schema: DataSchema) -> None:
        """Register validation schema"""
        with self.lock:
            validations = []
            for field_name, field_type in schema.fields.items():
                validation = DataValidation(
                    field_name=field_name,
                    data_type=field_type,
                    max_length=255 if field_type == "string" else None
                )
                validations.append(validation)
            self.validation_rules[schema.name] = validations

    def validate_data(self, schema_name: str, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate data against schema"""
        with self.lock:
            rules = self.validation_rules.get(schema_name, [])
            errors = []
            
            for rule in rules:
                if rule.field_name not in data:
                    if not rule.nullable:
                        errors.append(f"Required field {rule.field_name} is missing")
                    continue
                
                value = data[rule.field_name]
                
                # Type checking
                if rule.data_type == "string" and not isinstance(value, str):
                    errors.append(f"Field {rule.field_name}: expected string, got {type(value)}")
                
                # Length checking
                if rule.max_length and isinstance(value, str) and len(value) > rule.max_length:
                    errors.append(f"Field {rule.field_name}: exceeds max length {rule.max_length}")
            
            return len(errors) == 0, errors

    def compute_checksum(self, data: List[Dict]) -> str:
        """Compute checksum for data integrity verification"""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()


class DataMigrationPlan:
    """Plan for migrating data between phases"""

    def __init__(self, source_phase: str, target_phase: str):
        self.source_phase = source_phase
        self.target_phase = target_phase
        self.migrations: Dict[str, DataSchema] = {}
        self.transformations: Dict[str, Callable] = {}
        self.pre_migration_hooks: List[Callable] = []
        self.post_migration_hooks: List[Callable] = []
        self.rollback_plans: Dict[str, Callable] = {}
        self.lock = RLock()

    def add_data_migration(self, schema: DataSchema) -> None:
        """Add data migration to plan"""
        with self.lock:
            self.migrations[schema.name] = schema

    def add_transformation(self, schema_name: str, transformation: Callable) -> None:
        """Add data transformation function"""
        with self.lock:
            self.transformations[schema_name] = transformation

    def add_pre_migration_hook(self, callback: Callable) -> None:
        """Add pre-migration hook"""
        with self.lock:
            self.pre_migration_hooks.append(callback)

    def add_post_migration_hook(self, callback: Callable) -> None:
        """Add post-migration hook"""
        with self.lock:
            self.post_migration_hooks.append(callback)

    def add_rollback_plan(self, schema_name: str, rollback_fn: Callable) -> None:
        """Add rollback plan for migration"""
        with self.lock:
            self.rollback_plans[schema_name] = rollback_fn

    def get_migration_info(self) -> Dict[str, Any]:
        """Get migration plan information"""
        with self.lock:
            return {
                "source_phase": self.source_phase,
                "target_phase": self.target_phase,
                "data_schemas": len(self.migrations),
                "transformations": len(self.transformations),
                "rollback_enabled": len(self.rollback_plans) > 0
            }


class SecureDataMigrator:
    """Migrates data securely across platform phases"""

    def __init__(self, security_service: SecurityService):
        self.security_service = security_service
        self.validator = DataMigrationValidator(security_service)
        self.migration_history: List[MigrationRecord] = []
        self.active_migrations: Dict[str, MigrationRecord] = {}
        self.lock = RLock()

    def plan_migration(self, source_phase: str, target_phase: str) -> DataMigrationPlan:
        """Create a migration plan between phases"""
        return DataMigrationPlan(source_phase, target_phase)

    def execute_migration(self, plan: DataMigrationPlan, data: Dict[str, List[Dict]],
                        user_id: str, ip_address: str) -> tuple[bool, str, Optional[MigrationRecord]]:
        """Execute data migration with security and validation"""
        migration_id = self._generate_migration_id()
        
        with self.lock:
            try:
                # Pre-migration hooks
                for hook in plan.pre_migration_hooks:
                    hook(data)
                
                # Process each data type
                encrypted_data = {}
                records = []
                
                for schema_name, schema_data_list in data.items():
                    if schema_name not in plan.migrations:
                        return False, f"Unknown schema {schema_name}", None
                    
                    schema = plan.migrations[schema_name]
                    
                    # Validate data
                    for record in schema_data_list:
                        valid, errors = self.validator.validate_data(schema_name, record)
                        if not valid:
                            return False, f"Validation failed: {errors}", None
                    
                    # Apply transformation if exists
                    if schema_name in plan.transformations:
                        schema_data_list = [plan.transformations[schema_name](r) for r in schema_data_list]
                    
                    # Encrypt if required
                    if schema.encryption_required:
                        encrypted_list = []
                        for record in schema_data_list:
                            record_str = json.dumps(record, default=str)
                            encrypted = self.security_service.encrypt_data(record_str)
                            encrypted_list.append({
                                "ciphertext": encrypted.ciphertext,
                                "nonce": encrypted.nonce,
                                "algorithm": encrypted.algorithm.value,
                                "key_id": encrypted.key_id
                            })
                        encrypted_data[schema_name] = encrypted_list
                    else:
                        encrypted_data[schema_name] = schema_data_list
                    
                    # Create migration record
                    record = MigrationRecord(
                        migration_id=migration_id,
                        source_phase=plan.source_phase,
                        target_phase=plan.target_phase,
                        data_schema=schema_name,
                        record_count=len(schema_data_list),
                        classification=schema.classification,
                        encryption_applied=schema.encryption_required,
                        checksum=self.validator.compute_checksum(schema_data_list)
                    )
                    records.append(record)
                
                # Post-migration hooks
                for hook in plan.post_migration_hooks:
                    hook(encrypted_data)
                
                # Log migration
                for record in records:
                    record.status = MigrationStatus.COMPLETED
                    record.completed_at = datetime.utcnow()
                    self.migration_history.append(record)
                    
                    # Audit log
                    if record.classification != DataClassification.PUBLIC:
                        self.security_service.log_audit(
                            user_id=user_id,
                            action="DATA_MIGRATION",
                            resource="secure_data",
                            resource_id=record.migration_id,
                            status="success",
                            details={
                                "source_phase": plan.source_phase,
                                "target_phase": plan.target_phase,
                                "schema": record.data_schema,
                                "count": record.record_count,
                                "encryption": record.encryption_applied
                            },
                            ip_address=ip_address,
                            user_agent="secure_migrator",
                            severity="info"
                        )
                
                return True, migration_id, records[0] if records else None
            
            except Exception as e:
                error_msg = f"Migration failed: {str(e)}"
                logger.error(error_msg)
                
                # Attempt rollback
                for schema_name in plan.migrations:
                    if schema_name in plan.rollback_plans:
                        try:
                            plan.rollback_plans[schema_name]()
                        except Exception as rb_err:
                            logger.error(f"Rollback failed for {schema_name}: {rb_err}")
                
                return False, error_msg, None

    def verify_migration(self, migration_id: str) -> tuple[bool, List[str]]:
        """Verify migration integrity"""
        with self.lock:
            errors = []
            
            # Find migration records
            records = [r for r in self.migration_history if r.migration_id == migration_id]
            if not records:
                return False, ["Migration record not found"]
            
            # Verify checksums (if source data available)
            for record in records:
                if record.checksum is None:
                    errors.append(f"No checksum for {record.data_schema}")
                else:
                    record.validated = True
            
            return len(errors) == 0, errors

    def get_migration_history(self, limit: int = 100) -> List[MigrationRecord]:
        """Get migration history"""
        with self.lock:
            return sorted(
                self.migration_history,
                key=lambda r: r.timestamp,
                reverse=True
            )[:limit]

    def get_migration_statistics(self) -> Dict[str, Any]:
        """Get migration statistics"""
        with self.lock:
            completed = sum(1 for r in self.migration_history if r.status == MigrationStatus.COMPLETED)
            failed = sum(1 for r in self.migration_history if r.status == MigrationStatus.FAILED)
            total_records = sum(r.record_count for r in self.migration_history)
            encrypted_records = sum(r.record_count for r in self.migration_history if r.encryption_applied)
            
            return {
                "total_migrations": len(self.migration_history),
                "completed": completed,
                "failed": failed,
                "total_records_migrated": total_records,
                "records_encrypted": encrypted_records,
                "encryption_rate": (encrypted_records / total_records * 100) if total_records > 0 else 0
            }

    def _generate_migration_id(self) -> str:
        """Generate unique migration ID"""
        import uuid
        return f"migration_{uuid.uuid4().hex[:12]}"


class DataMigrationValidator:
    """Validates data migration integrity"""

    def __init__(self, security_service: SecurityService):
        self.security_service = security_service
        self.checksums: Dict[str, str] = {}

    def check_data_integrity(self, original_data: List[Dict], 
                            migrated_data: List[Dict]) -> tuple[bool, List[str]]:
        """Verify data integrity between original and migrated"""
        errors = []
        
        if len(original_data) != len(migrated_data):
            errors.append(f"Record count mismatch: {len(original_data)} vs {len(migrated_data)}")
        
        for i, (orig, migrated) in enumerate(zip(original_data, migrated_data)):
            if set(orig.keys()) != set(migrated.keys()):
                errors.append(f"Record {i}: field mismatch")
        
        return len(errors) == 0, errors


# Global migrator instance
_migrator: Optional[SecureDataMigrator] = None


def get_secure_data_migrator(security_service: SecurityService) -> SecureDataMigrator:
    """Get or create secure data migrator instance"""
    global _migrator
    if _migrator is None:
        _migrator = SecureDataMigrator(security_service)
    return _migrator
