"""
Phase 53: Code Generation API Routes
Provides endpoints for generating client code, server stubs, and test suites from OpenAPI specs.
"""

from fastapi import APIRouter, HTTPException, Query, Body, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import json
import zipfile
import io
from datetime import datetime

from code_generator_service import (
    get_code_generation_service,
    CodeGenerationConfig,
    CodeGenerationService,
    CodeType,
    LanguageType,
    Endpoint,
    Parameter,
    Response,
    GeneratedCode,
)

router = APIRouter(prefix="/api/v1/codegen", tags=["code-generation"])


# Pydantic Models for Request/Response
class ParameterRequest(BaseModel):
    """Request model for endpoint parameter."""
    name: str
    type_hint: str
    required: bool = True
    default_value: Optional[str] = None
    description: str = ""
    location: str = "query"  # query, path, header, body


class ResponseRequest(BaseModel):
    """Request model for endpoint response."""
    status_code: int
    content_type: str = "application/json"
    schema: Dict[str, Any]
    description: str = ""


class EndpointRequest(BaseModel):
    """Request model for API endpoint."""
    path: str
    method: str
    summary: str
    parameters: List[ParameterRequest] = []
    request_body: Optional[Dict[str, Any]] = None
    responses: List[ResponseRequest] = []
    tags: List[str] = []
    deprecated: bool = False


class CodeGenerationRequest(BaseModel):
    """Request model for code generation."""
    endpoints: List[EndpointRequest]
    schemas: Optional[Dict[str, Any]] = None
    language: str = "python"  # python, typescript, javascript
    code_type: str = "client"  # client, server_stub, test_suite, models
    api_base_url: Optional[str] = None
    package_name: Optional[str] = None
    include_documentation: bool = True
    include_type_hints: bool = True
    include_error_handling: bool = True
    use_async: bool = True
    test_framework: str = "pytest"
    code_style: str = "pep8"


class GeneratedCodeResponse(BaseModel):
    """Response model for generated code file."""
    filename: str
    file_path: str
    language: str
    code_type: str
    size_bytes: int
    line_count: int
    imports: List[str] = []
    dependencies: List[str] = []
    preview: Optional[str] = None  # First 500 chars for preview
    metadata: Dict[str, Any] = {}


class CodeGenerationResponse(BaseModel):
    """Response model for code generation."""
    status: str = "success"
    timestamp: str
    language: str
    code_type: str
    file_count: int
    total_size_bytes: int
    total_lines: int
    files: List[GeneratedCodeResponse]
    message: str


class CodeGenerationStatistics(BaseModel):
    """Statistics about generated codes."""
    total_files: int
    total_size_bytes: int
    total_lines: int
    by_language: Dict[str, Dict[str, int]]
    by_code_type: Dict[str, Dict[str, int]]
    generation_history: Dict[str, Any]


# Helper functions
def convert_parameter_request(param: ParameterRequest) -> Parameter:
    """Convert request parameter to domain parameter."""
    return Parameter(
        name=param.name,
        type_hint=param.type_hint,
        required=param.required,
        default_value=param.default_value,
        description=param.description,
        location=param.location
    )


def convert_response_request(resp: ResponseRequest) -> Response:
    """Convert request response to domain response."""
    return Response(
        status_code=resp.status_code,
        content_type=resp.content_type,
        schema=resp.schema,
        description=resp.description
    )


def convert_endpoint_request(ep: EndpointRequest) -> Endpoint:
    """Convert request endpoint to domain endpoint."""
    return Endpoint(
        path=ep.path,
        method=ep.method,
        summary=ep.summary,
        parameters=[convert_parameter_request(p) for p in ep.parameters],
        request_body=ep.request_body,
        responses=[convert_response_request(r) for r in ep.responses],
        tags=ep.tags,
        deprecated=ep.deprecated
    )


