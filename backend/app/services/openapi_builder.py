"""
Phase 52: OpenAPI Schema Builder
Auto-generate OpenAPI/Swagger specifications from FastAPI routes
"""

from typing import Dict, Any, List, Optional, Type
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HTTPMethod(Enum):
    """HTTP methods"""
    GET = "get"
    POST = "post"
    PUT = "put"
    DELETE = "delete"
    PATCH = "patch"
    HEAD = "head"
    OPTIONS = "options"


class DataType(Enum):
    """OpenAPI data types"""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class Parameter:
    """API parameter definition"""
    name: str
    param_type: str = "query"  # query, path, header, cookie
    data_type: DataType = DataType.STRING
    required: bool = False
    description: str = ""
    default: Optional[Any] = None
    example: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to OpenAPI parameter"""
        param = {
            "name": self.name,
            "in": self.param_type,
            "required": self.required,
            "schema": {
                "type": self.data_type.value
            }
        }
        
        if self.description:
            param["description"] = self.description
        if self.default is not None:
            param["schema"]["default"] = self.default
        if self.example is not None:
            param["example"] = self.example
        
        return param


@dataclass
class RequestBody:
    """Request body definition"""
    content_type: str = "application/json"
    schema: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    required: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to OpenAPI request body"""
        return {
            "required": self.required,
            "content": {
                self.content_type: {
                    "schema": self.schema
                }
            },
            "description": self.description
        }


@dataclass
class Response:
    """Response definition"""
    status_code: int = 200
    description: str = ""
    schema: Dict[str, Any] = field(default_factory=dict)
    content_type: str = "application/json"
    headers: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to OpenAPI response"""
        response = {
            "description": self.description
        }
        
        if self.schema:
            response["content"] = {
                self.content_type: {
                    "schema": self.schema
                }
            }
        
        if self.headers:
            response["headers"] = self.headers
        
        return response


@dataclass
class Endpoint:
    """API endpoint definition"""
    path: str
    method: HTTPMethod
    summary: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    parameters: List[Parameter] = field(default_factory=list)
    request_body: Optional[RequestBody] = None
    responses: List[Response] = field(default_factory=list)
    deprecated: bool = False
    operation_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to OpenAPI operation"""
        operation = {
            "summary": self.summary,
            "description": self.description
        }
        
        if self.tags:
            operation["tags"] = self.tags
        
        if self.parameters:
            operation["parameters"] = [p.to_dict() for p in self.parameters]
        
        if self.request_body:
            operation["requestBody"] = self.request_body.to_dict()
        
        # Add responses
        responses = {}
        if self.responses:
            for resp in self.responses:
                responses[str(resp.status_code)] = resp.to_dict()
        else:
            # Default responses
            responses["200"] = Response(200, "Successful response").to_dict()
            responses["400"] = Response(400, "Bad request").to_dict()
            responses["500"] = Response(500, "Server error").to_dict()
        
        operation["responses"] = responses
        
        if self.deprecated:
            operation["deprecated"] = True
        
        if self.operation_id:
            operation["operationId"] = self.operation_id
        
        return operation


