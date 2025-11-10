"""Quick test to verify workspace name generation fix."""

import asyncio

from capabilities.base import CapabilityContext
from capabilities.databricks import DatabricksCapability


async def test_workspace_name_generation():
    """Test that workspace_name is auto-generated when not provided."""
    capability = DatabricksCapability()

    # Test case: All required params, no workspace_name
    context = CapabilityContext(
        capability_name="provision_databricks",
        user_request="I need Databricks for data analytics",
        parameters={
            "team": "data-analytics-demo1",
            "environment": "dev",
            "region": "eastus"
        }
    )

    # This should auto-generate workspace_name as "data-analytics-demo1-dev"
    infra_request = capability._build_infrastructure_request(context)

    print(f"✅ Generated workspace_name: {infra_request.workspace_name}")
    assert infra_request.workspace_name == "data-analytics-demo1-dev", \
        f"Expected 'data-analytics-demo1-dev', got '{infra_request.workspace_name}'"

    print(f"✅ Team: {infra_request.team}")
    print(f"✅ Environment: {infra_request.environment}")
    print(f"✅ Region: {infra_request.region}")
    print("\n✅ All assertions passed! Workspace name generation works correctly.")


if __name__ == "__main__":
    asyncio.run(test_workspace_name_generation())
