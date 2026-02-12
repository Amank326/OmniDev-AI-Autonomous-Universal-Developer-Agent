"""
Phase 55: Migration Helpers
Automatic request/response transformation between versions,
migration guides generation, and schema mapping utilities.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
import json
from datetime import datetime


class TransformationType(Enum):
    """Type of transformation operation."""
    RENAME_FIELD = "rename_field"
    REMOVE_FIELD = "remove_field"
    ADD_FIELD = "add_field"
    TYPE_CONVERT = "type_convert"
    NEST_FIELD = "nest_field"
    FLATTEN_FIELD = "flatten_field"
    MAP_ENUM = "map_enum"
    MERGE_FIELDS = "merge_fields"
    SPLIT_FIELD = "split_field"


class MigrationStrategy(Enum):
    """Migration strategy for handling versions."""
    AUTOMATIC = "automatic"  # Automatically transform
    MANUAL = "manual"  # Requires manual intervention
    DEPRECATED = "deprecated"  # Will be removed


class FieldMapping:
    """Maps a field from one version to another."""

    def __init__(
        self,
        from_path: str,
        to_path: str,
        transformation_type: TransformationType,
        transformer: Optional[Callable[[Any], Any]] = None,
        description: str = ""
    ):
        """Initialize field mapping."""
        self.from_path = from_path
        self.to_path = to_path
        self.transformation_type = transformation_type
        self.transformer = transformer
        self.description = description

    def apply(self, source_value: Any) -> Any:
        """Apply transformation to value."""
        if self.transformer:
            return self.transformer(source_value)
        return source_value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'from_path': self.from_path,
            'to_path': self.to_path,
            'transformation_type': self.transformation_type.value,
            'description': self.description
        }


@dataclass
class VersionMapping:
    """Mapping between two API versions."""
    from_version: str
    to_version: str
    direction: str  # 'forward' or 'backward'
    request_mappings: List[FieldMapping] = field(default_factory=list)
    response_mappings: List[FieldMapping] = field(default_factory=list)
    strategy: MigrationStrategy = MigrationStrategy.AUTOMATIC
    migration_notes: str = ""
    auto_migration_available: bool = True

    def add_request_mapping(self, mapping: FieldMapping) -> 'VersionMapping':
        """Add request field mapping."""
        self.request_mappings.append(mapping)
        return self

    def add_response_mapping(self, mapping: FieldMapping) -> 'VersionMapping':
        """Add response field mapping."""
        self.response_mappings.append(mapping)
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'from_version': self.from_version,
            'to_version': self.to_version,
            'direction': self.direction,
            'strategy': self.strategy.value,
            'request_mappings': len(self.request_mappings),
            'response_mappings': len(self.response_mappings),
            'auto_migration_available': self.auto_migration_available
        }


class FieldTransformer:
    """Transforms fields between versions."""

    @staticmethod
    def get_nested_value(obj: Dict[str, Any], path: str) -> Any:
        """Get value from nested object using dot notation."""
        parts = path.split('.')
        current = obj
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    @staticmethod
    def set_nested_value(obj: Dict[str, Any], path: str, value: Any) -> Dict[str, Any]:
        """Set value in nested object using dot notation."""
        parts = path.split('.')
        current = obj
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
        return obj

    @staticmethod
    def rename_field(data: Dict[str, Any], old_path: str, new_path: str) -> Dict[str, Any]:
        """Rename a field."""
        value = FieldTransformer.get_nested_value(data, old_path)
        if value is not None:
            FieldTransformer.set_nested_value(data, new_path, value)
            # Remove old field
            old_parts = old_path.split('.')
            current = data
            for part in old_parts[:-1]:
                if part in current:
                    current = current[part]
                else:
                    return data
            if old_parts[-1] in current:
                del current[old_parts[-1]]
        return data

    @staticmethod
    def remove_field(data: Dict[str, Any], path: str) -> Dict[str, Any]:
        """Remove a field."""
        parts = path.split('.')
        current = data
        for part in parts[:-1]:
            if part in current:
                current = current[part]
            else:
                return data
        if parts[-1] in current:
            del current[parts[-1]]
        return data

    @staticmethod
    def add_field(data: Dict[str, Any], path: str, value: Any) -> Dict[str, Any]:
        """Add a new field."""
        return FieldTransformer.set_nested_value(data, path, value)

    @staticmethod
    def convert_type(value: Any, target_type: str) -> Any:
        """Convert value to target type."""
        if value is None:
            return None
        
        if target_type == 'int':
            return int(value)
        elif target_type == 'float':
            return float(value)
        elif target_type == 'str':
            return str(value)
        elif target_type == 'bool':
            return bool(value)
        elif target_type == 'list':
            return list(value) if isinstance(value, (list, tuple)) else [value]
        elif target_type == 'dict':
            return dict(value) if isinstance(value, dict) else {}
        else:
            return value


@dataclass
class MigrationGuide:
    """Guide for migrating between versions."""
    from_version: str
    to_version: str
    title: str
    description: str
    steps: List[Dict[str, str]] = field(default_factory=list)
    code_examples: List[Dict[str, str]] = field(default_factory=list)
    common_issues: List[Dict[str, str]] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    estimated_migration_time_hours: int = 1
    difficulty_level: str = "easy"  # easy, medium, hard
    breaking_changes: List[str] = field(default_factory=list)

    def add_step(self, step_title: str, step_description: str, code_snippet: str = "") -> 'MigrationGuide':
        """Add a migration step."""
        self.steps.append({
            'title': step_title,
            'description': step_description,
            'code': code_snippet
        })
        return self

    def add_example(self, title: str, old_code: str, new_code: str) -> 'MigrationGuide':
        """Add code example."""
        self.code_examples.append({
            'title': title,
            'old': old_code,
            'new': new_code
        })
        return self

    def add_common_issue(self, issue: str, solution: str) -> 'MigrationGuide':
        """Add common issue."""
        self.common_issues.append({
            'issue': issue,
            'solution': solution
        })
        return self

    def to_html(self) -> str:
        """Generate HTML migration guide."""
        html = f"""
        <div class="migration-guide">
            <h1>{self.title}</h1>
            <p>{self.description}</p>
            
            <div class="difficulty">
                <strong>Difficulty:</strong> {self.difficulty_level}
            </div>
            
            <div class="estimated-time">
                <strong>Estimated Time:</strong> {self.estimated_migration_time_hours} hours
            </div>
            
            <h2>Breaking Changes</h2>
            <ul>
        """
        
        for change in self.breaking_changes:
            html += f"<li>{change}</li>"
        
        html += """
            </ul>
            
            <h2>Migration Steps</h2>
            <ol>
        """
        
        for i, step in enumerate(self.steps, 1):
            html += f"""
            <li>
                <h3>{step['title']}</h3>
                <p>{step['description']}</p>
            """
            if step.get('code'):
                html += f"<pre><code>{step['code']}</code></pre>"
            html += "</li>"
        
        html += """
            </ol>
            
            <h2>Code Examples</h2>
        """
        
        for example in self.code_examples:
            html += f"""
            <div class="code-example">
                <h3>{example['title']}</h3>
                <div class="old-code">
                    <p><strong>Before (v{self.from_version}):</strong></p>
                    <pre><code>{example['old']}</code></pre>
                </div>
                <div class="new-code">
                    <p><strong>After (v{self.to_version}):</strong></p>
                    <pre><code>{example['new']}</code></pre>
                </div>
            </div>
            """
        
        html += """
            <h2>Common Issues</h2>
            <ul>
        """
        
        for issue in self.common_issues:
            html += f"""
            <li>
                <strong>{issue['issue']}</strong><br>
                <em>Solution: {issue['solution']}</em>
            </li>
            """
        
        html += """
            </ul>
        </div>
        """
        
        return html

    def to_markdown(self) -> str:
        """Generate Markdown migration guide."""
        md = f"""# Migration Guide: v{self.from_version} → v{self.to_version}

