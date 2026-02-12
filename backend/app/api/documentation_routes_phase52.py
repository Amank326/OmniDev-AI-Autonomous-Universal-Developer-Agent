"""
Phase 52: API Documentation Routes
FastAPI routes for API documentation and specifications
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging
import json

from backend.app.services.openapi_builder import (
    OpenAPIBuilder, Endpoint, Parameter, Response, HTTPMethod,
    SchemaGenerator, get_openapi_builder
)
from backend.app.services.endpoint_discovery import (
    EndpointDiscovery, EndpointInfo, RouteInfo, DocumentationGenerator,
    get_endpoint_discovery
)
from backend.app.services.schema_validator import (
    SchemaValidator, RequestValidator, ResponseValidator,
    ValidationRule, get_request_validator, get_response_validator
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/docs", tags=["documentation"])


# ============================================================================
# Pydantic Models
# ============================================================================

class EndpointDefinition(BaseModel):
    """Endpoint definition"""
    path: str
    method: str
    summary: str = ""
    description: str = ""
    tags: List[str] = []
    deprecated: bool = False


class SchemaDefinition(BaseModel):
    """Schema definition"""
    name: str
    properties: Dict[str, str]
    required: List[str] = []


class ValidationRuleDefinition(BaseModel):
    """Validation rule definition"""
    field_name: str
    field_type: str
    required: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None


class DocumentationResponse(BaseModel):
    """API documentation response"""
    title: str
    version: str
    description: str = ""
    routes: Dict[str, Any] = {}
    total_endpoints: int = 0


class OpenAPIResponse(BaseModel):
    """OpenAPI specification response"""
    openapi: str = "3.0.0"
    info: Dict[str, str] = {}
    paths: Dict[str, Any] = {}
    tags: List[Dict[str, str]] = []


# ============================================================================
# OpenAPI Routes
# ============================================================================

@router.get("/openapi.json", summary="Get OpenAPI specification")
async def get_openapi_spec() -> Dict[str, Any]:
    """Get complete OpenAPI specification"""
    try:
        builder = get_openapi_builder("OmniDev API", "1.0.0")
        
        # Add some default endpoints
        cache_endpoint = Endpoint(
            path="/api/v1/cache/get/{key}",
            method=HTTPMethod.GET,
            summary="Get cache value",
            description="Retrieve a value from the cache by key",
            tags=["cache"],
            parameters=[
                Parameter("key", "path", required=True, description="Cache key")
            ],
            responses=[Response(200, "Cache value retrieved")]
        )
        builder.add_endpoint(cache_endpoint)
        
        cache_stats_endpoint = Endpoint(
            path="/api/v1/cache/stats",
            method=HTTPMethod.GET,
            summary="Get cache statistics",
            description="Get current cache statistics",
            tags=["cache"],
            responses=[Response(200, "Cache statistics")]
        )
        builder.add_endpoint(cache_stats_endpoint)
        
        return builder.build()
    except Exception as e:
        logger.error(f"Error generating OpenAPI spec: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate spec: {str(e)}")


@router.get("/openapi.yaml", summary="Get OpenAPI YAML")
async def get_openapi_yaml() -> str:
    """Get OpenAPI specification as YAML"""
    try:
        spec = await get_openapi_spec()
        
        # Convert to YAML-like format
        import json
        yaml_str = json.dumps(spec, indent=2)
        
        return yaml_str
    except Exception as e:
        logger.error(f"Error generating OpenAPI YAML: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate YAML: {str(e)}")


@router.get("/swagger.json", summary="Get Swagger specification")
async def get_swagger_spec() -> Dict[str, Any]:
    """Get Swagger (OpenAPI 2.0) specification"""
    try:
        # For now, return OpenAPI 3.0
        return await get_openapi_spec()
    except Exception as e:
        logger.error(f"Error generating Swagger spec: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate spec: {str(e)}")


# ============================================================================
# Documentation Routes
# ============================================================================

@router.get("/", summary="Get API documentation")
async def get_documentation() -> Dict[str, Any]:
    """Get complete API documentation"""
    try:
        discovery = get_endpoint_discovery()
        doc = discovery.get_documentation(
            title="OmniDev API",
            version="1.0.0",
            description="Comprehensive API Documentation"
        )
        
        return{
            "title": doc.title,
            "version": doc.version,
            "description": doc.description,
            "routes": {
                prefix: {
                    "description": route.description,
                    "tags": route.tags,
                    "endpoints": len(route.endpoints)
                }
                for prefix, route in doc.routes.items()
            },
            "total_endpoints": doc.total_endpoints
        }
    except Exception as e:
        logger.error(f"Error getting documentation: {e}")
        raise HTTPException(status_code=500, detail=f"Documentation error: {str(e)}")


@router.get("/markdown", summary="Get documentation as Markdown")
async def get_markdown_docs() -> str:
    """Get documentation in Markdown format"""
    try:
        discovery = get_endpoint_discovery()
        generator = DocumentationGenerator(discovery)
        
        return generator.generate_markdown("OmniDev API Documentation")
    except Exception as e:
        logger.error(f"Error generating Markdown docs: {e}")
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")


@router.get("/html", summary="Get documentation as HTML")
async def get_html_docs() -> str:
    """Get documentation in HTML format"""
    try:
        discovery = get_endpoint_discovery()
        generator = DocumentationGenerator(discovery)
        
        return generator.generate_html("OmniDev API Documentation")
    except Exception as e:
        logger.error(f"Error generating HTML docs: {e}")
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")


# ============================================================================
# Endpoint Discovery Routes
# ============================================================================

@router.get("/endpoints", summary="Get all endpoints")
async def get_all_endpoints() -> Dict[str, Any]:
    """Get list of all discovered endpoints"""
    try:
        discovery = get_endpoint_discovery()
        summary = discovery.get_endpoint_summary()
        
        eps = []
        for route in discovery.routes.values():
            for endpoint in route.endpoints:
                eps.append({
                    "path": endpoint.path,
                    "method": endpoint.method,
                    "name": endpoint.name,
                    "summary": endpoint.summary,
                    "tags": endpoint.tags
                })
        
        return {
            "summary": summary,
            "endpoints": eps,
            "total": len(eps)
        }
    except Exception as e:
        logger.error(f"Error getting endpoints: {e}")
        raise HTTPException(status_code=500, detail=f"Discovery error: {str(e)}")


@router.get("/endpoints/by-method/{method}", summary="Get endpoints by method")
async def get_endpoints_by_method(method: str) -> Dict[str, Any]:
    """Get endpoints filtered by HTTP method"""
    try:
        discovery = get_endpoint_discovery()
        method_upper = method.upper()
        
        endpoints = []
        for route in discovery.routes.values():
            for endpoint in route.endpoints:
                if endpoint.method.upper() == method_upper:
                    endpoints.append({
                        "path": endpoint.path,
                        "method": endpoint.method,
                        "summary": endpoint.summary
                    })
        
        return {
            "method": method_upper,
            "endpoints": endpoints,
            "count": len(endpoints)
        }
    except Exception as e:
        logger.error(f"Error filtering endpoints: {e}")
        raise HTTPException(status_code=500, detail=f"Filter error: {str(e)}")


@router.get("/endpoints/by-tag/{tag}", summary="Get endpoints by tag")
async def get_endpoints_by_tag(tag: str) -> Dict[str, Any]:
    """Get endpoints filtered by tag"""
    try:
        discovery = get_endpoint_discovery()
        
        endpoints = []
        for route in discovery.routes.values():
            for endpoint in route.endpoints:
                if tag in endpoint.tags:
                    endpoints.append({
                        "path": endpoint.path,
                        "method": endpoint.method,
                        "summary": endpoint.summary
                    })
        
        return{
            "tag": tag,
            "endpoints": endpoints,
            "count": len(endpoints)
        }
    except Exception as e:
        logger.error(f"Error filtering by tag: {e}")
        raise HTTPException(status_code=500, detail=f"Filter error: {str(e)}")


# ============================================================================
# Schema & Validation Routes
# ============================================================================

@router.post("/validate/request", summary="Validate request")
async def validate_request(
    endpoint: str = Query(..., description="Endpoint path"),
    method: str = Query("POST", description="HTTP method"),
    body: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Validate a request against endpoint schema"""
    try:
        validator = get_request_validator()
        
        is_valid, errors = validator.validate_request(endpoint, method, body or {})
        
        return {
            "valid": is_valid,
            "errors": [e.to_dict() for e in errors],
            "error_count": len(errors)
        }
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


