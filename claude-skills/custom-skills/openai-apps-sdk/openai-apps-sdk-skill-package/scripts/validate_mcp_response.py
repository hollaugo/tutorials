#!/usr/bin/env python3
"""
OpenAI Apps SDK - MCP Response Validator

Validates that MCP server tool responses conform to OpenAI Apps SDK requirements.
"""

import json
import sys
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ValidationError:
    field: str
    message: str
    severity: str  # 'error' or 'warning'


class MCPResponseValidator:
    """Validates MCP tool responses for OpenAI Apps SDK compatibility."""
    
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
    
    def validate_tool_response(self, response: Dict[str, Any]) -> bool:
        """
        Validate a complete tool response.
        
        Args:
            response: The tool response dictionary
            
        Returns:
            True if valid, False otherwise
        """
        self.errors = []
        self.warnings = []
        
        # Check top-level structure
        self._validate_content(response)
        self._validate_structured_content(response)
        self._validate_metadata(response)
        
        return len(self.errors) == 0
    
    def _validate_content(self, response: Dict[str, Any]):
        """Validate the content field (for conversation transcript)."""
        if "content" not in response:
            self.errors.append(ValidationError(
                "content",
                "Missing required 'content' field for conversation transcript",
                "error"
            ))
            return
        
        content = response["content"]
        
        if not isinstance(content, list):
            self.errors.append(ValidationError(
                "content",
                "Content must be a list",
                "error"
            ))
            return
        
        if len(content) == 0:
            self.warnings.append(ValidationError(
                "content",
                "Content list is empty - user won't see any response text",
                "warning"
            ))
        
        for i, item in enumerate(content):
            if not isinstance(item, dict):
                self.errors.append(ValidationError(
                    f"content[{i}]",
                    "Content items must be dictionaries",
                    "error"
                ))
                continue
            
            if "type" not in item:
                self.errors.append(ValidationError(
                    f"content[{i}]",
                    "Content item missing 'type' field",
                    "error"
                ))
            
            if item.get("type") == "text" and "text" not in item:
                self.errors.append(ValidationError(
                    f"content[{i}]",
                    "Text content item missing 'text' field",
                    "error"
                ))
    
    def _validate_structured_content(self, response: Dict[str, Any]):
        """Validate structured content (for model reasoning)."""
        if "structuredContent" not in response:
            self.warnings.append(ValidationError(
                "structuredContent",
                "Missing 'structuredContent' - model won't be able to reason about data",
                "warning"
            ))
            return
        
        structured = response["structuredContent"]
        
        if not isinstance(structured, dict):
            self.errors.append(ValidationError(
                "structuredContent",
                "structuredContent must be a dictionary",
                "error"
            ))
    
    def _validate_metadata(self, response: Dict[str, Any]):
        """Validate _meta field for widget rendering."""
        if "_meta" not in response:
            self.warnings.append(ValidationError(
                "_meta",
                "Missing '_meta' field - no widget will be rendered",
                "warning"
            ))
            return
        
        meta = response["_meta"]
        
        if not isinstance(meta, dict):
            self.errors.append(ValidationError(
                "_meta",
                "_meta must be a dictionary",
                "error"
            ))
            return
        
        # Check for output template
        if "openai/outputTemplate" not in meta:
            self.warnings.append(ValidationError(
                "_meta",
                "Missing '_meta[\"openai/outputTemplate\"]' - no widget will be rendered",
                "warning"
            ))
        else:
            template = meta["openai/outputTemplate"]
            if not template.startswith("ui://widget/"):
                self.errors.append(ValidationError(
                    "_meta.openai/outputTemplate",
                    f"Output template must start with 'ui://widget/', got: {template}",
                    "error"
                ))
            if not template.endswith(".html"):
                self.warnings.append(ValidationError(
                    "_meta.openai/outputTemplate",
                    f"Output template should end with '.html', got: {template}",
                    "warning"
                ))
    
    def validate_resource_response(self, response: Dict[str, Any]) -> bool:
        """
        Validate a resource (widget template) response.
        
        Args:
            response: The resource response dictionary
            
        Returns:
            True if valid, False otherwise
        """
        self.errors = []
        self.warnings = []
        
        if "contents" not in response:
            self.errors.append(ValidationError(
                "contents",
                "Resource response missing 'contents' field",
                "error"
            ))
            return False
        
        contents = response["contents"]
        
        if not isinstance(contents, list):
            self.errors.append(ValidationError(
                "contents",
                "Resource contents must be a list",
                "error"
            ))
            return False
        
        if len(contents) == 0:
            self.errors.append(ValidationError(
                "contents",
                "Resource contents list is empty",
                "error"
            ))
            return False
        
        for i, content in enumerate(contents):
            self._validate_resource_content(content, i)
        
        return len(self.errors) == 0
    
    def _validate_resource_content(self, content: Dict[str, Any], index: int):
        """Validate individual resource content item."""
        required_fields = ["uri", "mimeType", "text"]
        
        for field in required_fields:
            if field not in content:
                self.errors.append(ValidationError(
                    f"contents[{index}].{field}",
                    f"Missing required field '{field}'",
                    "error"
                ))
        
        # Validate MIME type - CRITICAL for OpenAI Apps SDK
        mime_type = content.get("mimeType", "")
        if mime_type != "text/html+skybridge":
            self.errors.append(ValidationError(
                f"contents[{index}].mimeType",
                f"MIME type must be 'text/html+skybridge', got: '{mime_type}'",
                "error"
            ))
        
        # Validate URI format
        uri = content.get("uri", "")
        if not uri.startswith("ui://widget/"):
            self.errors.append(ValidationError(
                f"contents[{index}].uri",
                f"URI must start with 'ui://widget/', got: {uri}",
                "error"
            ))
        
        # Check for widget metadata
        if "_meta" in content:
            meta = content["_meta"]
            
            # Widget description helps the model understand what's displayed
            if "openai/widgetDescription" not in meta:
                self.warnings.append(ValidationError(
                    f"contents[{index}]._meta",
                    "Missing 'openai/widgetDescription' - helps model understand the widget",
                    "warning"
                ))
    
    def print_results(self):
        """Print validation results in a readable format."""
        if not self.errors and not self.warnings:
            print("✅ Validation passed! No issues found.")
            return
        
        if self.errors:
            print(f"\n❌ Found {len(self.errors)} error(s):\n")
            for error in self.errors:
                print(f"  ERROR: {error.field}")
                print(f"    {error.message}\n")
        
        if self.warnings:
            print(f"\n⚠️  Found {len(self.warnings)} warning(s):\n")
            for warning in self.warnings:
                print(f"  WARNING: {warning.field}")
                print(f"    {warning.message}\n")
        
        if self.errors:
            print("\n❌ Validation failed. Please fix the errors above.")
        else:
            print("\n✅ Validation passed with warnings. Consider addressing them.")


def main():
    """Main entry point for the validator."""
    if len(sys.argv) < 2:
        print("Usage: python validate_mcp_response.py <json_file> [--type=tool|resource]")
        print("\nExamples:")
        print("  python validate_mcp_response.py tool_response.json")
        print("  python validate_mcp_response.py resource_response.json --type=resource")
        sys.exit(1)
    
    filename = sys.argv[1]
    response_type = "tool"  # default
    
    # Check for type flag
    for arg in sys.argv[2:]:
        if arg.startswith("--type="):
            response_type = arg.split("=")[1]
    
    try:
        with open(filename, 'r') as f:
            response = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File '{filename}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{filename}'")
        print(f"   {str(e)}")
        sys.exit(1)
    
    validator = MCPResponseValidator()
    
    print(f"\n🔍 Validating {response_type} response from: {filename}\n")
    
    if response_type == "tool":
        is_valid = validator.validate_tool_response(response)
    elif response_type == "resource":
        is_valid = validator.validate_resource_response(response)
    else:
        print(f"❌ Error: Invalid type '{response_type}'. Use 'tool' or 'resource'")
        sys.exit(1)
    
    validator.print_results()
    
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
