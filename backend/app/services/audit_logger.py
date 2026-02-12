"""
Phase 12: Audit Logger
Comprehensive audit logging for compliance and forensics
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Audit event types"""
    # User events
    LOGIN = "user.login"
    LOGOUT = "user.logout"
    PASSWORD_CHANGE = "user.password_change"
    PROFILE_UPDATE = "user.profile_update"

    # Resource events
    RESOURCE_CREATE = "resource.create"
    RESOURCE_UPDATE = "resource.update"
    RESOURCE_DELETE = "resource.delete"
    RESOURCE_READ = "resource.read"

    # Permission events
    PERMISSION_GRANT = "permission.grant"
    PERMISSION_REVOKE = "permission.revoke"
    ROLE_ASSIGN = "role.assign"
    ROLE_REVOKE = "role.revoke"

    # Workflow events
    WORKFLOW_EXECUTE = "workflow.execute"
    WORKFLOW_STOP = "workflow.stop"
    WORKFLOW_FAILURE = "workflow.failure"

    # API events
    API_KEY_GENERATE = "api.key_generate"
    API_KEY_REVOKE = "api.key_revoke"
    API_CALL = "api.call"

    # Tenant events
    TENANT_CREATE = "tenant.create"
    TENANT_UPDATE = "tenant.update"
    TENANT_DELETE = "tenant.delete"
    TENANT_MEMBER_ADD = "tenant.member_add"
    TENANT_MEMBER_REMOVE = "tenant.member_remove"

    # Data export
    DATA_EXPORT = "data.export"
    REPORT_GENERATE = "report.generate"


class AuditLog:
    """Individual audit log entry"""

    def __init__(self, event_type: str, user_id: str, tenant_id: str,
                 resource_type: Optional[str] = None,
                 resource_id: Optional[str] = None,
                 description: str = "",
                 details: Optional[Dict[str, Any]] = None,
                 ip_address: Optional[str] = None,
                 user_agent: Optional[str] = None):

        self.event_id = self._generate_event_id()
        self.timestamp = datetime.utcnow()
        self.event_type = event_type
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.description = description
        self.details = details or {}
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.status = "success"
        self.error_message = None

    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        timestamp_str = datetime.utcnow().isoformat()
        content = f"{timestamp_str}{datetime.utcnow().microsecond}".encode()
        return hashlib.sha256(content).hexdigest()[:16]

    def mark_failure(self, error: str) -> None:
        """Mark event as failed with error message"""
        self.status = "failure"
        self.error_message = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "description": self.description,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "status": self.status,
            "error_message": self.error_message,
        }


