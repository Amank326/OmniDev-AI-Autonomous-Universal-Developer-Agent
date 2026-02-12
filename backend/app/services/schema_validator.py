"""
Phase 52: Schema Validation Service
Validate API requests against schemas
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class ValidationType(Enum):
    """Types of validation"""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    ENUM = "enum"
    EMAIL = "email"
    URL = "url"


@dataclass
class ValidationRule:
    """Validation rule for a field"""
    field_name: str
    field_type: ValidationType
    required: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None
    enum_values: Optional[List[Any]] = None
    items_type: Optional[ValidationType] = None
    
    def validate(self, value: Any) -> Tuple[bool, str]:
        """
        Validate value against rule
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required
        if value is None:
            if self.required:
                return False, f"{self.field_name} is required"
            return True, ""
        
        # Type validation
        if self.field_type == ValidationType.STRING:
            if not isinstance(value, str):
                return False, f"{self.field_name} must be string"
            
            if self.min_length and len(value) < self.min_length:
                return False, f"{self.field_name} must be >= {self.min_length} chars"
            
            if self.max_length and len(value) > self.max_length:
                return False, f"{self.field_name} must be <= {self.max_length} chars"
        
        elif self.field_type == ValidationType.INTEGER:
            if not isinstance(value, int) or isinstance(value, bool):
                return False, f"{self.field_name} must be integer"
            
            if self.min_value is not None and value < self.min_value:
                return False, f"{self.field_name} must be >= {self.min_value}"
            
            if self.max_value is not None and value > self.max_value:
                return False, f"{self.field_name} must be <= {self.max_value}"
        
        elif self.field_type == ValidationType.NUMBER:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return False, f"{self.field_name} must be number"
            
            if self.min_value is not None and value < self.min_value:
                return False, f"{self.field_name} must be >= {self.min_value}"
            
            if self.max_value is not None and value > self.max_value:
                return False, f"{self.field_name} must be <= {self.max_value}"
        
        elif self.field_type == ValidationType.BOOLEAN:
            if not isinstance(value, bool):
                return False, f"{self.field_name} must be boolean"
        
        elif self.field_type == ValidationType.ARRAY:
            if not isinstance(value, list):
                return False, f"{self.field_name} must be array"
            
            if self.min_length and len(value) < self.min_length:
                return False, f"{self.field_name} must have >= {self.min_length} items"
            
            if self.max_length and len(value) > self.max_length:
                return False, f"{self.field_name} must have <= {self.max_length} items"
        
        elif self.field_type == ValidationType.ENUM:
            if self.enum_values and value not in self.enum_values:
                return False, f"{self.field_name} must be one of {self.enum_values}"
        
        elif self.field_type == ValidationType.EMAIL:
            if not isinstance(value, str):
                return False, f"{self.field_name} must be string"
            if '@' not in value or '.' not in value:
                return False, f"{self.field_name} must be valid email"
        
        elif self.field_type == ValidationType.URL:
            if not isinstance(value, str):
                return False, f"{self.field_name} must be string"
            if not (value.startswith('http://') or value.startswith('https://')):
                return False, f"{self.field_name} must be valid URL"
        
        return True, ""


@dataclass
class ValidationError:
    """Validation error information"""
    field: str
    message: str
    value: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "field": self.field,
            "message": self.message,
            "value": self.value
        }


