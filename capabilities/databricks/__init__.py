"""Databricks provisioning capability.

Provides infrastructure provisioning for Azure Databricks workspaces and clusters.

Organized in three layers:
- core/: Business logic (intent parsing, decision making, configuration)
- models/: Data structures (requests, decisions, results)
- provisioning/: Infrastructure deployment (Terraform generation and execution)
"""

from .capability import DatabricksCapability

# Core business logic
from .core.config import Config
from .core.decision_maker import DecisionMaker
from .core.intent_parser import IntentParser

# Data models
from .models.schemas import (
    DeploymentResult,
    InfrastructureDecision,
    InfrastructureRequest,
    TerraformFiles,
)

# Provisioning layer
from .provisioning.terraform.executor import TerraformExecutor
from .provisioning.terraform.generator import TerraformGenerator

__all__ = [
    # Main capability
    "DatabricksCapability",
    # Core
    "Config",
    "DecisionMaker",
    "IntentParser",
    # Models
    "DeploymentResult",
    "InfrastructureDecision",
    "InfrastructureRequest",
    "TerraformFiles",
    # Provisioning
    "TerraformExecutor",
    "TerraformGenerator",
]
