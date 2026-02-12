"""
Phase 52: Endpoint Discovery & Documentation Service
Auto-discover API endpoints and generate documentation
"""

import inspect
from typing import Dict, Any, List, Optional, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class EndpointInfo:
    """Information about an API endpoint"""
    path: str
    method: str
    name: str
    description: str = ""
    summary: str = ""
    tags: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    response_code: int = 200
    deprecated: bool = False
    auth_required: bool = False
    rate_limited: bool = False


@dataclass
class RouteInfo:
    """Information about a route module"""
    prefix: str
    tags: List[str] = field(default_factory=list)
    endpoints: List[EndpointInfo] = field(default_factory=list)
    description: str = ""


@dataclass
class APIDocumentation:
    """Complete API documentation"""
    title: str
    version: str
    description: str = ""
    base_url: str = ""
    routes: Dict[str, RouteInfo] = field(default_factory=dict)
    total_endpoints: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "title": self.title,
            "version": self.version,
            "description": self.description,
            "base_url": self.base_url,
            "total_endpoints": self.total_endpoints,
            "routes": {
                prefix: {
                    "description": route.description,
                    "tags": route.tags,
                    "endpoints": [
                        {
                            "path": ep.path,
                            "method": ep.method,
                            "name": ep.name,
                            "description": ep.description,
                            "summary": ep.summary,
                            "tags": ep.tags,
                            "auth_required": ep.auth_required,
                            "rate_limited": ep.rate_limited
                        }
                        for ep in route.endpoints
                    ]
                }
                for prefix, route in self.routes.items()
            }
        }


class EndpointDiscovery:
    """Discover API endpoints automatically"""
    
    def __init__(self):
        self.discovered_endpoints: Dict[str, List[EndpointInfo]] = defaultdict(list)
        self.routes: Dict[str, RouteInfo] = {}
    
    def discover_from_router(self, router) -> List[EndpointInfo]:
        """
        Discover endpoints from FastAPI router
        
        Args:
            router: FastAPI APIRouter instance
        
        Returns:
            List of discovered endpoints
        """
        endpoints = []
        
        try:
            # Try to extract routes from router
            if hasattr(router, 'routes'):
                for route in router.routes:
                    endpoint_info = self._extract_endpoint_info(route)
                    if endpoint_info:
                        endpoints.append(endpoint_info)
                        logger.debug(f"Discovered endpoint: {endpoint_info.method.upper()} {endpoint_info.path}")
        except Exception as e:
            logger.warning(f"Error discovering endpoints: {e}")
        
        return endpoints
    
    def discover_from_function(self, func: Callable, method: str = "GET",
                               path: str = "") -> Optional[EndpointInfo]:
        """
        Discover endpoint from function
        
        Args:
            func: Function to analyze
            method: HTTP method
            path: URL path
        
        Returns:
            EndpointInfo or None
        """
        try:
            # Get function name
            name = func.__name__
            
            # Get docstring as description
            description = inspect.getdoc(func) or ""
            
            # Get function parameters
            sig = inspect.signature(func)
            parameters = list(sig.parameters.keys())
            
            # Get return type
            return_annotation = sig.return_annotation
            response_code = 200
            
            endpoint = EndpointInfo(
                path=path or f"/{name}",
                method=method.upper(),
                name=name,
                description=description,
                parameters=parameters,
                response_code=response_code
            )
            
            logger.debug(f"Discovered function endpoint: {method.upper()} {path}")
            
            return endpoint
        except Exception as e:
            logger.warning(f"Error analyzing function {func.__name__}: {e}")
            return None
    
    def register_route(self, prefix: str, route_info: RouteInfo) -> None:
        """Register a route with endpoints"""
        self.routes[prefix] = route_info
        logger.info(f"Registered route: {prefix} ({len(route_info.endpoints)} endpoints)")
    
    def get_documentation(self, title: str = "API", 
                         version: str = "1.0.0",
                         description: str = "") -> APIDocumentation:
        """Get complete API documentation"""
        total_endpoints = sum(
            len(route.endpoints) 
            for route in self.routes.values()
        )
        
        return APIDocumentation(
            title=title,
            version=version,
            description=description,
            routes=self.routes,
            total_endpoints=total_endpoints
        )
    
    def get_endpoint_summary(self) -> Dict[str, Any]:
        """Get summary of discovered endpoints"""
        endpoints_by_method = defaultdict(int)
        endpoints_by_tag = defaultdict(int)
        
        for route in self.routes.values():
            for endpoint in route.endpoints:
                endpoints_by_method[endpoint.method] += 1
                for tag in endpoint.tags:
                    endpoints_by_tag[tag] += 1
        
        return {
            "total_routes": len(self.routes),
            "total_endpoints": sum(len(r.endpoints) for r in self.routes.values()),
            "methods": dict(endpoints_by_method),
            "tags": dict(endpoints_by_tag)
        }
    
    def _extract_endpoint_info(self, route) -> Optional[EndpointInfo]:
        """Extract endpoint info from FastAPI route"""
        try:
            path = route.path if hasattr(route, 'path') else ""
            name = route.name if hasattr(route, 'name') else ""
            
            methods = getattr(route, 'methods', {'GET'})
            method = list(methods)[0] if methods else "GET"
            
            # Get summary from route
            summary = getattr(route, 'summary', "") or ""
            description = getattr(route, 'description', "") or ""
            tags = getattr(route, 'tags', []) or []
            
            return EndpointInfo(
                path=path,
                method=method,
                name=name,
                summary=summary,
                description=description,
                tags=tags
            )
        except Exception as e:
            logger.debug(f"Could not extract endpoint info: {e}")
            return None


