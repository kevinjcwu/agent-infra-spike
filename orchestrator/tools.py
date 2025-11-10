"""
Tools for the Infrastructure Orchestrator.

This module contains all tool functions that the orchestrator can call.
Tools are automatically registered via the @tool_manager.register decorator.
"""

import json
from typing import Annotated, Any

from pydantic import Field

from orchestrator.capability_registry import capability_registry
from orchestrator.tool_manager import tool_manager


@tool_manager.register(
    "REQUIRED: Execute infrastructure deployment after user approval. "
    "When user says 'yes', 'proceed', 'go ahead', or 'deploy', you MUST call this tool with capability name and ALL gathered parameters."
)
async def execute_deployment(
    capability_name: Annotated[str, Field(description="Name of capability (e.g., 'provision_databricks')")],
    parameters: Annotated[dict[str, Any], Field(description="All parameters gathered from conversation as a dict")]
) -> str:
    """Execute infrastructure deployment after user approval.

    This tool actually triggers the infrastructure provisioning.

    Args:
        capability_name: The capability to execute
        parameters: Dict containing all capability-specific parameters

    Returns:
        JSON string with deployment status
    """
    orchestrator = tool_manager.orchestrator
    if not orchestrator:
        return json.dumps({
            "status": "error",
            "message": "Orchestrator not available"
        })

    try:
        # Execute the capability (async call)
        plan, result = await orchestrator.execute_capability(
            capability_name=capability_name,
            user_request="Deploy infrastructure",
            parameters=parameters
        )

        # Update orchestrator state
        orchestrator.state.plan_approved = True
        orchestrator.state.deployment_complete = True

        return json.dumps({
            "status": "success",
            "capability": capability_name,
            "message": result.message,
            "outputs": result.outputs or {},
            "duration_seconds": result.duration_seconds
        })

    except Exception as e:
        return json.dumps({
            "status": "error",
            "capability": capability_name,
            "message": f"Deployment failed: {str(e)}"
        })


@tool_manager.register(
    "Select required infrastructure capabilities based on user requirements. "
    "Use this to declare which capabilities are needed after understanding the user's workload."
)
def select_capabilities(
    capabilities: Annotated[list[str], Field(description="List of capability identifiers (must match exact names from registry)")],
    rationale: Annotated[str, Field(description="Explanation of why these capabilities were selected")]
) -> str:
    """Validate and confirm infrastructure capability selection."""
    validated = []
    errors = []

    # Validate each capability against registry
    for cap in capabilities:
        is_valid, error_msg = capability_registry.validate_capability(cap)

        if is_valid:
            info = capability_registry.get_capability_info(cap)
            if info:  # Should always be true if validation passed
                validated.append({
                    "name": cap,
                    "display_name": info["display_name"],
                    "description": info["description"],
                })
        else:
            errors.append(error_msg)

    # If any invalid capabilities, return error
    if errors:
        return json.dumps({
            "status": "error",
            "errors": errors,
            "valid_capabilities": capability_registry.get_valid_capability_names(),
            "hint": "Use exact capability names from the available list",
        })

    # Success - return validated capabilities
    return json.dumps({
        "status": "success",
        "capabilities": validated,
        "count": len(validated),
        "rationale": rationale,
        "next_steps": "Gather configuration details for each capability",
    })


@tool_manager.register("Generate smart resource naming suggestions following Azure best practices")
def suggest_naming(
    team: Annotated[str, Field(description="Team name (e.g., 'ml', 'data-eng')")],
    environment: Annotated[str, Field(description="Environment (dev, staging, prod)")],
    resource_type: Annotated[str, Field(description="Type of resource (resource_group, workspace, storage)")]
) -> str:
    """Generate smart naming suggestions following Azure best practices."""
    # Sanitize inputs for naming
    team_clean = team.lower().replace(" ", "-").replace("_", "-")
    env_clean = environment.lower()[:4]  # dev, stag, prod

    suggestions = {}

    if resource_type == "resource_group":
        suggestions["primary"] = f"rg-{team_clean}-{env_clean}"
        suggestions["alternatives"] = [
            f"rg-{team_clean}-{env_clean}-001",
            f"rg-databricks-{team_clean}-{env_clean}",
            f"{team_clean}-{env_clean}-rg",
        ]

    elif resource_type == "workspace":
        suggestions["primary"] = f"{team_clean}-{env_clean}"
        suggestions["alternatives"] = [
            f"dbw-{team_clean}-{env_clean}",
            f"{team_clean}-databricks-{env_clean}",
            f"{team_clean}-workspace-{env_clean}",
        ]

    elif resource_type == "storage":
        # Storage accounts: lowercase, no hyphens, max 24 chars
        team_short = team_clean.replace("-", "")[:8]
        suggestions["primary"] = f"sa{team_short}{env_clean}001"
        suggestions["alternatives"] = [
            f"st{team_short}{env_clean}",
            f"{team_short}{env_clean}storage",
        ]

    else:
        suggestions["primary"] = f"{team_clean}-{env_clean}-{resource_type}"
        suggestions["alternatives"] = []

    suggestions["pattern_info"] = {
        "follows_azure_conventions": True,
        "pattern": "resource_type-team-environment",
        "example": suggestions["primary"],
    }

    return json.dumps(suggestions)


