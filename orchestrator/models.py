"""
Data models for the orchestrator.

Defines request/response structures for orchestrator interactions.
"""

from typing import Any

from pydantic import BaseModel, Field


class InfrastructureRequest(BaseModel):
    """User request for infrastructure provisioning.

    Generic request structure - capability-specific parameters are stored
    in the parameters dict rather than as individual fields.
    """

    raw_request: str = Field(..., description="Original user message")
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Capability-specific parameters gathered from conversation"
    )


class NamingConfig(BaseModel):
    """Configuration for resource naming."""

    team: str = Field(..., description="Team name")
    environment: str = Field(..., description="Environment")
    prefix: str | None = Field(None, description="Custom prefix")
    suffix: str | None = Field(None, description="Custom suffix")


class ProvisioningPlan(BaseModel):
    """Plan for infrastructure provisioning.

    Generic plan structure - capability-specific details are stored in
    the parameters dict rather than as individual fields.
    """

    capability: str = Field(..., description="Capability to execute (e.g., provision_databricks)")
    region: str = Field(..., description="Azure region")
    team: str = Field(..., description="Team name")
    environment: str = Field(..., description="Environment")
    estimated_cost: float = Field(..., description="Estimated monthly cost in USD")
    requires_approval: bool = Field(True, description="Whether user approval is needed")
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="All capability-specific parameters as key-value pairs"
    )


class ConversationState(BaseModel):
    """State of the orchestrator conversation.

    Generic state tracking - capability-specific parameters are stored in
    the parameters dict rather than as individual fields.
    """

    messages_count: int = Field(default=0, description="Number of messages exchanged")
    has_complete_info: bool = Field(default=False, description="Whether we have all required info")
    plan_proposed: bool = Field(default=False, description="Whether plan has been proposed")
    plan_approved: bool = Field(default=False, description="Whether user approved plan")
    deployment_complete: bool = Field(default=False, description="Whether deployment has finished")
    current_plan: ProvisioningPlan | None = Field(default=None, description="Current plan")

    # Generic parameters gathered from conversation - stored as dict
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Capability-specific parameters gathered during conversation"
    )
