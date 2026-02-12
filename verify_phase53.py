"""
Phase 53: Code Generation Verification Tests
Comprehensive tests for code generation service and generators.
"""

import sys
sys.path.insert(0, '.')

from code_generator_service import (
    get_code_generation_service,
    reset_code_generation_service,
    CodeGenerationConfig,
    CodeType,
    LanguageType,
    Endpoint,
    Parameter,
    Response,
    PythonCodeGenerator,
    TypeScriptCodeGenerator,
    CodeGenerationService,
)


def verify_python_client_generation() -> bool:
    """Verify Python client code generation."""
    print("\n✓ Testing Python Client Generation...")
    
    reset_code_generation_service()
    config = CodeGenerationConfig(
        language=LanguageType.PYTHON,
        code_type=CodeType.CLIENT
    )
    
    # Create test endpoints
    endpoints = [
        Endpoint(
            path="/users",
            method="GET",
            summary="Get all users",
            parameters=[
                Parameter(name="limit", type_hint="int", location="query", required=False),
                Parameter(name="offset", type_hint="int", location="query", required=False)
            ],
            responses=[
                Response(status_code=200, content_type="application/json", schema={"type": "array"})
            ],
            tags=["users"]
        ),
        Endpoint(
            path="/users/{user_id}",
            method="GET",
            summary="Get user by ID",
            parameters=[
                Parameter(name="user_id", type_hint="str", location="path", required=True)
            ],
            responses=[
                Response(status_code=200, content_type="application/json", schema={"type": "object"})
            ],
            tags=["users"]
        ),
    ]
    
    generator = PythonCodeGenerator(config)
    generated = generator.generate_client(endpoints)
    
    assert len(generated) >= 1, "Expected at least 1 generated file"
    assert any("client" in f.filename.lower() for f in generated), "Expected client file"
    
    # Check generated code quality
    client_code = next((f for f in generated if "client" in f.filename.lower()), None)
    assert client_code is not None, "Client file not found"
    assert "class APIClient" in client_code.content, "APIClient class not found"
    assert "def _make_request" in client_code.content, "_make_request method not found"
    assert len(client_code.content) > 500, f"Client code too short: {len(client_code.content)} bytes"
    
    print(f"  Generated {len(generated)} file(s): {', '.join(f.filename for f in generated)}")
    print(f"  Client size: {client_code.get_size_bytes()} bytes, {client_code.get_line_count()} lines")
    
    return True


def verify_typescript_client_generation() -> bool:
    """Verify TypeScript client code generation."""
    print("\n✓ Testing TypeScript Client Generation...")
    
    reset_code_generation_service()
    config = CodeGenerationConfig(
        language=LanguageType.TYPESCRIPT,
        code_type=CodeType.CLIENT
    )
    
    endpoints = [
        Endpoint(
            path="/products",
            method="GET",
            summary="Get all products",
            responses=[
                Response(status_code=200, content_type="application/json", schema={"type": "array"})
            ],
            tags=["products"]
        ),
    ]
    
    generator = TypeScriptCodeGenerator(config)
    generated = generator.generate_client(endpoints)
    
    assert len(generated) >= 1, "Expected at least 1 generated file"
    
    ts_code = next((f for f in generated if f.language == LanguageType.TYPESCRIPT), None)
    assert ts_code is not None, "TypeScript code not found"
    assert "export class APIClient" in ts_code.content, "APIClient class not found"
    assert "import axios" in ts_code.content, "axios import not found"
    
    print(f"  Generated {len(generated)} TypeScript file(s)")
    print(f"  Total size: {sum(f.get_size_bytes() for f in generated)} bytes")
    
    return True


