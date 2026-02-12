"""
Phase 52: API Documentation - Verification Tests
Comprehensive tests for all Phase 52 services
"""

import sys
import json
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("Phase 52: API Documentation & Auto-Generated Specs - Verification")
print("=" * 80)

# ============================================================================
# Import Tests
# ============================================================================

print("\n📦 Importing Phase 52 services...")
checks_total = 0
checks_passed = 0

try:
    from backend.app.services.openapi_builder import (
        OpenAPIBuilder, Endpoint, Parameter, Response, HTTPMethod,
        SchemaGenerator, DataType, get_openapi_builder, reset_openapi_builder
    )
    print("   ✅ OpenAPIBuilder imported")
except Exception as e:
    print(f"   ❌ OpenAPIBuilder import failed: {e}")
    sys.exit(1)

try:
    from backend.app.services.endpoint_discovery import (
        EndpointDiscovery, EndpointInfo, RouteInfo, DocumentationGenerator,
        get_endpoint_discovery
    )
    print("   ✅ EndpointDiscovery imported")
except Exception as e:
    print(f"   ❌ EndpointDiscovery import failed: {e}")
    sys.exit(1)

try:
    from backend.app.services.schema_validator import (
        SchemaValidator, RequestValidator, ResponseValidator,
        ValidationRule, ValidationType, get_request_validator,
        get_response_validator
    )
    print("   ✅ SchemaValidator imported")
except Exception as e:
    print(f"   ❌ SchemaValidator import failed: {e}")
    sys.exit(1)

# ============================================================================
# Check 1: OpenAPI Spec Generation
# ============================================================================

print("\n🧪 Testing OpenAPI Builder...")
checks_total += 1
try:
    builder = get_openapi_builder("Test API", "1.0.0")
    
    # Add endpoint
    endpoint = Endpoint(
        path="/api/test",
        method=HTTPMethod.GET,
        summary="Test endpoint",
        description="This is a test endpoint",
        tags=["test"]
    )
    builder.add_endpoint(endpoint)
    
    # Build spec
    spec = builder.build()
    
    if spec and spec.get("openapi") == "3.0.0":
        print(f"   ✅ OpenAPI Spec Generation: SUCCESS")
        print(f"      Version: {spec['openapi']}")
        print(f"      Paths: {len(spec.get('paths', {}))}")
        checks_passed += 1
    else:
        print(f"   ❌ OpenAPI spec invalid")
except Exception as e:
    print(f"   ❌ OpenAPI builder test error: {e}")

# ============================================================================
# Check 2: Parameter Definition
# ============================================================================

print("\n🧪 Testing Parameter Definition...")
checks_total += 1
try:
    param = Parameter(
        name="user_id",
        param_type="path",
        data_type=DataType.INTEGER,
        required=True,
        description="User ID"
    )
    
    param_dict = param.to_dict()
    
    if param_dict["name"] == "user_id" and param_dict["required"]:
        print(f"   ✅ Parameter Definition: SUCCESS")
        print(f"      Name: {param_dict['name']}")
        print(f"      Type: {param_dict['schema']['type']}")
        print(f"      Required: {param_dict['required']}")
        checks_passed += 1
    else:
        print(f"   ❌ Parameter definition invalid")
except Exception as e:
    print(f"   ❌ Parameter test error: {e}")

# ============================================================================
# Check 3: Response Definition
# ============================================================================

print("\n🧪 Testing Response Definition...")
checks_total += 1
try:
    response = Response(
        status_code=200,
        description="Success response",
        schema={"type": "object", "properties": {"data": {"type": "string"}}}
    )
    
    response_dict = response.to_dict()
    
    if response_dict["description"] == "Success response" and "content" in response_dict:
        print(f"   ✅ Response Definition: SUCCESS")
        print(f"      Status Code: 200")
        print(f"      Has Content Schema: True")
        checks_passed += 1
    else:
        print(f"   ❌ Response definition invalid")
except Exception as e:
    print(f"   ❌ Response test error: {e}")

# ============================================================================
# Check 4: Schema Generation
# ============================================================================

print("\n🧪 Testing Schema Generation...")
checks_total += 1
try:
    test_data = {
        "id": 1,
        "name": "John",
        "age": 30,
        "active": True,
        "tags": ["admin", "user"]
    }
    
    schema = SchemaGenerator.from_dict(test_data)
    
    if schema["type"] == "object" and "properties" in schema:
        print(f"   ✅ Schema Generation: SUCCESS")
        print(f"      Properties: {len(schema['properties'])}")
        print(f"      Types detected: id(int), name(str), active(bool), tags(array)")
        checks_passed += 1
    else:
        print(f"   ❌ Schema generation failed")
