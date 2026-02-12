"""
Phase 53: Code Generation Service
Auto-generates client libraries, server stubs, and test suites from OpenAPI specifications.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import json
import re
from abc import ABC, abstractmethod
from datetime import datetime


class LanguageType(Enum):
    """Supported programming languages for code generation."""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"


class CodeType(Enum):
    """Types of code that can be generated."""
    CLIENT = "client"
    SERVER_STUB = "server_stub"
    TEST_SUITE = "test_suite"
    MODELS = "models"


@dataclass
class GeneratedCode:
    """Represents a single generated code file."""
    filename: str
    file_path: str
    language: LanguageType
    code_type: CodeType
    content: str
    imports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_size_bytes(self) -> int:
        """Get the size of generated code in bytes."""
        return len(self.content.encode('utf-8'))

    def get_line_count(self) -> int:
        """Get the number of lines in generated code."""
        return len(self.content.split('\n'))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'filename': self.filename,
            'file_path': self.file_path,
            'language': self.language.value,
            'code_type': self.code_type.value,
            'size_bytes': self.get_size_bytes(),
            'line_count': self.get_line_count(),
            'imports': self.imports,
            'dependencies': self.dependencies,
            'metadata': self.metadata
        }


@dataclass
class CodeGenerationConfig:
    """Configuration for code generation."""
    language: LanguageType
    code_type: CodeType
    include_documentation: bool = True
    include_type_hints: bool = True
    include_error_handling: bool = True
    api_base_url: Optional[str] = None
    package_name: Optional[str] = None
    output_directory: str = "./generated"
    use_async: bool = True
    test_framework: str = "pytest"  # pytest, unittest, jasmine, etc.
    code_style: str = "pep8"  # pep8 for Python, prettier for JS/TS
    extra_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Parameter:
    """API parameter definition."""
    name: str
    type_hint: str
    required: bool = True
    default_value: Optional[str] = None
    description: str = ""
    location: str = "query"  # query, path, header, body


@dataclass
class Response:
    """API response definition."""
    status_code: int
    content_type: str
    schema: Dict[str, Any]
    description: str = ""


@dataclass
class Endpoint:
    """API endpoint definition."""
    path: str
    method: str
    summary: str
    parameters: List[Parameter] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: List[Response] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    deprecated: bool = False


class CodeGenerator(ABC):
    """Base class for code generators."""

    def __init__(self, config: CodeGenerationConfig):
        """Initialize the code generator."""
        self.config = config
        self.generated_files: List[GeneratedCode] = []
        self.imports: Set[str] = set()
        self.dependencies: Set[str] = set()

    @abstractmethod
    def generate_client(self, endpoints: List[Endpoint]) -> List[GeneratedCode]:
        """Generate client code from endpoints."""
        pass

    @abstractmethod
    def generate_server_stub(self, endpoints: List[Endpoint]) -> List[GeneratedCode]:
        """Generate server stub code from endpoints."""
        pass

    @abstractmethod
    def generate_test_suite(self, endpoints: List[Endpoint]) -> List[GeneratedCode]:
        """Generate test suite code from endpoints."""
        pass

    @abstractmethod
    def generate_models(self, schemas: Dict[str, Any]) -> List[GeneratedCode]:
        """Generate data model code from schemas."""
        pass

    def _add_standard_imports(self) -> None:
        """Add standard imports for the language."""
        pass

    def _format_code(self, code: str) -> str:
        """Format generated code according to style guidelines."""
        return code

    def generate(self, endpoints: List[Endpoint], schemas: Optional[Dict[str, Any]] = None) -> List[GeneratedCode]:
        """Generate code based on configuration."""
        self.generated_files = []
        self.imports.clear()
        self.dependencies.clear()

        if self.config.code_type == CodeType.CLIENT:
            self.generated_files.extend(self.generate_client(endpoints))
        elif self.config.code_type == CodeType.SERVER_STUB:
            self.generated_files.extend(self.generate_server_stub(endpoints))
        elif self.config.code_type == CodeType.TEST_SUITE:
            self.generated_files.extend(self.generate_test_suite(endpoints))
        elif self.config.code_type == CodeType.MODELS and schemas:
            self.generated_files.extend(self.generate_models(schemas))

        return self.generated_files


class PythonCodeGenerator(CodeGenerator):
    """Generates Python code from OpenAPI specifications."""

    def generate_client(self, endpoints: List[Endpoint]) -> List[GeneratedCode]:
        """Generate a Python HTTP client."""
        generated = []

        # Generate main client module
        client_code = self._generate_python_client_module(endpoints)
        generated.append(GeneratedCode(
            filename="api_client.py",
            file_path=f"{self.config.output_directory}/api_client.py",
            language=LanguageType.PYTHON,
            code_type=CodeType.CLIENT,
            content=client_code,
            imports=['requests', 'typing', 'json', 'urllib.parse'],
            dependencies=['requests>=2.28.0']
        ))

        # Generate models module
        models_code = self._generate_python_models(endpoints)
        generated.append(GeneratedCode(
            filename="models.py",
            file_path=f"{self.config.output_directory}/models.py",
            language=LanguageType.PYTHON,
            code_type=CodeType.CLIENT,
            content=models_code,
            imports=['dataclasses', 'typing', 'json'],
            dependencies=[]
        ))

        return generated

    def generate_server_stub(self, endpoints: List[Endpoint]) -> List[GeneratedCode]:
        """Generate a Python FastAPI server stub."""
        generated = []

        stub_code = self._generate_python_server_stub(endpoints)
        generated.append(GeneratedCode(
            filename="server_stub.py",
            file_path=f"{self.config.output_directory}/server_stub.py",
            language=LanguageType.PYTHON,
            code_type=CodeType.SERVER_STUB,
            content=stub_code,
            imports=['fastapi', 'pydantic', 'typing'],
            dependencies=['fastapi>=0.95.0', 'pydantic>=2.0.0', 'uvicorn>=0.20.0']
        ))

        return generated

    def generate_test_suite(self, endpoints: List[Endpoint]) -> List[GeneratedCode]:
        """Generate pytest test suite."""
        generated = []

        test_code = self._generate_python_tests(endpoints)
        generated.append(GeneratedCode(
            filename="test_api.py",
            file_path=f"{self.config.output_directory}/test_api.py",
            language=LanguageType.PYTHON,
            code_type=CodeType.TEST_SUITE,
            content=test_code,
            imports=['pytest', 'requests', 'unittest.mock'],
            dependencies=['pytest>=7.0.0', 'pytest-cov>=4.0.0']
        ))

        return generated

    def generate_models(self, schemas: Dict[str, Any]) -> List[GeneratedCode]:
        """Generate Python dataclasses from JSON schemas."""
        generated = []

        models_code = self._generate_python_dataclass_models(schemas)
        generated.append(GeneratedCode(
            filename="models.py",
            file_path=f"{self.config.output_directory}/models.py",
            language=LanguageType.PYTHON,
            code_type=CodeType.MODELS,
            content=models_code,
            imports=['dataclasses', 'typing', 'json'],
            dependencies=[]
        ))

        return generated

    def _generate_python_client_module(self, endpoints: List[Endpoint]) -> str:
        """Generate Python client module code."""
        lines = [
            '"""',
            'Auto-generated API client.',
            f'Generated: {datetime.now().isoformat()}',
            '"""',
            '',
            'import requests',
            'import json',
            'from typing import Dict, Any, Optional, List',
            'from urllib.parse import urlencode',
            '',
            'class APIError(Exception):',
            '    """API communication error."""',
            '    pass',
            '',
            '',
            'class APIClient:',
            '    """HTTP client for API endpoints."""',
            '',
            '    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):',
            '        """Initialize API client."""',
            '        self.base_url = base_url.rstrip("/")',
            '        self.timeout = timeout',
            '        self.session = requests.Session()',
            '',
            '    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:',
            '        """Make HTTP request to API."""',
            '        url = f"{self.base_url}{endpoint}"',
            '        try:',
            '            response = self.session.request(method, url, timeout=self.timeout, **kwargs)',
            '            response.raise_for_status()',
            '            return response.json() if response.content else {}',
            '        except requests.RequestException as e:',
            '            raise APIError(f"Request failed: {str(e)}") from e',
            '        except json.JSONDecodeError as e:',
            '            raise APIError(f"Invalid response format: {str(e)}") from e',
            '',
        ]

        # Generate methods for each endpoint
        for endpoint in endpoints:
            method_name = self._endpoint_to_method_name(endpoint)
            lines.extend(self._generate_endpoint_method(endpoint, method_name))
            lines.append('')

        return '\n'.join(lines)

        return '\n'.join(lines)

    def _generate_endpoint_method(self, endpoint: Endpoint, method_name: str) -> List[str]:
        """Generate a single endpoint method."""
        lines = [
            f'    def {method_name}(self' + (''.join(
                f', {p.name}: {p.type_hint}' for p in endpoint.parameters
            )) + '):',
            f'        """{endpoint.summary}"""',
        ]

        # Build URL with path parameters
        path = endpoint.path
        for param in [p for p in endpoint.parameters if p.location == 'path']:
            path = path.replace(f'{{{param.name}}}', f'{{{param.name}}}')
        
        lines.append(f'        endpoint = "{path}"')

        # Add query parameters
        query_params = [p for p in endpoint.parameters if p.location == 'query']
        if query_params:
            lines.append('        params = {}')
            for param in query_params:
                lines.append(f'        params["{param.name}"] = {param.name}')
        else:
            lines.append('        params = {}')

        # Make request
        lines.append(f'        return self._make_request("{endpoint.method.upper()}", endpoint, params=params)')

        return lines

    def _generate_python_models(self, endpoints: List[Endpoint]) -> str:
        """Generate Python model definitions."""
        lines = [
            '"""Auto-generated data models."""',
            '',
            'from dataclasses import dataclass',
            'from typing import Any, Dict, Optional, List',
            'import json',
            '',
        ]

        # Generate model classes from responses
        models = set()
        for endpoint in endpoints:
            for response in endpoint.responses:
                if response.status_code == 200 and 'schema' in response.schema:
                    model_name = self._generate_model_from_schema(response.schema['schema'], response.status_code)
                    if model_name:
                        models.add(model_name)

        lines.append('@dataclass')
        lines.append('class APIResponse:')
        lines.append('    """Standard API response."""')
        lines.append('    status: int')
        lines.append('    data: Optional[Dict[str, Any]] = None')
        lines.append('    error: Optional[str] = None')

        return '\n'.join(lines)

    def _generate_python_server_stub(self, endpoints: List[Endpoint]) -> str:
        """Generate Python FastAPI server stub."""
        lines = [
            '"""',
            'Auto-generated FastAPI server stub.',
            f'Generated: {datetime.now().isoformat()}',
            '"""',
            '',
            'from fastapi import FastAPI, HTTPException, Query, Path',
            'from pydantic import BaseModel',
            'from typing import Optional, Dict, Any, List',
            'import uvicorn',
            '',
            'app = FastAPI(title="Generated API", version="1.0.0")',
            '',
        ]

        for endpoint in endpoints:
            lines.extend(self._generate_server_endpoint(endpoint))
            lines.append('')

        lines.extend([
            'if __name__ == "__main__":',
            '    uvicorn.run(app, host="0.0.0.0", port=8000)',
        ])

        return '\n'.join(lines)

    def _generate_server_endpoint(self, endpoint: Endpoint) -> List[str]:
        """Generate a single server endpoint stub."""
        decorator_path = endpoint.path.replace('{', '{').replace('}', '}')
        method = endpoint.method.lower()
        
        lines = [
            f'@app.{method}("{decorator_path}", tags={endpoint.tags})',
            f'async def {self._endpoint_to_method_name(endpoint)}(' + ''.join(
                f'{p.name}: {p.type_hint}' for p in endpoint.parameters
            ) + f') -> Dict[str, Any]:',
            f'    """{endpoint.summary}"""',
            '    # TODO: Implement endpoint logic',
            '    return {"message": "Not implemented"}',
        ]

        return lines

    def _generate_python_tests(self, endpoints: List[Endpoint]) -> str:
        """Generate pytest test suite."""
        lines = [
            '"""',
            'Auto-generated pytest test suite.',
            f'Generated: {datetime.now().isoformat()}',
            '"""',
            '',
            'import pytest',
            'import json',
            'from unittest.mock import Mock, patch, MagicMock',
            'from api_client import APIClient, APIError',
            '',
            'class TestAPIClient:',
            '    """Test suite for API client."""',
            '',
            '    @pytest.fixture',
            '    def client(self):',
            '        """Create API client for testing."""',
            '        return APIClient(base_url="http://localhost:8000")',
            '',
        ]

        for endpoint in endpoints:
            test_name = f'test_{self._endpoint_to_method_name(endpoint)}'
            lines.extend([
                f'    def {test_name}(self, client):',
                f'        """{endpoint.summary}"""',
                f'        # TODO: Implement test for {endpoint.path}',
                f'        # response = client.{self._endpoint_to_method_name(endpoint)}(...)',
                f'        # assert response is not None',
                '',
            ])

        return '\n'.join(lines)

    def _generate_python_dataclass_models(self, schemas: Dict[str, Any]) -> str:
        """Generate dataclass models from JSON schemas."""
        lines = [
            '"""Auto-generated dataclass models."""',
            '',
            'from dataclasses import dataclass, field',
            'from typing import Any, Dict, Optional, List',
            'import json',
            '',
        ]

        for schema_name, schema_def in schemas.items():
            if isinstance(schema_def, dict) and schema_def.get('type') == 'object':
                lines.append('@dataclass')
                lines.append(f'class {schema_name}:')
                lines.append(f'    """{schema_def.get("description", "")}"""')
                
                properties = schema_def.get('properties', {})
                if not properties:
                    lines.append('    pass')
                else:
                    for prop_name, prop_def in properties.items():
                        type_hint = self._json_type_to_python(prop_def.get('type', 'str'))
                        required = prop_name in schema_def.get('required', [])
                        if not required:
                            type_hint = f'Optional[{type_hint}]'
                        lines.append(f'    {prop_name}: {type_hint} = None')
                
                lines.append('')

        return '\n'.join(lines)

    def _endpoint_to_method_name(self, endpoint: Endpoint) -> str:
        """Convert endpoint path to valid Python method name."""
        name = endpoint.method.lower() + '_' + endpoint.path
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        name = re.sub(r'_+', '_', name).strip('_')
        return name

    def _generate_model_from_schema(self, schema: Any, status_code: int) -> str:
        """Extract model name from schema."""
        if isinstance(schema, dict):
            if '$ref' in schema:
                return schema['$ref'].split('/')[-1]
        return f"Response{status_code}"

    def _json_type_to_python(self, json_type: str) -> str:
        """Convert JSON schema type to Python type hint."""
        type_map = {
            'string': 'str',
            'integer': 'int',
            'number': 'float',
            'boolean': 'bool',
            'array': 'List',
            'object': 'Dict'
        }
        return type_map.get(json_type, 'Any')


