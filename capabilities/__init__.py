"""Infrastructure provisioning capabilities.

This package contains all infrastructure provisioning capabilities.
Each capability is a pluggable module that can provision specific infrastructure.

Structure:
    capabilities/
        base.py - BaseCapability interface and data models
        databricks/ - Databricks workspace provisioning
        [future: openai/, firewall/, etc.]
"""

from capabilities.base import (
    BaseCapability,
    CapabilityContext,
    CapabilityPlan,
    CapabilityResult,
)

__all__ = [
    "BaseCapability",
    "CapabilityContext",
    "CapabilityPlan",
    "CapabilityResult",
]