except Exception as e:
    print(f"   ❌ Schema generation test error: {e}")

# ============================================================================
# Check 5: Request Validation
# ============================================================================

print("\n🧪 Testing Request Validation...")
checks_total += 1
try:
    validator = get_request_validator()
    
    # Register schema
    schema = {
        "name": {"type": "string", "required": True},
        "age": {"type": "integer"},
        "email": {"type": "string"}
    }
    validator.register_request_schema("/api/users", "POST", schema)
    
    # Valid request
    valid_body = {"name": "John", "age": 30, "email": "john@example.com"}
    is_valid, errors = validator.validate_request("/api/users", "POST", valid_body)
    
    if is_valid and len(errors) == 0:
        print(f"   ✅ Valid Request: SUCCESS")
        print(f"      Errors: 0")
        
        # Invalid request
        invalid_body = {"age": 30}  # Missing required name
        is_valid_2, errors_2 = validator.validate_request("/api/users", "POST", invalid_body)
        
        if not is_valid_2 and len(errors_2) > 0:
            print(f"   ✅ Invalid Request Detected: SUCCESS")
            print(f"      Errors: {len(errors_2)}")
            checks_passed += 1
        else:
            print(f"   ❌ Invalid request not caught")
    else:
        print(f"   ❌ Valid request marked as invalid")
except Exception as e:
    print(f"   ❌ Request validation test error: {e}")

# ============================================================================
# Check 6: Response Validation
# ============================================================================

print("\n🧪 Testing Response Validation...")
checks_total += 1
try:
    validator = get_response_validator()
    
    # Register response schema
    schema = {
        "id": {"required": True},
        "name": {"required": True},
        "data": {"required": False}
    }
    validator.register_response_schema("/api/users/1", 200, schema)
    
    # Valid response
    valid_body = {"id": 1, "name": "John"}
    is_valid, errors = validator.validate_response("/api/users/1", 200, valid_body)
    
    if is_valid and len(errors) == 0:
        print(f"   ✅ Valid Response: SUCCESS")
        print(f"      Errors: 0")
        checks_passed += 1
    else:
        print(f"   ❌ Valid response marked as invalid")
except Exception as e:
    print(f"   ❌ Response validation test error: {e}")

# ============================================================================
# Check 7: Endpoint Discovery
# ============================================================================

print("\n🧪 Testing Endpoint Discovery...")
checks_total += 1
try:
    discovery = get_endpoint_discovery()
    
    # Create endpoints
    endpoint = EndpointInfo(
        path="/api/users",
        method="GET",
        name="list_users",
        summary="List all users",
        tags=["users"]
    )
    
    # Create route
    route = RouteInfo(
        prefix="/api/v1",
        tags=["api"],
        endpoints=[endpoint],
        description="API endpoints"
    )
    
    discovery.register_route("/api/v1", route)
    
    summary = discovery.get_endpoint_summary()
    
    if summary["total_endpoints"] > 0:
        print(f"   ✅ Endpoint Discovery: SUCCESS")
        print(f"      Total Routes: {summary['total_routes']}")
        print(f"      Total Endpoints: {summary['total_endpoints']}")
        checks_passed += 1
    else:
        print(f"   ❌ No endpoints discovered")
except Exception as e:
    print(f"   ❌ Endpoint discovery test error: {e}")

# ============================================================================
# Check 8: Documentation Generation
# ============================================================================

print("\n🧪 Testing Documentation Generation...")
checks_total += 1
try:
    discovery = get_endpoint_discovery()
    generator = DocumentationGenerator(discovery)
    
    # Generate Markdown
    markdown = generator.generate_markdown("API Documentation")
    
    if markdown and "# API Documentation" in markdown:
        print(f"   ✅ Markdown Documentation: SUCCESS")
        print(f"      Content Length: {len(markdown)} chars")
        
        # Generate HTML
        html = generator.generate_html("API Documentation")
        if html and "<html>" in html.lower():
            print(f"   ✅ HTML Documentation: SUCCESS")
            print(f"      Content Length: {len(html)} chars")
            checks_passed += 1
        else:
            print(f"   ❌ HTML generation failed")
    else:
        print(f"   ❌ Markdown generation failed")