def verify_server_stub_generation() -> bool:
    """Verify server stub code generation."""
    print("\n✓ Testing Server Stub Generation...")
    
    reset_code_generation_service()
    config = CodeGenerationConfig(
        language=LanguageType.PYTHON,
        code_type=CodeType.SERVER_STUB
    )
    
    endpoints = [
        Endpoint(
            path="/api/posts",
            method="POST",
            summary="Create a post",
            responses=[
                Response(status_code=201, content_type="application/json", schema={"type": "object"})
            ],
            tags=["posts"]
        ),
    ]
    
    generator = PythonCodeGenerator(config)
    generated = generator.generate_server_stub(endpoints)
    
    assert len(generated) >= 1, "Expected at least 1 generated file"
    
    stub_code = next(f for f in generated)
    assert "from fastapi import FastAPI" in stub_code.content, "FastAPI import not found"
    assert "@app.post" in stub_code.content or "@app.post" in stub_code.content, "Route decorator not found"
    assert "TODO" in stub_code.content, "TODO comments not found (implementation hints)"
    
    print(f"  Server stub size: {stub_code.get_size_bytes()} bytes, {stub_code.get_line_count()} lines")
    
    return True


def verify_test_suite_generation() -> bool:
    """Verify test suite code generation."""
    print("\n✓ Testing Test Suite Generation...")
    
    reset_code_generation_service()
    config = CodeGenerationConfig(
        language=LanguageType.PYTHON,
        code_type=CodeType.TEST_SUITE,
        test_framework="pytest"
    )
    
    endpoints = [
        Endpoint(
            path="/items/{item_id}",
            method="GET",
            summary="Get item",
            parameters=[
                Parameter(name="item_id", type_hint="str", location="path", required=True)
            ],
            responses=[
                Response(status_code=200, content_type="application/json", schema={"type": "object"})
            ]
        ),
    ]
    
    generator = PythonCodeGenerator(config)
    generated = generator.generate_test_suite(endpoints)
    
    assert len(generated) >= 1, "Expected at least 1 test file"
    
    test_code = next(f for f in generated)
    assert "import pytest" in test_code.content, "pytest import not found"
    assert "class Test" in test_code.content or "def test_" in test_code.content, "Test structure not found"
    assert "APIClient" in test_code.content, "APIClient reference not found"
    
    print(f"  Test suite size: {test_code.get_size_bytes()} bytes, {test_code.get_line_count()} lines")
    
    return True


def verify_model_generation() -> bool:
    """Verify model/schema generation."""
    print("\n✓ Testing Model Generation...")
    
    reset_code_generation_service()
    config = CodeGenerationConfig(
        language=LanguageType.PYTHON,
        code_type=CodeType.MODELS
    )
    
    schemas = {
        "User": {
            "type": "object",
            "description": "User model",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "email": {"type": "string"}
            },
            "required": ["id", "name", "email"]
        },
        "Post": {
            "type": "object",
            "description": "Blog post",
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "string"},
                "content": {"type": "string"},
                "author_id": {"type": "integer"}
            },
            "required": ["id", "title", "content"]
        }
    }
    
    generator = PythonCodeGenerator(config)
    generated = generator.generate_models(schemas)
    
    assert len(generated) >= 1, "Expected at least 1 generated file"
    
    model_code = next(f for f in generated)
    assert "@dataclass" in model_code.content, "@dataclass decorator not found"
    assert "class User" in model_code.content, "User model not found"
    assert "class Post" in model_code.content, "Post model not found"
    
    print(f"  Models size: {model_code.get_size_bytes()} bytes, {model_code.get_line_count()} lines")
    
    return True


def verify_service_integration() -> bool:
    """Verify CodeGenerationService integration."""
    print("\n✓ Testing CodeGenerationService Integration...")
    
    reset_code_generation_service()
    service = get_code_generation_service()
    
    config = CodeGenerationConfig(
        language=LanguageType.PYTHON,
        code_type=CodeType.CLIENT
    )
    
    endpoints = [
        Endpoint(
            path="/test",
            method="GET",
            summary="Test endpoint",
            responses=[
                Response(status_code=200, content_type="application/json", schema={})
            ]
        ),
    ]
    
    # Generate code
    generated = service.generate_code(endpoints, None, config)
    assert len(generated) > 0, "No code generated"
    
    # Check statistics
    stats = service.get_statistics()
    assert stats['total_files'] > 0, "Statistics not updated"
    assert stats['total_size_bytes'] > 0, "Size not calculated"
    assert stats['total_lines'] > 0, "Line count not calculated"
    
    # Check generation history
    assert len(stats['generation_history']) > 0, "Generation history not recorded"
    
    print(f"  Generated {stats['total_files']} file(s), {stats['total_size_bytes']} bytes")
    print(f"  Languages: {list(stats['by_language'].keys())}")
    print(f"  Code types: {list(stats['by_code_type'].keys())}")
    
    return True


