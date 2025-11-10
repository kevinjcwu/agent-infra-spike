"""Example: How to add Azure OpenAI capability (post-refactoring).

This demonstrates how the refactoring enables adding new capabilities
without modifying orchestrator core code.
"""

from typing import Any

from capabilities.base import (
    BaseCapability,
    CapabilityContext,
    CapabilityPlan,
    CapabilityResult,
)


class OpenAICapability(BaseCapability):
    """Provision Azure OpenAI service.

    This is a TEMPLATE showing how easy it is to add new capabilities
    after the refactoring. No orchestrator changes needed!
    """

    @property
    def name(self) -> str:
        """Capability identifier."""
        return "provision_openai"

    @property
    def description(self) -> str:
        """Human-readable description."""
        return "Provision Azure OpenAI service with GPT-4 deployment"

    def get_required_parameters(self) -> list[str]:
        """OpenAI-specific required parameters.

        Notice: These are COMPLETELY DIFFERENT from Databricks parameters.
        The orchestrator doesn't care - it just passes them through!
        """
        return ["deployment_name", "region", "sku"]

    def get_optional_parameters(self) -> dict[str, Any]:
        """OpenAI-specific optional parameters with defaults."""
        return {
            "capacity": 10,
            "model_version": "2024-02-15-preview",
            "content_filter": "default",
            "rate_limit": 100000,  # tokens per minute
        }

    async def plan(self, context: CapabilityContext) -> CapabilityPlan:
        """Generate OpenAI deployment plan.

        Notice: Completely different logic from Databricks.
        We extract OUR parameters (deployment_name, sku, etc.)
        without the orchestrator knowing about them.
        """
        params = context.parameters

        # Extract OpenAI-specific parameters
        deployment_name = params.get("deployment_name")
        region = params.get("region", "eastus")
        sku = params.get("sku", "S0")
        capacity = params.get("capacity", 10)

        # Calculate OpenAI-specific costs (different from Databricks!)
        monthly_cost = self._estimate_openai_cost(sku, capacity)

        return CapabilityPlan(
            capability_name=self.name,
            description=f"Provision Azure OpenAI '{deployment_name}' in {region}",
            resources=[
                {"type": "Azure OpenAI Service", "name": deployment_name},
                {"type": "GPT-4 Deployment", "name": f"{deployment_name}-gpt4"},
            ],
            estimated_cost=monthly_cost,
            estimated_duration=5,  # OpenAI deploys faster than Databricks
            requires_approval=True,
            details={
                "sku": sku,
                "capacity": capacity,
                "model": "gpt-4",
                # Would include terraform plan, etc.
            }
        )

    async def execute(self, plan: CapabilityPlan) -> CapabilityResult:
        """Execute OpenAI deployment.

        Would use Azure SDK or Terraform to actually provision OpenAI.
        """
        # Placeholder - would call Azure OpenAI provisioning API
        return CapabilityResult(
            capability_name=self.name,
            success=True,
            message="Azure OpenAI service provisioned successfully",
            resources_created=[
                {"type": "Azure OpenAI Service", "name": plan.details.get("deployment_name")},
            ],
            outputs={
                "endpoint": f"https://{plan.details.get('deployment_name')}.openai.azure.com",
                "api_key": "<would be fetched from Azure>",
                "model": "gpt-4",
            },
            duration_seconds=120.0
        )

    def _estimate_openai_cost(self, sku: str, capacity: int) -> float:
        """Estimate monthly OpenAI costs.

        Completely different pricing model from Databricks!
        """
        # OpenAI pricing (example)
        base_costs = {
            "S0": 200.0,   # Standard tier
            "S1": 500.0,   # Premium tier
        }

        base = base_costs.get(sku, 200.0)
        return base + (capacity * 20.0)  # $20 per capacity unit


# ==============================================================================
# HOW TO INTEGRATE (3 simple steps):
# ==============================================================================
#
# 1. Add to orchestrator/_register_capabilities():
#    from capabilities.openai import OpenAICapability
#    self.capabilities["provision_openai"] = OpenAICapability()
#
# 2. Add to orchestrator/capability_registry.py:
#    capability_registry.register(
#        name="provision_openai",
#        display_name="Azure OpenAI Service",
#        description="Provision Azure OpenAI with GPT-4 deployments",
#        tags=["azure", "ai", "openai"],
#        required_params=["deployment_name", "region", "sku"],
#        optional_params=["capacity", "model_version"]
#    )
#
# 3. DONE! The orchestrator will:
#    ✅ Discover the capability via registry
#    ✅ Route requests to it
#    ✅ Pass through parameters (deployment_name, sku, etc.)
#    ✅ Handle approval workflow
#    ✅ Execute deployment
#
# NO CHANGES TO:
# ❌ orchestrator/models.py
# ❌ orchestrator/tools.py
# ❌ orchestrator/orchestrator_agent.py (except 1-line registration)
# ==============================================================================

"""
EXAMPLE CONVERSATION (after adding OpenAI capability):

User: "I need Azure OpenAI for my chatbot"

Orchestrator:
  - Calls select_capabilities(["provision_openai"])
  - Asks: deployment name? region? SKU tier?

User: "name: chatbot-prod, region: eastus, SKU: S0"

Orchestrator:
  - Calls suggest_naming(...)
  - Calls estimate_cost(
        capability="provision_openai",
        parameters={
            "deployment_name": "chatbot-prod",
            "region": "eastus",
            "sku": "S0",
            "capacity": 10
        }
    )
  - Presents plan

User: "yes, deploy it"

Orchestrator:
  - Calls execute_deployment(
        capability_name="provision_openai",
        parameters={
            "deployment_name": "chatbot-prod",
            "region": "eastus",
            "sku": "S0",
            "capacity": 10
        }
    )
  - OpenAICapability.execute() provisions the service
  - Returns deployment results

THAT'S IT! The orchestrator doesn't know or care about OpenAI-specific params.
It just passes them through as an opaque dict.
"""