class SchemaValidator:
    """Validate data against schemas"""
    
    def __init__(self):
        self.schemas: Dict[str, List[ValidationRule]] = {}
    
    def register_schema(self, name: str, rules: List[ValidationRule]) -> None:
        """Register a validation schema"""
        self.schemas[name] = rules
        logger.debug(f"Registered schema: {name} with {len(rules)} rules")
    
    def validate(self, data: Dict[str, Any], 
                schema_name: str) -> Tuple[bool, List[ValidationError]]:
        """
        Validate data against schema
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if schema_name not in self.schemas:
            return False, [ValidationError(schema_name, "Schema not found")]
        
        rules = self.schemas[schema_name]
        errors: List[ValidationError] = []
        
        for rule in rules:
            value = data.get(rule.field_name)
            is_valid, error_msg = rule.validate(value)
            
            if not is_valid:
                errors.append(ValidationError(
                    field=rule.field_name,
                    message=error_msg,
                    value=value
                ))
        
        return len(errors) == 0, errors
    
    def validate_dict(self, data: Dict[str, Any],
                     schema: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
        """
        Validate data against inline schema
        
        Schema format:
            {'field': {'type': 'string', 'required': True, ...}}
        """
        errors: List[ValidationError] = []
        
        for field_name, field_schema in schema.items():
            value = data.get(field_name)
            
            # Check required
            if field_schema.get('required', False) and value is None:
                errors.append(ValidationError(
                    field=field_name,
                    message=f"{field_name} is required"
                ))
                continue
            
            if value is None:
                continue
            
            # Check type
            field_type = field_schema.get('type', 'string')
            
            type_valid = False
            if field_type == 'string' and isinstance(value, str):
                type_valid = True
            elif field_type == 'integer' and isinstance(value, int) and not isinstance(value, bool):
                type_valid = True
            elif field_type == 'number' and isinstance(value, (int, float)) and not isinstance(value, bool):
                type_valid = True
            elif field_type == 'boolean' and isinstance(value, bool):
                type_valid = True
            elif field_type == 'array' and isinstance(value, list):
                type_valid = True
            elif field_type == 'object' and isinstance(value, dict):
                type_valid = True
            
            if not type_valid:
                errors.append(ValidationError(
                    field=field_name,
                    message=f"{field_name} must be {field_type}",
                    value=value
                ))
        
        return len(errors) == 0, errors


class RequestValidator:
    """Validate API requests"""
    
    def __init__(self):
        self.validator = SchemaValidator()
        self.request_schemas: Dict[str, Dict[str, Any]] = {}
    
    def register_request_schema(self, endpoint: str, method: str,
                               schema: Dict[str, Any]) -> None:
        """Register request schema for endpoint"""
        key = f"{method} {endpoint}"
        self.request_schemas[key] = schema
        logger.debug(f"Registered request schema: {key}")
    
    def validate_request(self, endpoint: str, method: str,
                        body: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
        """
        Validate request against endpoint schema
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        key = f"{method} {endpoint}"
        
        if key not in self.request_schemas:
            # No schema registered
            return True, []
        
        schema = self.request_schemas[key]
        return self.validator.validate_dict(body, schema)
    
    def validate_query_params(self, params: Dict[str, Any],
                             schema: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
        """Validate query parameters"""
        return self.validator.validate_dict(params, schema)
    
    def get_validation_errors_summary(self, errors: List[ValidationError]) -> str:
        """Get human-readable summary of errors"""
        if not errors:
            return "No validation errors"
        
        error_lines = ["Validation errors:"]
        for error in errors:
            error_lines.append(f"  - {error.field}: {error.message}")
        
        return "\n".join(error_lines)


class ResponseValidator:
    """Validate API responses"""
    
    def __init__(self):
        self.response_schemas: Dict[str, Dict[str, Any]] = {}
    
    def register_response_schema(self, endpoint: str, status_code: int,
                                schema: Dict[str, Any]) -> None:
        """Register response schema for endpoint/status"""
        key = f"{endpoint}:{status_code}"
        self.response_schemas[key] = schema
    
    def validate_response(self, endpoint: str, status_code: int,
                         body: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
        """Validate response against schema"""
        key = f"{endpoint}:{status_code}"
        
        if key not in self.response_schemas:
            return True, []
        
        validator = SchemaValidator()
        schema = self.response_schemas[key]
        
        errors: List[ValidationError] = []
        
        for field_name, field_schema in schema.items():
            value = body.get(field_name)
            
            if field_schema.get('required', False) and value is None:
                errors.append(ValidationError(
                    field=field_name,
                    message=f"{field_name} is required in response"
                ))
        
        return len(errors) == 0, errors


# Global instances
_request_validator: Optional[RequestValidator] = None
_response_validator: Optional[ResponseValidator] = None


def get_request_validator() -> RequestValidator:
    """Get or create request validator"""
    global _request_validator
    if _request_validator is None:
        _request_validator = RequestValidator()
    return _request_validator


def get_response_validator() -> ResponseValidator:
    """Get or create response validator"""
    global _response_validator
    if _response_validator is None:
        _response_validator = ResponseValidator()
    return _response_validator


def reset_validators() -> None:
    """Reset validators (for testing)"""
    global _request_validator, _response_validator
    _request_validator = None
    _response_validator = None