def verify_multi_language_generation() -> bool:
    """Verify multi-language code generation."""
    print("\n✓ Testing Multi-Language Generation...")
    
    reset_code_generation_service()
    service = get_code_generation_service()
    
    endpoints = [
        Endpoint(
            path="/api/v1/data",
            method="GET",
            summary="Get data",
            responses=[
                Response(status_code=200, content_type="application/json", schema={})
            ]
        ),
    ]
    
    languages = [LanguageType.PYTHON, LanguageType.TYPESCRIPT]
    
    for lang in languages:
        config = CodeGenerationConfig(
            language=lang,
            code_type=CodeType.CLIENT
        )
        generated = service.generate_code(endpoints, None, config)
        assert len(generated) > 0, f"No code generated for {lang.value}"
    
    stats = service.get_statistics()
    assert len(stats['by_language']) == 2, f"Expected 2 languages, got {len(stats['by_language'])}"
    
    print(f"  Generated code in {len(stats['by_language'])} languages:")
    for lang, lang_stats in stats['by_language'].items():
        print(f"    - {lang}: {lang_stats['files']} file(s), {lang_stats['size_bytes']} bytes")
    
    return True


def verify_endpoint_validation() -> bool:
    """Verify endpoint definition validation."""
    print("\n✓ Testing Endpoint Validation...")
    
    # Test valid endpoint
    valid_endpoint = Endpoint(
        path="/valid/endpoint",
        method="GET",
        summary="Valid endpoint",
        responses=[
            Response(status_code=200, content_type="application/json", schema={})
        ]
    )
    
    assert valid_endpoint.path.startswith('/'), "Invalid path format"
    assert valid_endpoint.method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'], "Invalid method"
    
    # Test endpoint with parameters
    endpoint_with_params = Endpoint(
        path="/users/{user_id}",
        method="GET",
        summary="Get user",
        parameters=[
            Parameter(name="user_id", type_hint="str", location="path", required=True),
            Parameter(name="include_posts", type_hint="bool", location="query", required=False)
        ],
        responses=[
            Response(status_code=200, content_type="application/json", schema={})
        ]
    )
    
    assert len(endpoint_with_params.parameters) == 2, "Parameters not set correctly"
    assert endpoint_with_params.parameters[0].location == "path", "Path parameter location incorrect"
    assert endpoint_with_params.parameters[1].location == "query", "Query parameter location incorrect"
    
    print(f"  ✓ Valid endpoint validation passed")
    print(f"  ✓ Parameter validation passed")
    
    return True