def generated_code_to_response(code: GeneratedCode, include_preview: bool = True) -> GeneratedCodeResponse:
    """Convert generated code to response model."""
    preview = code.content[:500] + "..." if len(code.content) > 500 else code.content if include_preview else None
    return GeneratedCodeResponse(
        filename=code.filename,
        file_path=code.file_path,
        language=code.language.value,
        code_type=code.code_type.value,
        size_bytes=code.get_size_bytes(),
        line_count=code.get_line_count(),
        imports=code.imports,
        dependencies=code.dependencies,
        preview=preview,
        metadata=code.metadata
    )


@router.post("/generate", response_model=CodeGenerationResponse)
async def generate_code(request: CodeGenerationRequest) -> CodeGenerationResponse:
    """
    Generate code from OpenAPI specification.
    
    Generates client libraries, server stubs, or test suites in various languages
    from provided API endpoint definitions.
    """
    try:
        # Validate language
        try:
            language = LanguageType(request.language.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language: {request.language}. Supported: python, typescript, javascript"
            )

        # Validate code type
        try:
            code_type = CodeType(request.code_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported code type: {request.code_type}. Supported: client, server_stub, test_suite, models"
            )

        # Convert request to domain objects
        endpoints = [convert_endpoint_request(ep) for ep in request.endpoints]

        # Create configuration
        config = CodeGenerationConfig(
            language=language,
            code_type=code_type,
            include_documentation=request.include_documentation,
            include_type_hints=request.include_type_hints,
            include_error_handling=request.include_error_handling,
            api_base_url=request.api_base_url,
            package_name=request.package_name,
            use_async=request.use_async,
            test_framework=request.test_framework,
            code_style=request.code_style,
        )

        # Generate code
        service = get_code_generation_service()
        generated_codes = service.generate_code(endpoints, request.schemas, config)

        if not generated_codes:
            raise HTTPException(
                status_code=500,
                detail="Code generation failed: no files generated"
            )

        # Build response
        total_size = sum(c.get_size_bytes() for c in generated_codes)
        total_lines = sum(c.get_line_count() for c in generated_codes)
        files = [generated_code_to_response(c) for c in generated_codes]

        return CodeGenerationResponse(
            status="success",
            timestamp=datetime.now().isoformat(),
            language=request.language,
            code_type=request.code_type,
            file_count=len(generated_codes),
            total_size_bytes=total_size,
            total_lines=total_lines,
            files=files,
            message=f"Successfully generated {len(generated_codes)} file(s) totaling {total_size} bytes"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code generation failed: {str(e)}")


@router.post("/generate-client")
async def generate_client_code(
    endpoints: List[EndpointRequest] = Body(...),
    language: str = Query("python", description="Target language (python, typescript, javascript)"),
    api_base_url: Optional[str] = Query(None),
    package_name: Optional[str] = Query(None),
) -> CodeGenerationResponse:
    """Generate client library code from endpoints."""
    request = CodeGenerationRequest(
        endpoints=endpoints,
        language=language,
        code_type="client",
        api_base_url=api_base_url,
        package_name=package_name,
    )
    return await generate_code(request)


@router.post("/generate-server-stub")
async def generate_server_stub(
    endpoints: List[EndpointRequest] = Body(...),
    language: str = Query("python", description="Target language (python, typescript)"),
) -> CodeGenerationResponse:
    """Generate server stub code from endpoints."""
    request = CodeGenerationRequest(
        endpoints=endpoints,
        language=language,
        code_type="server_stub",
    )
    return await generate_code(request)


@router.post("/generate-tests")
async def generate_tests(
    endpoints: List[EndpointRequest] = Body(...),
    language: str = Query("python", description="Target language (python, typescript)"),
    test_framework: str = Query("pytest", description="Test framework (pytest, unittest, jest)"),
) -> CodeGenerationResponse:
    """Generate test suite code from endpoints."""
    request = CodeGenerationRequest(
        endpoints=endpoints,
        language=language,
        code_type="test_suite",
        test_framework=test_framework,
    )
    return await generate_code(request)


@router.post("/generate-models")
async def generate_models(
    schemas: Dict[str, Any] = Body(...),
    language: str = Query("python", description="Target language (python, typescript)"),
) -> CodeGenerationResponse:
    """Generate data models from JSON schemas."""
    request = CodeGenerationRequest(
        endpoints=[],
        schemas=schemas,
        language=language,
        code_type="models",
    )
    return await generate_code(request)


@router.get("/generated-codes")
async def get_generated_codes(
    language: Optional[str] = Query(None, description="Filter by language"),
    code_type: Optional[str] = Query(None, description="Filter by code type"),
    file_name: Optional[str] = Query(None, description="Filter by file name pattern"),
) -> Dict[str, Any]:
    """
    Get all generated codes.
    
    Returns list of all previously generated code files with metadata.
    """
    service = get_code_generation_service()
    codes = service.get_generated_codes()

    # Apply filters
    if language:
        codes = [c for c in codes if c.language.value == language.lower()]
    if code_type:
        codes = [c for c in codes if c.code_type.value == code_type.lower()]
    if file_name:
        codes = [c for c in codes if file_name.lower() in c.filename.lower()]

    return {
        "total": len(codes),
        "files": [generated_code_to_response(c, include_preview=False) for c in codes],
        "timestamp": datetime.now().isoformat()
    }


@router.get("/generated-codes/{filename}")
async def get_generated_code_content(filename: str) -> Dict[str, Any]:
    """
    Get full content of a generated code file.
    
    Returns the complete source code for the specified file.
    """
    service = get_code_generation_service()
    codes = service.get_generated_codes()

    for code in codes:
        if code.filename == filename:
            return {
                "filename": code.filename,
                "language": code.language.value,
                "code_type": code.code_type.value,
                "content": code.content,
                "size_bytes": code.get_size_bytes(),
                "line_count": code.get_line_count(),
                "imports": code.imports,
                "dependencies": code.dependencies,
            }

    raise HTTPException(status_code=404, detail=f"Generated code file not found: {filename}")


@router.post("/download/{format}")
async def download_generated_codes(
    format: str = "zip",
    language: Optional[str] = Query(None, description="Filter by language"),
) -> Dict[str, Any]:
    """
    Download generated codes in specified format.
    
    Supports formats: zip, json, tar
    Returns URL or inline content based on format.
    """
    service = get_code_generation_service()
    codes = service.get_generated_codes()

    # Apply language filter
    if language:
        codes = [c for c in codes if c.language.value == language.lower()]

    if not codes:
        raise HTTPException(status_code=404, detail="No generated codes found")

    if format.lower() == "json":
        return {
            "format": "json",
            "timestamp": datetime.now().isoformat(),
            "files": [generated_code_to_response(c, include_preview=False) for c in codes],
            "total_files": len(codes),
            "total_size_bytes": sum(c.get_size_bytes() for c in codes),
        }

    elif format.lower() == "zip":
        # Create in-memory zip file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for code in codes:
                zip_file.writestr(code.file_path, code.content)

        return {
            "format": "zip",
            "timestamp": datetime.now().isoformat(),
            "file_count": len(codes),
            "total_size_bytes": sum(c.get_size_bytes() for c in codes),
            "message": "Use binary download endpoint to retrieve zip file"
        }

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {format}. Supported: zip, json, tar"
        )