@router.post("/validate/response", summary="Validate response")
async def validate_response(
    endpoint: str = Query(..., description="Endpoint path"),
    status_code: int = Query(200, description="HTTP status code"),
    body: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Validate a response against endpoint schema"""
    try:
        validator = get_response_validator()
        
        is_valid, errors = validator.validate_response(endpoint, status_code, body or {})
        
        return {
            "valid": is_valid,
            "errors": [e.to_dict() for e in errors],
            "error_count": len(errors)
        }
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


# ============================================================================
# Schema Generation Routes
# ============================================================================

@router.post("/schemas/generate", summary="Generate schema from data")
async def generate_schema_from_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate JSON schema from sample data"""
    try:
        schema = SchemaGenerator.from_dict(data)
        
        return {
            "schema": schema,
            "properties_count": len(schema.get("properties", {}))
        }
    except Exception as e:
        logger.error(f"Schema generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")


@router.post("/schemas/create-model", summary="Create named schema")
async def create_model_schema(definition: SchemaDefinition) -> Dict[str, Any]:
    """Create a named schema model"""
    try:
        schema = SchemaGenerator.create_model_schema(
            definition.name,
            definition.properties,
            definition.required
        )
        
        return {
            "name": definition.name,
            "schema": schema,
            "created": True
        }
    except Exception as e:
        logger.error(f"Schema creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Creation error: {str(e)}")


# ============================================================================
# API Info Routes
# ============================================================================

@router.get("/info", summary="Get API information")
async def get_api_info() -> Dict[str, Any]:
    """Get API information and statistics"""
    try:
        discovery = get_endpoint_discovery()
        summary = discovery.get_endpoint_summary()
        
        # Get OpenAPI spec size
        spec = await get_openapi_spec()
        spec_size = len(json.dumps(spec))
        
        return {
            "api_info": {
                "title": "OmniDev API",
                "version": "1.0.0",
                "description": "Advanced API Gateway with Caching & Performance Optimization"
            },
            "statistics": {
                "total_routes": summary["total_routes"],
                "total_endpoints": summary["total_endpoints"],
                "http_methods": summary["methods"],
                "tags": summary["tags"]
            },
            "specifications": {
                "openapi_version": "3.0.0",
                "openapi_size_bytes": spec_size
            },
            "documentation_formats": ["json", "yaml", "markdown", "html", "swagger"]
        }
    except Exception as e:
        logger.error(f"Error getting API info: {e}")
        return {
            "version": "1.0.0",
            "error": str(e)
        }


@router.get("/health", summary="Health check")
async def health_check() -> Dict[str, Any]:
    """Health check for documentation service"""
    try:
        return {
            "status": "healthy",
            "service": "documentation",
            "components": {
                "openapi_builder": "operational",
                "endpoint_discovery": "operational",
                "schema_validator": "operational",
                "documentation_generator": "operational"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