@tool_manager.register("Estimate monthly infrastructure costs for capabilities")
async def estimate_cost(
    capability: str,
    parameters: dict[str, Any] | None = None
) -> str:
    """Estimate monthly infrastructure costs.

    NOTE: This is a simplified estimation function for the orchestrator.
    For production, this should query each capability's cost estimation method
    or use Azure Pricing API.

    Args:
        capability: The capability to estimate costs for
        parameters: Dict containing capability-specific parameters

    Returns:
        JSON string with cost breakdown
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"estimate_cost called with capability={capability}, parameters={parameters}")
    logger.info(f"Types: capability={type(capability)}, parameters={type(parameters)}")

    # Handle None parameters
    if parameters is None:
        parameters = {}

    try:
        # TODO: Refactor to use capability.estimate_cost(parameters) method
        # For now, using a simplified lookup to avoid hardcoded if/elif chains

        cost_estimators = _get_cost_estimators()

        if capability in cost_estimators:
            costs = cost_estimators[capability](parameters)
        else:
            # Default/unknown capability
            costs = {
                "capability": capability,
                "monthly_estimate": 0.0,
                "breakdown": [],
                "currency": "USD",
                "confidence": "unknown",
                "notes": [f"No cost estimator configured for '{capability}'"]
            }

        costs["confidence"] = costs.get("confidence", "medium")
        costs["notes"] = costs.get("notes", [
            "Estimates based on typical usage patterns",
            "Actual costs may vary based on usage",
            "Does not include egress/ingress bandwidth",
        ])

        return json.dumps(costs)

    except Exception as e:
        # Return error in JSON format so LLM can explain it to user
        import traceback
        return json.dumps({
            "status": "error",
            "capability": capability,
            "message": f"Cost estimation failed: {str(e)}",
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        })


def _get_cost_estimators() -> dict[str, Any]:
    """Get cost estimation functions for each capability.

    This is a temporary solution. In production, each capability should
    implement its own estimate_cost() method.
    """
    return {
        "provision_databricks": _estimate_databricks_cost,
    }


def _estimate_databricks_cost(parameters: dict[str, Any]) -> dict[str, Any]:
    """Estimate Databricks costs from parameters."""
    costs = {
        "capability": "provision_databricks",
        "monthly_estimate": 0.0,
        "breakdown": [],
        "currency": "USD"
    }

    costs["breakdown"].append({"item": "Databricks Workspace", "cost": 0.0, "note": "No base fee"})

    enable_gpu = parameters.get("enable_gpu", False)
    workload_type = parameters.get("workload_type", "data_engineering")

    if enable_gpu:
        costs["breakdown"].append({
            "item": "GPU Cluster (Standard_NC6s_v3)",
            "cost": 1200.0,
            "note": "ML workload, ~40 hours/week",
        })
        costs["monthly_estimate"] += 1200.0
    else:
        base_cost = 784.0 if workload_type == "data_engineering" else 500.0
        costs["breakdown"].append({
            "item": f"Standard Cluster ({workload_type})",
            "cost": base_cost,
            "note": "Standard_DS3_v2, ~40 hours/week",
        })
        costs["monthly_estimate"] += base_cost

    costs["breakdown"].append({"item": "Azure Storage (Blob)", "cost": 50.0, "note": "~500GB data"})
    costs["monthly_estimate"] += 50.0

    return costs