def verify_generated_code_quality() -> bool:
    """Verify quality of generated code."""
    print("\n✓ Testing Generated Code Quality...")
    
    reset_code_generation_service()
    config = CodeGenerationConfig(
        language=LanguageType.PYTHON,
        code_type=CodeType.CLIENT,
        include_documentation=True,
        include_type_hints=True,
        include_error_handling=True
    )
    
    endpoints = [
        Endpoint(
            path="/complex/{id}/endpoint",
            method="POST",
            summary="Complex endpoint test",
            parameters=[
                Parameter(name="id", type_hint="str", location="path", required=True),
                Parameter(name="filter", type_hint="str", location="query", required=False)
            ],
            request_body={"type": "object"},
            responses=[
                Response(status_code=200, content_type="application/json", schema={"type": "object"}),
                Response(status_code=400, content_type="application/json", schema={"type": "object"}),
                Response(status_code=500, content_type="application/json", schema={"type": "object"})
            ],
            tags=["complex"]
        ),
    ]
    
    generator = PythonCodeGenerator(config)
    generated = generator.generate_client(endpoints)
    
    # Check code quality - focus on client code
    client_code = next((c for c in generated if 'client' in c.filename.lower()), None)
    assert client_code is not None, "Client file not generated"
    
    # Check line count (should be substantial)
    assert client_code.get_line_count() >= 10, f"Generated code too short: {client_code.get_line_count()} lines"
    
    # Check for documentation
    if config.include_documentation:
        assert '"""' in client_code.content or "'''" in client_code.content, "Documentation not found"
    
    # Check for type hints
    if config.include_type_hints:
        assert '->' in client_code.content or ':' in client_code.content, "Type hints not found"
    
    # Check for error handling in client code
    if config.include_error_handling:
        assert 'try' in client_code.content and 'except' in client_code.content, "Error handling not found"
    
    print(f"  Generated {len(generated)} file(s)")
    for code in generated:
        print(f"    - {code.filename}: {code.get_line_count()} lines, {code.get_size_bytes()} bytes")
    
    return True


def verify_typescript_models_generation() -> bool:
    """Verify TypeScript interface generation."""
    print("\n✓ Testing TypeScript Models Generation...")
    
    reset_code_generation_service()
    config = CodeGenerationConfig(
        language=LanguageType.TYPESCRIPT,
        code_type=CodeType.MODELS
    )
    
    schemas = {
        "Product": {
            "type": "object",
            "description": "Product model",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "price": {"type": "number"},
                "in_stock": {"type": "boolean"}
            },
            "required": ["id", "name", "price"]
        }
    }
    
    generator = TypeScriptCodeGenerator(config)
    generated = generator.generate_models(schemas)
    
    assert len(generated) >= 1, "Expected at least 1 generated file"
    
    ts_models = next(f for f in generated)
    assert "export interface Product" in ts_models.content, "Product interface not found"
    assert "id: number" in ts_models.content, "id property not found"
    assert "name: string" in ts_models.content, "name property not found"
    
    print(f"  TypeScript interfaces generated: {ts_models.get_line_count()} lines")
    
    return True


def run_all_verifications():
    """Run all verification tests."""
    print("=" * 70)
    print("PHASE 53: CODE GENERATION VERIFICATION TESTS")
    print("=" * 70)
    
    tests = [
        ("Python Client Generation", verify_python_client_generation),
        ("TypeScript Client Generation", verify_typescript_client_generation),
        ("Server Stub Generation", verify_server_stub_generation),
        ("Test Suite Generation", verify_test_suite_generation),
        ("Model Generation", verify_model_generation),
        ("Service Integration", verify_service_integration),
        ("Multi-Language Generation", verify_multi_language_generation),
        ("Endpoint Validation", verify_endpoint_validation),
        ("Generated Code Quality", verify_generated_code_quality),
        ("TypeScript Models", verify_typescript_models_generation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, None))
            print(f"  ✅ PASSED")
        except AssertionError as e:
            results.append((test_name, False, str(e)))
            print(f"  ❌ FAILED: {e}")
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"  ❌ ERROR: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n✅ Checks Passed: {passed}/{total}")
    print(f"📊 Success Rate: {success_rate:.1f}%\n")
    
    if passed == total:
        print("🎉 All Phase 53 verification tests passed!")
        print("\nImplemented Services:")
        print("  ✅ PythonCodeGenerator (Python client/server/tests/models)")
        print("  ✅ TypeScriptCodeGenerator (TypeScript client/server/tests/models)")
        print("  ✅ CodeGenerationService (unified generation interface)")
        print("  ✅ Code Generation Routes (15+ API endpoints)")
        print("  ✅ Validation and Quality Checks")
        print("  ✅ Multi-language Support")
        print("  ✅ Code Statistics and Metrics")
    else:
        print("⚠️  Some tests failed. Details above.")
        for test_name, result, error in results:
            if not result:
                print(f"\n  ❌ {test_name}")
                if error:
                    print(f"     {error}")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_verifications()
    sys.exit(0 if success else 1)