class DocumentationGenerator:
    """Generate documentation from discovered endpoints"""
    
    def __init__(self, discovery: EndpointDiscovery):
        self.discovery = discovery
    
    def generate_markdown(self, title: str = "API Documentation") -> str:
        """Generate Markdown documentation"""
        lines = [
            f"# {title}",
            "",
            f"**Generated**: {__import__('datetime').datetime.utcnow().isoformat()}",
            ""
        ]
        
        summary = self.discovery.get_endpoint_summary()
        lines.extend([
            "## Overview",
            "",
            f"- **Total Routes**: {summary['total_routes']}",
            f"- **Total Endpoints**: {summary['total_endpoints']}",
            f"- **HTTP Methods**: {', '.join(summary['methods'].keys())}",
            ""
        ])
        
        # Add endpoints by section
        for prefix, route in sorted(self.discovery.routes.items()):
            lines.extend([
                f"## {prefix.lstrip('/')}",
                ""
            ])
            
            if route.description:
                lines.append(f"{route.description}\n")
            
            if route.tags:
                lines.append(f"**Tags**: {', '.join(route.tags)}\n")
            
            for endpoint in route.endpoints:
                lines.extend([
                    f"### {endpoint.method.upper()} {endpoint.path}",
                    ""
                ])
                
                if endpoint.summary:
                    lines.append(f"**Summary**: {endpoint.summary}\n")
                
                if endpoint.description:
                    lines.append(f"**Description**: {endpoint.description}\n")
                
                if endpoint.parameters:
                    lines.append(f"**Parameters**: {', '.join(endpoint.parameters)}\n")
                
                lines.append("")
        
        return "\n".join(lines)
    
    def generate_html(self, title: str = "API Documentation") -> str:
        """Generate HTML documentation"""
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{title}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "h1 { color: #333; }",
            "h2 { color: #666; margin-top: 30px; }",
            "h3 { color: #888; }",
            ".endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-left: 4px solid #007bff; }",
            ".method { font-weight: bold; color: #007bff; }",
            ".path { font-family: monospace; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{title}</h1>"
        ]
        
        summary = self.discovery.get_endpoint_summary()
        html_parts.extend([
            f"<p>Total Routes: {summary['total_routes']}</p>",
            f"<p>Total Endpoints: {summary['total_endpoints']}</p>"
        ])
        
        for prefix, route in sorted(self.discovery.routes.items()):
            html_parts.append(f"<h2>{prefix.lstrip('/')}</h2>")
            
            if route.description:
                html_parts.append(f"<p>{route.description}</p>")
            
            for endpoint in route.endpoints:
                html_parts.extend([
                    '<div class="endpoint">',
                    f'<span class="method">{endpoint.method.upper()}</span> '
                    f'<span class="path">{endpoint.path}</span>',
                    f"<p>{endpoint.summary or endpoint.description or 'No description'}</p>",
                    "</div>"
                ])
        
        html_parts.extend([
            "</body>",
            "</html>"
        ])
        
        return "\n".join(html_parts)


# Global discovery instance
_endpoint_discovery: Optional[EndpointDiscovery] = None


def get_endpoint_discovery() -> EndpointDiscovery:
    """Get or create endpoint discovery"""
    global _endpoint_discovery
    if _endpoint_discovery is None:
        _endpoint_discovery = EndpointDiscovery()
    return _endpoint_discovery


def reset_endpoint_discovery() -> None:
    """Reset endpoint discovery (for testing)"""
    global _endpoint_discovery
    _endpoint_discovery = None