@router.get("/statistics")
async def get_statistics() -> CodeGenerationStatistics:
    """
    Get code generation statistics.
    
    Returns metrics about generated codes including:
    - Total files and size
    - Breakdown by language
    - Breakdown by code type
    - Generation history
    """
    service = get_code_generation_service()
    stats = service.get_statistics()

    return CodeGenerationStatistics(
        total_files=stats['total_files'],
        total_size_bytes=stats['total_size_bytes'],
        total_lines=stats['total_lines'],
        by_language=stats['by_language'],
        by_code_type=stats['by_code_type'],
        generation_history=stats['generation_history']
    )


@router.get("/supported-languages")
async def get_supported_languages() -> Dict[str, Any]:
    """
    Get list of supported programming languages.
    
    Returns available languages and their capabilities.
    """
    return {
        "languages": [
            {
                "name": "Python",
                "value": "python",
                "code_types": ["client", "server_stub", "test_suite", "models"],
                "test_frameworks": ["pytest", "unittest"],
                "features": ["async_support", "type_hints", "documentation"]
            },
            {
                "name": "TypeScript",
                "value": "typescript",
                "code_types": ["client", "server_stub", "test_suite", "models"],
                "test_frameworks": ["jest", "mocha"],
                "features": ["async_support", "type_hints", "documentation"]
            },
            {
                "name": "JavaScript",
                "value": "javascript",
                "code_types": ["client", "server_stub", "test_suite"],
                "test_frameworks": ["jest", "mocha"],
                "features": ["async_support", "documentation"]
            }
        ],
        "timestamp": datetime.now().isoformat()
    }