class OpenAPIBuilder:
    """Build OpenAPI specifications"""
    
    def __init__(self, 
                 title: str = "API",
                 version: str = "1.0.0",
                 description: str = "",
                 base_path: str = "/api"):
        self.title = title
        self.version = version
        self.description = description
        self.base_path = base_path
        self.endpoints: Dict[str, Dict[str, Endpoint]] = {}
        self.tags: Dict[str, str] = {}
        self.servers: List[Dict[str, str]] = []
        self.security_schemes: Dict[str, Dict[str, Any]] = {}
    
    def add_endpoint(self, endpoint: Endpoint) -> None:
        """Add endpoint to specification"""
        path = endpoint.path
        method = endpoint.method.value
        
        if path not in self.endpoints:
            self.endpoints[path] = {}
        
        self.endpoints[path][method] = endpoint
        
        # Add tags
        for tag in endpoint.tags:
            if tag not in self.tags:
                self.tags[tag] = tag
        
        logger.debug(f"Added endpoint: {method.upper()} {path}")
    
    def add_tag(self, name: str, description: str = "") -> None:
        """Add tag definition"""
        self.tags[name] = description
    
    def add_server(self, url: str, description: str = "") -> None:
        """Add server definition"""
        server = {"url": url}
        if description:
            server["description"] = description
        self.servers.append(server)
    
    def add_security_scheme(self, name: str, scheme_type: str, 
                           **kwargs) -> None:
        """Add security scheme (e.g., OAuth2, Bearer)"""
        scheme = {"type": scheme_type}
        scheme.update(kwargs)
        self.security_schemes[name] = scheme
    
    def build(self) -> Dict[str, Any]:
        """Build complete OpenAPI specification"""
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": self.title,
                "version": self.version
            }
        }
        
        if self.description:
            spec["info"]["description"] = self.description
        
        spec["info"]["contact"] = {
            "name": "API Support"
        }
        
        # Add servers
        if self.servers:
            spec["servers"] = self.servers
        else:
            spec["servers"] = [{"url": self.base_path}]
        
        # Add paths
        paths = {}
        for path, methods in sorted(self.endpoints.items()):
            paths[path] = {}
            for method, endpoint in methods.items():
                paths[path][method] = endpoint.to_dict()
        
        spec["paths"] = paths
        
        # Add tags
        if self.tags:
            spec["tags"] = [
                {"name": name, "description": desc}
                for name, desc in self.tags.items()
            ]
        
        # Add security schemes
        if self.security_schemes:
            spec["components"] = {
                "securitySchemes": self.security_schemes
            }
        
        return spec
    
    def build_json(self, indent: int = 2) -> str:
        """Build and return as JSON string"""
        spec = self.build()
        return json.dumps(spec, indent=indent)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get specification summary"""
        total_endpoints = sum(len(methods) for methods in self.endpoints.values())
        
        method_counts = {}
        for methods in self.endpoints.values():
            for method in methods.keys():
                method_counts[method] = method_counts.get(method, 0) + 1
        
        return {
            "title": self.title,
            "version": self.version,
            "total_endpoints": total_endpoints,
            "paths": len(self.endpoints),
            "methods": method_counts,
            "tags": len(self.tags),
            "security_schemes": len(self.security_schemes)
        }


class SchemaGenerator:
    """Generate JSON schemas from Python types"""
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate schema from dictionary"""
        schema = {
            "type": "object",
            "properties": {}
        }
        
        for key, value in data.items():
            schema["properties"][key] = SchemaGenerator.infer_type(value)
        
        return schema
    
    @staticmethod
    def infer_type(value: Any) -> Dict[str, Any]:
        """Infer JSON schema from value"""
        if isinstance(value, bool):
            return {"type": "boolean"}
        elif isinstance(value, int):
            return {"type": "integer"}
        elif isinstance(value, float):
            return {"type": "number"}
        elif isinstance(value, str):
            return {"type": "string"}
        elif isinstance(value, list):
            if value:
                return {
                    "type": "array",
                    "items": SchemaGenerator.infer_type(value[0])
                }
            return {"type": "array"}
        elif isinstance(value, dict):
            return SchemaGenerator.from_dict(value)
        else:
            return {"type": "string"}
    
    @staticmethod
    def create_model_schema(name: str, properties: Dict[str, str],
                           required: List[str] = None) -> Dict[str, Any]:
        """Create a named schema"""
        schema = {
            "type": "object",
            "properties": {}
        }
        
        for prop_name, prop_type in properties.items():
            schema["properties"][prop_name] = {"type": prop_type}
        
        if required:
            schema["required"] = required
        
        return schema


# Global builder instance
_openapi_builder: Optional[OpenAPIBuilder] = None


def get_openapi_builder(title: str = "API",
                       version: str = "1.0.0") -> OpenAPIBuilder:
    """Get or create OpenAPI builder"""
    global _openapi_builder
    if _openapi_builder is None:
        _openapi_builder = OpenAPIBuilder(title, version)
    return _openapi_builder


def reset_openapi_builder() -> None:
    """Reset OpenAPI builder (for testing)"""
    global _openapi_builder
    _openapi_builder = None