class TypeScriptCodeGenerator(CodeGenerator):
    """Generates TypeScript code from OpenAPI specifications."""

    def generate_client(self, endpoints: List[Endpoint]) -> List[GeneratedCode]:
        """Generate a TypeScript HTTP client."""
        generated = []

        # Generate main client module
        client_code = self._generate_typescript_client_module(endpoints)
        generated.append(GeneratedCode(
            filename="api-client.ts",
            file_path=f"{self.config.output_directory}/api-client.ts",
            language=LanguageType.TYPESCRIPT,
            code_type=CodeType.CLIENT,
            content=client_code,
            imports=['axios', 'typing'],
            dependencies=['axios^1.4.0']
        ))

        # Generate models module
        models_code = self._generate_typescript_models(endpoints)
        generated.append(GeneratedCode(
            filename="models.ts",
            file_path=f"{self.config.output_directory}/models.ts",
            language=LanguageType.TYPESCRIPT,
            code_type=CodeType.CLIENT,
            content=models_code,
            imports=['typing'],
            dependencies=[]
        ))

        return generated

    def generate_server_stub(self, endpoints: List[Endpoint]) -> List[GeneratedCode]:
        """Generate a TypeScript Express server stub."""
        generated = []

        stub_code = self._generate_typescript_server_stub(endpoints)
        generated.append(GeneratedCode(
            filename="server-stub.ts",
            file_path=f"{self.config.output_directory}/server-stub.ts",
            language=LanguageType.TYPESCRIPT,
            code_type=CodeType.SERVER_STUB,
            content=stub_code,
            imports=['express', 'typing'],
            dependencies=['express^4.18.0', 'typescript^5.0.0']
        ))

        return generated

    def generate_test_suite(self, endpoints: List[Endpoint]) -> List[GeneratedCode]:
        """Generate Jest test suite."""
        generated = []

        test_code = self._generate_typescript_tests(endpoints)
        generated.append(GeneratedCode(
            filename="api-client.test.ts",
            file_path=f"{self.config.output_directory}/api-client.test.ts",
            language=LanguageType.TYPESCRIPT,
            code_type=CodeType.TEST_SUITE,
            content=test_code,
            imports=['jest', 'testing-library', 'axios-mock-adapter'],
            dependencies=['jest^29.0.0', 'ts-jest^29.0.0']
        ))

        return generated

    def generate_models(self, schemas: Dict[str, Any]) -> List[GeneratedCode]:
        """Generate TypeScript interfaces from JSON schemas."""
        generated = []

        models_code = self._generate_typescript_interface_models(schemas)
        generated.append(GeneratedCode(
            filename="models.ts",
            file_path=f"{self.config.output_directory}/models.ts",
            language=LanguageType.TYPESCRIPT,
            code_type=CodeType.MODELS,
            content=models_code,
            imports=[],
            dependencies=[]
        ))

        return generated

    def _generate_typescript_client_module(self, endpoints: List[Endpoint]) -> str:
        """Generate TypeScript client module code."""
        lines = [
            '/**',
            ' * Auto-generated API client.',
            f' * Generated: {datetime.now().isoformat()}',
            ' */',
            '',
            'import axios, { AxiosInstance, AxiosRequestConfig } from "axios";',
            'import { URLSearchParams } from "url";',
            '',
            'export class APIClient {',
            '  private client: AxiosInstance;',
            '  private baseUrl: string;',
            '',
            '  constructor(baseUrl: string = "http://localhost:8000") {',
            '    this.baseUrl = baseUrl;',
            '    this.client = axios.create({ baseURL: baseUrl });',
            '  }',
            '',
            '  private async makeRequest<T>(method: string, endpoint: string, config?: AxiosRequestConfig): Promise<T> {',
            '    try {',
            '      const response = await this.client.request<T>({',
            '        method,',
            '        url: endpoint,',
            '        ...config',
            '      });',
            '      return response.data;',
            '    } catch (error) {',
            '      throw new APIError(`Request failed: ${error}`);',
            '    }',
            '  }',
            '',
        ]

        # Generate methods for each endpoint
        for endpoint in endpoints:
            method_name = self._endpoint_to_method_name(endpoint)
            lines.extend(self._generate_typescript_endpoint_method(endpoint, method_name))
            lines.append('')

        lines.extend([
            '}',
            '',
            'export class APIError extends Error {',
            '  constructor(message: string) {',
            '    super(message);',
            '    this.name = "APIError";',
            '  }',
            '}',
        ])

        return '\n'.join(lines)

    def _generate_typescript_endpoint_method(self, endpoint: Endpoint, method_name: str) -> List[str]:
        """Generate a single TypeScript endpoint method."""
        params_str = ', '.join(
            f'{p.name}: {self._json_type_to_typescript(p.type_hint)}'
            for p in endpoint.parameters
        )
        
        lines = [
            f'  async {method_name}({params_str}): Promise<any> {{',
            f'    // {endpoint.summary}',
            f'    const endpoint = "{endpoint.path}";',
            '    const config: AxiosRequestConfig = {};',
            '    return this.makeRequest("' + endpoint.method.upper() + '", endpoint, config);',
            '  }',
        ]

        return lines

    def _generate_typescript_models(self, endpoints: List[Endpoint]) -> str:
        """Generate TypeScript model definitions."""
        lines = [
            '/**',
            ' * Auto-generated data models.',
            ' */',
            '',
            'export interface APIResponse<T = any> {',
            '  status: number;',
            '  data?: T;',
            '  error?: string;',
            '}',
            '',
        ]

        return '\n'.join(lines)

    def _generate_typescript_server_stub(self, endpoints: List[Endpoint]) -> str:
        """Generate TypeScript Express server stub."""
        lines = [
            '/**',
            ' * Auto-generated Express server stub.',
            f' * Generated: {datetime.now().isoformat()}',
            ' */',
            '',
            'import express, { Express, Request, Response } from "express";',
            '',
            'const app: Express = express();',
            'app.use(express.json());',
            '',
        ]

        for endpoint in endpoints:
            method = endpoint.method.lower()
            lines.append(f"app.{method}('{endpoint.path}', async (req: Request, res: Response) => {{")
            lines.append(f'  // {endpoint.summary}')
            lines.append('  // TODO: Implement endpoint logic')
            lines.append('  res.json({ message: "Not implemented" });')
            lines.append('});')
            lines.append('')

        lines.extend([
            'const PORT = process.env.PORT || 8000;',
            'app.listen(PORT, () => {',
            '  console.log(`Server running on port ${PORT}`);',
            '});',
        ])

        return '\n'.join(lines)

    def _generate_typescript_tests(self, endpoints: List[Endpoint]) -> str:
        """Generate Jest test suite."""
        lines = [
            '/**',
            ' * Auto-generated Jest test suite.',
            f' * Generated: {datetime.now().isoformat()}',
            ' */',
            '',
            'import { APIClient, APIError } from "./api-client";',
            '',
            'describe("APIClient", () => {',
            '  let client: APIClient;',
            '',
            '  beforeEach(() => {',
            '    client = new APIClient("http://localhost:8000");',
            '  });',
            '',
        ]

        for endpoint in endpoints:
            method_name = self._endpoint_to_method_name(endpoint)
            lines.extend([
                f'  test("should call {method_name}", async () => {{',
                f'    // TODO: Implement test for {endpoint.path}',
                '  });',
                '',
            ])

        lines.append('});')

        return '\n'.join(lines)

    def _generate_typescript_interface_models(self, schemas: Dict[str, Any]) -> str:
        """Generate TypeScript interface models from JSON schemas."""
        lines = [
            '/**',
            ' * Auto-generated TypeScript interfaces.',
            ' */',
            '',
        ]

        for schema_name, schema_def in schemas.items():
            if isinstance(schema_def, dict) and schema_def.get('type') == 'object':
                lines.append(f"export interface {schema_name} {{")
                
                properties = schema_def.get('properties', {})
                if not properties:
                    lines.append('  [key: string]: any;')
                else:
                    for prop_name, prop_def in properties.items():
                        type_hint = self._json_type_to_typescript(prop_def.get('type', 'string'))
                        required = prop_name in schema_def.get('required', [])
                        optional = '?' if not required else ''
                        lines.append(f'  {prop_name}{optional}: {type_hint};')
                
                lines.append('}')
                lines.append('')

        return '\n'.join(lines)

    def _endpoint_to_method_name(self, endpoint: Endpoint) -> str:
        """Convert endpoint path to valid TypeScript method name."""
        name = endpoint.method.lower() + '_' + endpoint.path.replace('/', '_').replace('{', '').replace('}', '')
        name = re.sub(r'_+', '_', name).strip('_')
        # Convert to camelCase
        parts = name.split('_')
        return parts[0] + ''.join(p.capitalize() for p in parts[1:])

    def _json_type_to_typescript(self, json_type: str) -> str:
        """Convert JSON schema type to TypeScript type."""
        type_map = {
            'string': 'string',
            'integer': 'number',
            'number': 'number',
            'boolean': 'boolean',
            'array': 'any[]',
            'object': 'Record<string, any>'
        }
        return type_map.get(json_type, 'any')