## {self.title}

{self.description}

**Difficulty:** {self.difficulty_level}  
**Estimated Time:** {self.estimated_migration_time_hours} hours

## Breaking Changes

"""
        
        for change in self.breaking_changes:
            md += f"- {change}\n"
        
        md += "\n## Migration Steps\n\n"
        
        for i, step in enumerate(self.steps, 1):
            md += f"### {i}. {step['title']}\n\n{step['description']}\n\n"
            if step.get('code'):
                md += f"```\n{step['code']}\n```\n\n"
        
        md += "## Code Examples\n\n"
        
        for example in self.code_examples:
            md += f"### {example['title']}\n\n"
            md += f"**Before (v{self.from_version}):**\n```\n{example['old']}\n```\n\n"
            md += f"**After (v{self.to_version}):**\n```\n{example['new']}\n```\n\n"
        
        md += "## Common Issues & Solutions\n\n"
        
        for issue in self.common_issues:
            md += f"**Q: {issue['issue']}**  \n"
            md += f"A: {issue['solution']}\n\n"
        
        return md

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'from_version': self.from_version,
            'to_version': self.to_version,
            'title': self.title,
            'description': self.description,
            'steps': self.steps,
            'code_examples': self.code_examples,
            'common_issues': self.common_issues,
            'breaking_changes': self.breaking_changes,
            'estimated_migration_time_hours': self.estimated_migration_time_hours,
            'difficulty_level': self.difficulty_level
        }


class RequestTransformer:
    """Transforms request objects between versions."""

    def __init__(self, mapping: VersionMapping):
        """Initialize request transformer."""
        self.mapping = mapping

    def transform(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform request from source to target version."""
        result = {}
        
        for field_map in self.mapping.request_mappings:
            value = FieldTransformer.get_nested_value(request_data, field_map.from_path)
            
            if value is not None:
                transformed_value = field_map.apply(value)
                FieldTransformer.set_nested_value(result, field_map.to_path, transformed_value)
        
        # Add fields not in mapping
        for key, value in request_data.items():
            if key not in [m.from_path.split('.')[0] for m in self.mapping.request_mappings]:
                result[key] = value
        
        return result


