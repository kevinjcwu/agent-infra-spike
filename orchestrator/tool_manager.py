"""
Tool Registry for Dynamic Tool Management.

Provides decorator-based tool registration with auto-schema generation
from Python type hints. Eliminates hardcoded if/elif dispatch chains.

Usage:
    @tool_manager.register("Tool description")
    def my_tool(param: str) -> str:
        return json.dumps(result)

The tool is automatically:
- Registered in the global registry
- Schema generated from type hints
- Available for dynamic execution
"""

import inspect
from collections.abc import Callable
from typing import Any, get_args, get_origin


class ToolManager:
    """
    Manages tool registration and provides schemas for MAF agents.

    Supports two registration methods:
    1. Decorator: @tool_manager.register("description")
    2. Method: tool_manager.register_tool(func, "description")

    Auto-generates OpenAI-compatible function schemas from type hints.
    """

    def __init__(self):
        self.tools: dict[str, Callable] = {}  # name -> function
        self.tool_schemas: list[dict[str, Any]] = []  # OpenAI function schemas
        self.descriptions: dict[str, str] = {}  # name -> description
        self.orchestrator: Any = None  # Will be set by orchestrator on init

    def register(self, description: str) -> Callable:
        """
        Decorator to register a tool with auto-generated schema.

        Args:
            description: Human-readable description of what the tool does

        Returns:
            Decorator function

        Example:
            @tool_manager.register("Estimate infrastructure costs")
            def estimate_cost(capability: str, config: dict) -> str:
                return json.dumps({"cost": 1000})
        """

        def decorator(func: Callable) -> Callable:
            tool_name = func.__name__
            self.tools[tool_name] = func
            self.descriptions[tool_name] = description

            # Generate OpenAI function schema from Python signature
            schema = self._generate_schema(func, description)
            self.tool_schemas.append(schema)

            return func

        return decorator

    def _generate_schema(self, func: Callable, description: str) -> dict[str, Any]:
        """
        Auto-generate OpenAI function schema from Python function signature.

        Uses inspect to extract parameter names, types, and defaults,
        then converts to JSON Schema format.

        Args:
            func: The Python function to generate schema for
            description: Human-readable description

        Returns:
            OpenAI function schema dict
        """
        sig = inspect.signature(func)
        parameters = {
            "type": "object",
            "properties": {},
            "required": [],
        }

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            # Extract type hint
            param_type = param.annotation
            if param_type == inspect.Parameter.empty:
                # No type hint - default to string
                json_type = "string"
            else:
                json_type = self._python_type_to_json_type(param_type)

            parameters["properties"][param_name] = {"type": json_type}

            # Mark as required if no default value
            if param.default == inspect.Parameter.empty:
                parameters["required"].append(param_name)

        return {
            "name": func.__name__,
            "description": description,
            "parameters": parameters,
        }

    def _python_type_to_json_type(self, python_type) -> str:
        """
        Convert Python type hints to JSON Schema types.

        Args:
            python_type: Python type annotation

        Returns:
            JSON Schema type string
        """
        # Handle Optional types (Union[X, None])
        origin = get_origin(python_type)
        if origin is not None:
            args = get_args(python_type)
            # For Optional[X], use X's type
            if len(args) == 2 and type(None) in args:
                # Get the non-None type
                non_none_type = args[0] if args[1] is type(None) else args[1]
                return self._python_type_to_json_type(non_none_type)

        # Direct type mappings
        if python_type is str:
            return "string"
        elif python_type is int:
            return "integer"
        elif python_type is float:
            return "number"
        elif python_type is bool:
            return "boolean"
        elif python_type is dict:
            return "object"
        elif python_type is list:
            return "array"
        else:
            # Default to string for unknown types
            return "string"  # Default fallback

    def execute(self, tool_name: str, **kwargs) -> str:
        """
        Execute a registered tool by name with dynamic dispatch.

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Arguments to pass to the tool

        Returns:
            Tool execution result (typically JSON string)

        Raises:
            ValueError: If tool not found
        """
        if tool_name not in self.tools:
            raise ValueError(
                f"Tool '{tool_name}' not found. Available: {list(self.tools.keys())}"
            )

        tool_func = self.tools[tool_name]
        return tool_func(**kwargs)

    def get_schemas(self, wrapped: bool = True) -> list[dict[str, Any]]:
        """
        Get all registered tool schemas for MAF agent creation.

        Args:
            wrapped: If True, wrap each schema with {"type": "function", "function": schema}
                    as required by OpenAI/MAF tools parameter

        Returns:
            List of OpenAI function schema dicts
        """
        if wrapped:
            # Wrap schemas for OpenAI tools format
            return [
                {
                    "type": "function",
                    "function": schema
                }
                for schema in self.tool_schemas
            ]
        return self.tool_schemas

    def get_tool_functions(self) -> list[Callable]:
        """
        Get all registered tool functions for MAF agent creation.

        MAF expects actual Python functions (not schemas) and will handle
        schema generation and tool calling automatically.

        Returns:
            List of tool function callables
        """
        return list(self.tools.values())

    def list_tools(self) -> list[str]:
        """
        Get list of all registered tool names.

        Returns:
            List of tool names
        """
        return list(self.tools.keys())

    def get_tool_info(self, tool_name: str) -> dict[str, Any]:
        """
        Get detailed information about a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Dict with tool metadata

        Raises:
            ValueError: If tool not found
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")

        return {
            "name": tool_name,
            "description": self.descriptions.get(tool_name, ""),
            "function": self.tools[tool_name],
            "schema": next(
                (s for s in self.tool_schemas if s["name"] == tool_name), None
            ),
        }


# Global singleton instance
tool_manager = ToolManager()