class CodeGenerationService:
    """Service for managing code generation from OpenAPI specs."""

    def __init__(self):
        """Initialize code generation service."""
        self.generators: Dict[LanguageType, type] = {
            LanguageType.PYTHON: PythonCodeGenerator,
            LanguageType.TYPESCRIPT: TypeScriptCodeGenerator,
        }
        self.generated_codes: List[GeneratedCode] = []
        self.generation_history: Dict[str, Any] = {}

    def generate_code(
        self,
        endpoints: List[Endpoint],
        schemas: Optional[Dict[str, Any]] = None,
        config: Optional[CodeGenerationConfig] = None
    ) -> List[GeneratedCode]:
        """Generate code from endpoints and schemas."""
        if config is None:
            config = CodeGenerationConfig(
                language=LanguageType.PYTHON,
                code_type=CodeType.CLIENT
            )

        generator_class = self.generators.get(config.language)
        if not generator_class:
            raise ValueError(f"Unsupported language: {config.language}")

        generator = generator_class(config)
        generated = generator.generate(endpoints, schemas)

        # Track generation
        self.generated_codes.extend(generated)
        self.generation_history[f"{config.language.value}_{config.code_type.value}"] = {
            'timestamp': datetime.now().isoformat(),
            'language': config.language.value,
            'code_type': config.code_type.value,
            'endpoint_count': len(endpoints),
            'file_count': len(generated),
            'total_size_bytes': sum(f.get_size_bytes() for f in generated),
            'total_lines': sum(f.get_line_count() for f in generated)
        }

        return generated

    def get_generated_codes(self) -> List[GeneratedCode]:
        """Get all generated codes."""
        return self.generated_codes

    def get_statistics(self) -> Dict[str, Any]:
        """Get code generation statistics."""
        return {
            'total_files': len(self.generated_codes),
            'total_size_bytes': sum(f.get_size_bytes() for f in self.generated_codes),
            'total_lines': sum(f.get_line_count() for f in self.generated_codes),
            'by_language': self._stats_by_language(),
            'by_code_type': self._stats_by_code_type(),
            'generation_history': self.generation_history
        }

    def _stats_by_language(self) -> Dict[str, Dict[str, int]]:
        """Get statistics grouped by language."""
        stats: Dict[str, Dict[str, int]] = {}
        for code in self.generated_codes:
            lang = code.language.value
            if lang not in stats:
                stats[lang] = {'files': 0, 'size_bytes': 0, 'lines': 0}
            stats[lang]['files'] += 1
            stats[lang]['size_bytes'] += code.get_size_bytes()
            stats[lang]['lines'] += code.get_line_count()
        return stats

    def _stats_by_code_type(self) -> Dict[str, Dict[str, int]]:
        """Get statistics grouped by code type."""
        stats: Dict[str, Dict[str, int]] = {}
        for code in self.generated_codes:
            code_type = code.code_type.value
            if code_type not in stats:
                stats[code_type] = {'files': 0, 'size_bytes': 0, 'lines': 0}
            stats[code_type]['files'] += 1
            stats[code_type]['size_bytes'] += code.get_size_bytes()
            stats[code_type]['lines'] += code.get_line_count()
        return stats

    def clear_generated_codes(self) -> None:
        """Clear all generated codes."""
        self.generated_codes.clear()
        self.generation_history.clear()


# Singleton instance
_code_generation_service: Optional[CodeGenerationService] = None


def get_code_generation_service() -> CodeGenerationService:
    """Get the code generation service singleton."""
    global _code_generation_service
    if _code_generation_service is None:
        _code_generation_service = CodeGenerationService()
    return _code_generation_service


def reset_code_generation_service() -> None:
    """Reset the code generation service (for testing)."""
    global _code_generation_service
    _code_generation_service = None
