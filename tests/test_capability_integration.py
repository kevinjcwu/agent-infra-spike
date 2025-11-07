"""Tests for Phase 2: Capability Integration.

Tests the integration between orchestrator and capability execution.
"""

import pytest

from capabilities import CapabilityContext
from capabilities.databricks import DatabricksCapability
from orchestrator.orchestrator_agent import InfrastructureOrchestrator


def test_databricks_capability_registration():
    """Test that Databricks capability is properly registered."""
    orchestrator = InfrastructureOrchestrator()

    # Check capability is registered
    assert "provision_databricks" in orchestrator.list_capabilities()

    # Check capability can be retrieved
    capability = orchestrator.get_capability("provision_databricks")
    assert capability is not None
    assert isinstance(capability, DatabricksCapability)
    assert capability.name == "provision_databricks"


def test_databricks_capability_properties():
    """Test Databricks capability properties."""
    capability = DatabricksCapability()

    assert capability.name == "provision_databricks"
    assert "Databricks" in capability.description
    assert len(capability.description) > 0


@pytest.mark.asyncio
async def test_databricks_capability_plan_generation():
    """Test that Databricks capability can generate an execution plan."""
    capability = DatabricksCapability()

    # Create test context
    context = CapabilityContext(
        user_request="I need a Databricks workspace for the ML team in production",
        capability_name="provision_databricks",
        parameters={
            "team": "ml-team",
            "environment": "prod",
            "region": "eastus",
        }
    )

    # Generate plan
    plan = await capability.plan(context)

    # Validate plan structure
    assert plan.capability_name == "provision_databricks"
    assert len(plan.description) > 0
    assert len(plan.resources) > 0
    assert plan.estimated_cost is not None
    assert plan.estimated_cost > 0
    assert plan.estimated_duration is not None
    assert plan.requires_approval is True

    # Check resources include expected types
    resource_types = [r["type"] for r in plan.resources]
    assert "Resource Group" in resource_types
    assert "Databricks Workspace" in resource_types

    # Check plan has terraform details
    assert "decision" in plan.details
    assert "terraform_files" in plan.details
    assert "terraform_plan" in plan.details


@pytest.mark.asyncio
async def test_databricks_capability_validation():
    """Test Databricks capability validation."""
    capability = DatabricksCapability()

    # Create valid context
    context = CapabilityContext(
        user_request="Provision Databricks workspace",
        capability_name="provision_databricks",
        parameters={
            "team": "data-science",
            "environment": "dev",
        }
    )

    # Validate
    is_valid, errors = await capability.validate(context)

    # Should be valid (current implementation has minimal validation)
    assert is_valid is True
    assert len(errors) == 0


@pytest.mark.asyncio
async def test_orchestrator_capability_execution_flow():
    """Test orchestrator can execute capability flow (plan only, no actual deployment).

    Note: This test generates a plan but does NOT execute deployment
    to avoid actually creating Azure resources in test environment.
    """
    orchestrator = InfrastructureOrchestrator()

    # Test parameters from conversation
    parameters = {
        "team": "test-team",
        "environment": "dev",
        "region": "eastus",
        "workspace_name": "test-workspace",
    }

    # Get capability
    capability = orchestrator.get_capability("provision_databricks")
    assert capability is not None

    # Create context
    context = CapabilityContext(
        user_request="I need a test Databricks workspace",
        capability_name="provision_databricks",
        parameters=parameters,
    )

    # Generate plan only (don't execute)
    plan = await capability.plan(context)

    # Validate orchestrator can work with the plan
    assert plan is not None
    assert plan.capability_name == "provision_databricks"
    assert plan.estimated_cost > 0

    # Verify plan summary is human-readable
    summary = plan.to_summary()
    assert "provision_databricks" in summary
    assert "Resource" in summary


def test_orchestrator_list_capabilities():
    """Test orchestrator can list all registered capabilities."""
    orchestrator = InfrastructureOrchestrator()

    capabilities = orchestrator.list_capabilities()

    # Should have at least Databricks
    assert len(capabilities) >= 1
    assert "provision_databricks" in capabilities


def test_orchestrator_get_unknown_capability():
    """Test getting an unknown capability returns None."""
    orchestrator = InfrastructureOrchestrator()

    capability = orchestrator.get_capability("unknown_capability")
    assert capability is None


@pytest.mark.asyncio
async def test_capability_plan_to_summary():
    """Test capability plan can generate human-readable summary."""
    capability = DatabricksCapability()

    context = CapabilityContext(
        user_request="Create Databricks workspace",
        capability_name="provision_databricks",
        parameters={
            "team": "analytics",
            "environment": "staging",
            "region": "westus2",
        }
    )

    plan = await capability.plan(context)
    summary = plan.to_summary()

    # Check summary contains key information
    assert "provision_databricks" in summary
    assert "Resource" in summary
    assert "Estimated cost" in summary
    assert "Estimated duration" in summary
    assert "$" in summary  # Cost should be formatted with $
