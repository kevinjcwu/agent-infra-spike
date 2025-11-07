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
    "When user says 'yes', 'proceed', 'go ahead', or 'deploy', you MUST call this tool with ALL parameters."
)
def execute_deployment(
    capability_name: Annotated[str, Field(description="Name of capability (e.g., 'provision_databricks')")],
    team: Annotated[str, Field(description="Team name")],
    environment: Annotated[str, Field(description="Environment (dev/staging/prod)")],
    region: Annotated[str, Field(description="Azure region (e.g., 'eastus')")],
    workspace_name: Annotated[str, Field(description="Workspace name")],
    enable_gpu: Annotated[bool, Field(description="Enable GPU support")],
    workload_type: Annotated[str, Field(description="Workload type (data_engineering/ml/analytics)")]
) -> str:
    """Execute infrastructure deployment after user approval."""
    return json.dumps({
        "status": "executing",
        "capability": capability_name,
        "message": "Deployment is now being executed. This will take 5-15 minutes. Check console for progress.",
        "parameters": {
            "team": team,
            "environment": environment,
            "region": region,
            "workspace_name": workspace_name,
            "enable_gpu": enable_gpu,
            "workload_type": workload_type
        }
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
def estimate_cost(
    capability: Annotated[str, Field(description="Capability name (e.g., 'provision_databricks')")],
    enable_gpu: Annotated[bool, Field(description="Whether GPU support is needed")],
    workload_type: Annotated[str, Field(description="Workload type: data_engineering, ml, or analytics")]
) -> str:
    """Estimate monthly infrastructure costs."""
    costs = {"capability": capability, "monthly_estimate": 0.0, "breakdown": [], "currency": "USD"}

    if capability == "provision_databricks":
        # Base workspace cost
        costs["breakdown"].append({"item": "Databricks Workspace", "cost": 0.0, "note": "No base fee"})

        # Compute costs - use parameters directly instead of from dict
        # enable_gpu = configuration.get("enable_gpu", False)
        # workload_type = configuration.get("workload_type", "data_engineering")

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

        # Storage
        costs["breakdown"].append({"item": "Azure Storage (Blob)", "cost": 50.0, "note": "~500GB data"})
        costs["monthly_estimate"] += 50.0

    elif capability == "provision_openai":
        costs["breakdown"].append({
            "item": "Azure OpenAI Service",
            "cost": 200.0,
            "note": "GPT-4, ~1M tokens/month",
        })
        costs["monthly_estimate"] += 200.0

    elif capability == "configure_firewall":
        costs["breakdown"].append({
            "item": "Azure Firewall Rules",
            "cost": 0.0,
            "note": "No additional cost for rule changes",
        })

    costs["confidence"] = "medium"
    costs["notes"] = [
        "Estimates based on typical usage patterns",
        "Actual costs may vary based on usage",
        "Does not include egress/ingress bandwidth",
    ]

    return json.dumps(costs)