class ResponseTransformer:
    """Transforms response objects between versions."""

    def __init__(self, mapping: VersionMapping):
        """Initialize response transformer."""
        self.mapping = mapping

    def transform(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform response from source to target version."""
        result = {}
        
        for field_map in self.mapping.response_mappings:
            value = FieldTransformer.get_nested_value(response_data, field_map.from_path)
            
            if value is not None:
                transformed_value = field_map.apply(value)
                FieldTransformer.set_nested_value(result, field_map.to_path, transformed_value)
        
        # Add fields not in mapping
        for key, value in response_data.items():
            if key not in [m.from_path.split('.')[0] for m in self.mapping.response_mappings]:
                result[key] = value
        
        return result


class MigrationHelper:
    """Helps with API version migrations."""

    def __init__(self):
        """Initialize migration helper."""
        self.version_mappings: Dict[str, VersionMapping] = {}
        self.migration_guides: Dict[str, MigrationGuide] = {}

    def register_mapping(self, mapping: VersionMapping) -> 'MigrationHelper':
        """Register a version mapping."""
        key = f"{mapping.from_version}->{mapping.to_version}"
        self.version_mappings[key] = mapping
        return self

    def register_guide(self, guide: MigrationGuide) -> 'MigrationHelper':
        """Register a migration guide."""
        key = f"{guide.from_version}->{guide.to_version}"
        self.migration_guides[key] = guide
        return self

    def get_mapping(self, from_version: str, to_version: str) -> Optional[VersionMapping]:
        """Get mapping between versions."""
        key = f"{from_version}->{to_version}"
        return self.version_mappings.get(key)

    def get_guide(self, from_version: str, to_version: str) -> Optional[MigrationGuide]:
        """Get migration guide."""
        key = f"{from_version}->{to_version}"
        return self.migration_guides.get(key)

    def transform_request(
        self,
        request_data: Dict[str, Any],
        from_version: str,
        to_version: str
    ) -> Optional[Dict[str, Any]]:
        """Transform request between versions."""
        mapping = self.get_mapping(from_version, to_version)
        if not mapping:
            return None
        
        transformer = RequestTransformer(mapping)
        return transformer.transform(request_data)

    def transform_response(
        self,
        response_data: Dict[str, Any],
        from_version: str,
        to_version: str
    ) -> Optional[Dict[str, Any]]:
        """Transform response between versions."""
        mapping = self.get_mapping(from_version, to_version)
        if not mapping:
            return None
        
        transformer = ResponseTransformer(mapping)
        return transformer.transform(response_data)

    def get_all_guides(self) -> List[MigrationGuide]:
        """Get all migration guides."""
        return list(self.migration_guides.values())

    def get_all_mappings(self) -> List[VersionMapping]:
        """Get all version mappings."""
        return list(self.version_mappings.values())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'version_mappings': len(self.version_mappings),
            'migration_guides': len(self.migration_guides),
            'mappings': [m.to_dict() for m in self.get_all_mappings()],
            'guides': [g.to_dict() for g in self.get_all_guides()]
        }


# Singleton instance
_migration_helper: Optional[MigrationHelper] = None


def get_migration_helper() -> MigrationHelper:
    """Get the migration helper singleton."""
    global _migration_helper
    if _migration_helper is None:
        _migration_helper = MigrationHelper()
    return _migration_helper


def reset_migration_helper() -> None:
    """Reset the migration helper (for testing)."""
    global _migration_helper
    _migration_helper = None