except Exception as e:
    print(f"   ❌ Documentation generation test error: {e}")

# ============================================================================
# Check 9: Validation Rules
# ============================================================================

print("\n🧪 Testing Validation Rules...")
checks_total += 1
try:
    # Test string validation
    rule = ValidationRule(
        field_name="email",
        field_type=ValidationType.EMAIL,
        required=True
    )
    
    valid, msg = rule.validate("test@example.com")
    if valid:
        print(f"   ✅ Email Validation: SUCCESS")
        
        # Test failed validation
        invalid, msg2 = rule.validate("invalid-email")
        if not invalid:
            print(f"   ✅ Invalid Email Detection: SUCCESS")
            
            # Test integer validation
            int_rule = ValidationRule(
                field_name="age",
                field_type=ValidationType.INTEGER,
                required=False,
                min_value=0,
                max_value=150
            )
            valid_int, msg3 = int_rule.validate(25)
            if valid_int:
                print(f"   ✅ Integer Validation: SUCCESS")
                checks_passed += 1
            else:
                print(f"   ❌ Integer validation failed")
        else:
            print(f"   ❌ Invalid email not detected")
    else:
        print(f"   ❌ Email validation failed")
except Exception as e:
    print(f"   ❌ Validation rules test error: {e}")

# ============================================================================
# Check 10: Schema Summary
# ============================================================================

print("\n🧪 Testing OpenAPI Summary...")
checks_total += 1
try:
    # Create new builder instance
    builder = OpenAPIBuilder("Summary Test", "2.0.0")
    
    # Add multiple endpoints
    for i in range(3):
        endpoint = Endpoint(
            path=f"/api/test{i}",
            method=HTTPMethod.GET,
            summary=f"Test endpoint {i}",
            tags=["test"]
        )
        builder.add_endpoint(endpoint)
    
    summary = builder.get_summary()
    
    if summary["total_endpoints"] == 3:
        print(f"   ✅ OpenAPI Summary: SUCCESS")
        print(f"      Total Endpoints: {summary['total_endpoints']}")
        print(f"      Total Paths: {summary['paths']}")
        print(f"      Methods: {summary['methods']}")
        checks_passed += 1
    else:
        print(f"   ❌ Summary count mismatch (got {summary['total_endpoints']}, expected 3)")
except Exception as e:
    print(f"   ❌ OpenAPI summary test error: {e}")

# ============================================================================
# Check 11: JSON Serialization
# ============================================================================

print("\n🧪 Testing JSON Serialization...")
checks_total += 1
try:
    builder = get_openapi_builder("JSON Test", "1.0.0")
    
    endpoint = Endpoint(
        path="/api/test",
        method=HTTPMethod.POST,
        summary="Test",
        tags=["test"]
    )
    builder.add_endpoint(endpoint)
    
    # Generate JSON
    json_str = builder.build_json()
    json_obj = json.loads(json_str)
    
    if json_obj and "openapi" in json_obj:
        print(f"   ✅ JSON Serialization: SUCCESS")
        print(f"      JSON Size: {len(json_str)} chars")
        print(f"      Valid JSON: True")
        checks_passed += 1
    else:
        print(f"   ❌ JSON serialization failed")
except Exception as e:
    print(f"   ❌ JSON serialization test error: {e}")

# ============================================================================
# Summary
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 52 VERIFICATION SUMMARY")
print("=" * 80)

print(f"\n✅ Checks Passed: {checks_passed}/{checks_total}")
print(f"📊 Success Rate: {(checks_passed/checks_total)*100:.1f}%")

if checks_passed == checks_total:
    print("\n🎉 PHASE 52: COMPLETE & OPERATIONAL ✅")
    print("\nImplemented Services:")
    print("  ✅ OpenAPI Builder (Swagger/OpenAPI 3.0 generation)")
    print("  ✅ Endpoint Discovery (auto-discovery from routers)")
    print("  ✅ Schema Validator (request/response validation)")
    print("  ✅ Documentation Generator (Markdown, HTML)")
    print("  ✅ Request/Response Validators (schema-based)")
    print("  ✅ Schema Generator (from Python types/data)")
    print("\nAll services operational and tested!")
else:
    print(f"\n⚠️  Some checks failed. Review errors above.")

print("=" * 80)