@router.get("/supported-code-types")
async def get_supported_code_types() -> Dict[str, Any]:
    """
    Get list of supported code generation types.
    
    Returns available code types and their descriptions.
    """
    return {
        "code_types": [
            {
                "name": "Client Library",
                "value": "client",
                "description": "Generate HTTP client library for consuming API",
                "supports_languages": ["python", "typescript", "javascript"]
            },
            {
                "name": "Server Stub",
                "value": "server_stub",
                "description": "Generate server implementation stub with placeholder routes",
                "supports_languages": ["python", "typescript"]
            },
            {
                "name": "Test Suite",
                "value": "test_suite",
                "description": "Generate comprehensive test suite for API endpoints",
                "supports_languages": ["python", "typescript", "javascript"]
            },
            {
                "name": "Models",
                "value": "models",
                "description": "Generate typed data models/interfaces from JSON schemas",
                "supports_languages": ["python", "typescript"]
            }
        ],
        "timestamp": datetime.now().isoformat()
    }


@router.post("/validate-endpoints")
async def validate_endpoints(endpoints: List[EndpointRequest]) -> Dict[str, Any]:
    """
    Validate endpoint definitions before code generation.
    
    Checks for common issues like duplicate paths, invalid methods, etc.
    """
    errors = []
    warnings = []
    paths_seen = set()

    for ep in endpoints:
        # Check path
        if not ep.path:
            errors.append("Endpoint path cannot be empty")
        elif not ep.path.startswith('/'):
            errors.append(f"Endpoint path must start with '/': {ep.path}")

        # Check method
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        if ep.method.upper() not in valid_methods:
            errors.append(f"Invalid HTTP method: {ep.method}")

        # Check for duplicate paths
        if ep.path in paths_seen:
            warnings.append(f"Duplicate endpoint path: {ep.path}")
        paths_seen.add(ep.path)

        # Check parameters
        if ep.parameters:
            param_names = set()
            for param in ep.parameters:
                if not param.name:
                    errors.append(f"Parameter name cannot be empty in {ep.path}")
                elif param.name in param_names:
                    errors.append(f"Duplicate parameter name '{param.name}' in {ep.path}")
                param_names.add(param.name)

        # Check responses
        if not ep.responses:
            warnings.append(f"No responses defined for {ep.path}")

    return {
        "valid": len(errors) == 0,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/clear-generated-codes")
async def clear_generated_codes() -> Dict[str, str]:
    """
    Clear all generated codes from memory.
    
    Useful for resetting the service state.
    """
    service = get_code_generation_service()
    code_count = len(service.get_generated_codes())
    service.clear_generated_codes()

    return {
        "status": "success",
        "message": f"Cleared {code_count} generated code files",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/health")
async def health() -> Dict[str, Any]:
    """Health check for code generation service."""
    service = get_code_generation_service()
    stats = service.get_statistics()

    return {
        "status": "healthy",
        "service": "Code Generation Service",
        "version": "1.0.0",
        "generated_files": stats['total_files'],
        "total_size_bytes": stats['total_size_bytes'],
        "timestamp": datetime.now().isoformat()
    }


# Export router
__all__ = ['router']
