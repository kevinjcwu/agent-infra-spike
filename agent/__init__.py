"""
AI Agent for Databricks Infrastructure Provisioning.

This package provides an LLM-powered agent that automates Databricks workspace
provisioning in Azure using Terraform.

NOTE: This is now a thin compatibility layer. The actual implementation has moved
to capabilities.databricks.
For maximum compatibility, import from capabilities.databricks directly in new code.
"""

__version__ = "0.1.0"

# Only export InfrastructureAgent (the thin wrapper)
# For other classes, import directly from capabilities.databricks
from .infrastructure_agent import InfrastructureAgent

__all__ = [
    "InfrastructureAgent",
]