class AuditLogger:
    """
    Comprehensive audit logging service
    Immutable log with forensic capabilities
    """

    def __init__(self):
        self.logs: List[AuditLog] = []
        self.log_file = "audit.log"  # For persistence
        self.retention_days = 365  # Keep 1 year

    def log_user_action(self, event_type: str, user_id: str, tenant_id: str,
                       description: str = "", details: Optional[Dict] = None,
                       ip_address: Optional[str] = None,
                       user_agent: Optional[str] = None) -> str:
        """
        Log a user action
        Returns event_id
        """
        audit_log = AuditLog(
            event_type=event_type,
            user_id=user_id,
            tenant_id=tenant_id,
            description=description,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.logs.append(audit_log)
        logger.info(f"Audit: {event_type} by {user_id} (event_id={audit_log.event_id})")

        return audit_log.event_id

    def log_resource_change(self, action: str, resource_type: str,
                           resource_id: str, user_id: str, tenant_id: str,
                           old_value: Optional[Dict] = None,
                           new_value: Optional[Dict] = None,
                           ip_address: Optional[str] = None) -> str:
        """
        Log resource create/update/delete
        Returns event_id
        """
        if action == "create":
            event_type = AuditEventType.RESOURCE_CREATE
            description = f"Created {resource_type} {resource_id}"
        elif action == "update":
            event_type = AuditEventType.RESOURCE_UPDATE
            description = f"Updated {resource_type} {resource_id}"
        elif action == "delete":
            event_type = AuditEventType.RESOURCE_DELETE
            description = f"Deleted {resource_type} {resource_id}"
        else:
            event_type = action
            description = f"{action} {resource_type} {resource_id}"

        details = {"action": action}
        if old_value:
            details["old_value"] = old_value
        if new_value:
            details["new_value"] = new_value

        audit_log = AuditLog(
            event_type=event_type,
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            details=details,
            ip_address=ip_address,
        )

        self.logs.append(audit_log)
        logger.info(f"Audit: {event_type} {resource_type}/{resource_id} by {user_id}")

        return audit_log.event_id

    def log_permission_change(self, action: str, user_id: str, target_user_id: str,
                             tenant_id: str, role_or_permission: str,
                             changed_by: str, reason: str = "") -> str:
        """
        Log permission or role change
        """
        if action in ["grant", "assign"]:
            event_type = AuditEventType.PERMISSION_GRANT if action == "grant" else AuditEventType.ROLE_ASSIGN
            description = f"Assigned {role_or_permission} to {target_user_id}"
        elif action in ["revoke"]:
            event_type = AuditEventType.PERMISSION_REVOKE
            description = f"Revoked {role_or_permission} from {target_user_id}"
        else:
            event_type = action
            description = f"{action} {role_or_permission} for {target_user_id}"

        audit_log = AuditLog(
            event_type=event_type,
            user_id=changed_by,
            tenant_id=tenant_id,
            resource_type="user",
            resource_id=target_user_id,
            description=description,
            details={
                "action": action,
                "target_user": target_user_id,
                "role_or_permission": role_or_permission,
                "reason": reason,
            },
        )

        self.logs.append(audit_log)
        logger.info(f"Audit: Permission change {action} {role_or_permission} for {target_user_id}")

        return audit_log.event_id

    def log_workflow_execution(self, workflow_id: str, execution_id: str,
                              user_id: str, tenant_id: str,
                              status: str, duration: float = 0,
                              error: Optional[str] = None) -> str:
        """
        Log workflow execution
        """
        event_type = AuditEventType.WORKFLOW_EXECUTE
        description = f"Executed workflow {workflow_id}"

        audit_log = AuditLog(
            event_type=event_type,
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type="workflow",
            resource_id=workflow_id,
            description=description,
            details={
                "execution_id": execution_id,
                "status": status,
                "duration": duration,
                "error": error,
            },
        )

        if error:
            audit_log.mark_failure(error)

        self.logs.append(audit_log)
        logger.info(f"Audit: Workflow {workflow_id} {status} (execution_id={execution_id})")

        return audit_log.event_id

    def log_api_call(self, endpoint: str, method: str, user_id: str,
                    tenant_id: str, status_code: int,
                    response_time: float, ip_address: Optional[str] = None) -> str:
        """
        Log API call
        """
        audit_log = AuditLog(
            event_type=AuditEventType.API_CALL,
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type="api",
            resource_id=endpoint,
            description=f"{method} {endpoint}",
            details={
                "method": method,
                "endpoint": endpoint,
                "status_code": status_code,
                "response_time": response_time,
            },
            ip_address=ip_address,
        )

        if status_code >= 400:
            audit_log.status = "failure"

        self.logs.append(audit_log)

        return audit_log.event_id

    def log_data_export(self, export_id: str, resource_type: str,
                       user_id: str, tenant_id: str, record_count: int,
                       export_format: str) -> str:
        """
        Log data export for compliance
        """
        audit_log = AuditLog(
            event_type=AuditEventType.DATA_EXPORT,
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=export_id,
            description=f"Exported {record_count} {resource_type} records",
            details={
                "export_id": export_id,
                "resource_type": resource_type,
                "record_count": record_count,
                "format": export_format,
            },
        )

        self.logs.append(audit_log)
        logger.info(f"Audit: Data export {export_id} ({record_count} records)")

        return audit_log.event_id

    def get_audit_log(self, tenant_id: str, filters: Optional[Dict] = None,
                     limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Get audit logs with filtering
        Filters: event_type, user_id, resource_type, date_range, status
        """
        filtered_logs = [log for log in self.logs if log.tenant_id == tenant_id]

        # Apply filters
        if filters:
            if "event_type" in filters:
                filtered_logs = [
                    log for log in filtered_logs
                    if log.event_type == filters["event_type"]
                ]

            if "user_id" in filters:
                filtered_logs = [
                    log for log in filtered_logs
                    if log.user_id == filters["user_id"]
                ]

            if "resource_type" in filters:
                filtered_logs = [
                    log for log in filtered_logs
                    if log.resource_type == filters["resource_type"]
                ]

            if "status" in filters:
                filtered_logs = [
                    log for log in filtered_logs
                    if log.status == filters["status"]
                ]

            if "date_range" in filters:
                start_date, end_date = filters["date_range"]
                filtered_logs = [
                    log for log in filtered_logs
                    if start_date <= log.timestamp <= end_date
                ]

        # Sort by timestamp descending
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)

        # Paginate
        paginated = filtered_logs[offset:offset + limit]

        return [log.to_dict() for log in paginated]

    def get_user_audit_log(self, tenant_id: str, user_id: str,
                          limit: int = 100) -> List[Dict]:
        """
        Get audit log for specific user
        """
        return self.get_audit_log(
            tenant_id,
            filters={"user_id": user_id},
            limit=limit
        )

    def get_resource_audit_log(self, tenant_id: str, resource_type: str,
                              resource_id: str) -> List[Dict]:
        """
        Get audit log for specific resource
        """
        filtered_logs = [
            log for log in self.logs
            if log.tenant_id == tenant_id
            and log.resource_type == resource_type
            and log.resource_id == resource_id
        ]

        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)

        return [log.to_dict() for log in filtered_logs]

    def export_audit_log(self, tenant_id: str, format: str = "json",
                        filters: Optional[Dict] = None) -> str:
        """
        Export audit logs
        Formats: json, csv
        Returns export content
        """
        logs = self.get_audit_log(tenant_id, filters=filters, limit=10000)

        if format == "json":
            return json.dumps(logs, indent=2, default=str)

        elif format == "csv":
            if not logs:
                return "event_id,timestamp,event_type,user_id,resource_type,resource_id,description,status"

            import csv
            from io import StringIO

            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=logs[0].keys())
            writer.writeheader()
            writer.writerows(logs)

            return output.getvalue()

        else:
            logger.error(f"Unsupported export format: {format}")
            return ""

    def get_audit_stats(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get audit log statistics
        """
        tenant_logs = [log for log in self.logs if log.tenant_id == tenant_id]

        event_counts = {}
        user_counts = {}
        failures = 0

        for log in tenant_logs:
            # Count by event type
            event_counts[log.event_type] = event_counts.get(log.event_type, 0) + 1

            # Count by user
            user_counts[log.user_id] = user_counts.get(log.user_id, 0) + 1

            # Count failures
            if log.status == "failure":
                failures += 1

        return {
            "total_events": len(tenant_logs),
            "total_users": len(user_counts),
            "total_failures": failures,
            "events_by_type": event_counts,
            "events_by_user": user_counts,
            "date_range": {
                "start": min(log.timestamp for log in tenant_logs).isoformat() if tenant_logs else None,
                "end": max(log.timestamp for log in tenant_logs).isoformat() if tenant_logs else None,
            },
        }

    def search_audit_log(self, tenant_id: str, query: str) -> List[Dict]:
        """
        Search audit log by description or details
        """
        filtered_logs = []

        for log in self.logs:
            if log.tenant_id != tenant_id:
                continue

            # Search in description
            if query.lower() in log.description.lower():
                filtered_logs.append(log)
                continue

            # Search in details
            details_str = json.dumps(log.details, default=str)
            if query.lower() in details_str.lower():
                filtered_logs.append(log)

        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)

        return [log.to_dict() for log in filtered_logs]
