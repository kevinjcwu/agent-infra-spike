"""
Capability Registry for Infrastructure Provisioning.

Maintains the source of truth for all available infrastructure capabilities.
Prevents LLM hallucination by providing a validated list of supported capabilities.

Usage:
    from orchestrator.capability_registry import capability_registry

    # Get valid capability names
    valid = capability_registry.get_valid_capability_names()

    # Get capability info
    info = capability_registry.get_capability_info("provision_databricks")
"""


class CapabilityRegistry:
    """
    Registry of all supported infrastructure capabilities.

    Each capability represents a distinct infrastructure provisioning action
    that the system can perform. This serves as the source of truth to prevent
    LLM hallucination of unsupported capabilities.
    """

    def __init__(self):
        """Initialize registry with supported capabilities."""
        self.capabilities = {
            "provision_databricks": {
                "name": "provision_databricks",
                "display_name": "Azure Databricks Workspace",
                "description": "Provision Azure Databricks workspace for data engineering, ML, and analytics",
                "keywords": [
                    "databricks",
                    "workspace",
                    "spark",
                    "ml platform",
                    "machine learning",
                    "data engineering",
                    "analytics",
                    "jupyter",
                    "notebooks",
                ],
                "use_cases": [
                    "Data engineering pipelines",
                    "ML model training and experimentation",
                    "Large-scale data analytics",
                    "Spark workloads",
                    "Collaborative data science",
                ],
                "category": "compute",
            },
            # Future capabilities (not yet implemented):
            # "provision_openai": { ... }
            # "configure_firewall": { ... }
        }

    def get_valid_capability_names(self) -> list[str]:
        """
        Get list of all valid capability identifiers.

        Returns:
            List of capability names that can be provisioned
        """
        return list(self.capabilities.keys())

    def get_capability_info(self, capability_name: str) -> dict | None:
        """
        Get detailed information about a specific capability.

        Args:
            capability_name: The capability identifier

        Returns:
            Capability info dict or None if not found
        """
        return self.capabilities.get(capability_name)

    def validate_capability(self, capability_name: str) -> tuple[bool, str]:
        """
        Validate if a capability name is supported.

        Args:
            capability_name: The capability to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if capability_name in self.capabilities:
            return True, ""

        valid_names = self.get_valid_capability_names()
        return False, f"Unknown capability '{capability_name}'. Valid options: {valid_names}"

    def get_capabilities_description(self) -> str:
        """
        Generate formatted description of all capabilities for system prompts.

        Returns:
            Multi-line string describing all capabilities
        """
        descriptions = []

        for name, info in self.capabilities.items():
            use_cases = "\n  ".join(f"• {uc}" for uc in info["use_cases"])

            description = f"""
**{info['display_name']}** (`{name}`)
{info['description']}

Use cases:
  {use_cases}
""".strip()

            descriptions.append(description)

        return "\n\n".join(descriptions)

    def get_capabilities_for_prompt(self) -> str:
        """
        Generate concise capability list for system prompt.

        Returns:
            Formatted string listing capabilities with descriptions
        """
        lines = []
        for name, info in self.capabilities.items():
            lines.append(f"- `{name}`: {info['description']}")
        return "\n".join(lines)

    def search_by_keywords(self, query: str) -> list[str]:
        """
        Search capabilities by keyword matching (for fallback/testing).

        This is a simple keyword-based search. The LLM should handle
        semantic understanding, but this can be used for validation.

        Args:
            query: Search query

        Returns:
            List of matching capability names
        """
        query_lower = query.lower()
        matches = []

        for name, info in self.capabilities.items():
            # Check if any keyword appears in query
            if any(keyword in query_lower for keyword in info["keywords"]):
                matches.append(name)

        return matches

    def get_categories(self) -> dict[str, list[str]]:
        """
        Get capabilities grouped by category.

        Returns:
            Dict mapping category names to capability names
        """
        categories = {}

        for name, info in self.capabilities.items():
            category = info.get("category", "other")
            if category not in categories:
                categories[category] = []
            categories[category].append(name)

        return categories


# Global singleton instance
capability_registry = CapabilityRegistry()
