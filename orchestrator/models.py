"""
Data models for the orchestrator.

Defines request/response structures for orchestrator interactions.
"""

from typing import Optional

from pydantic import BaseModel, Field


class InfrastructureRequest(BaseModel):
    """User request for infrastructure provisioning."""

    raw_request: str = Field(..., description="Original user message")
    workspace_name: Optional[str] = Field(None, description="Workspace/resource name")
    team: Optional[str] = Field(None, description="Team name")
    environment: Optional[str] = Field(None, description="Environment (dev/staging/prod)")
    region: Optional[str] = Field(None, description="Azure region")
    resource_group: Optional[str] = Field(None, description="Azure resource group name")
    budget_limit: Optional[float] = Field(None, description="Monthly budget limit in USD")
    enable_gpu: bool = Field(False, description="Enable GPU support")
    workload_type: Optional[str] = Field(
        None, description="Workload type (data_engineering, ml, analytics)"
    )


class NamingConfig(BaseModel):
    """Configuration for resource naming."""

    team: str = Field(..., description="Team name")
    environment: str = Field(..., description="Environment")
    prefix: Optional[str] = Field(None, description="Custom prefix")
    suffix: Optional[str] = Field(None, description="Custom suffix")


class ProvisioningPlan(BaseModel):
    """Plan for infrastructure provisioning."""

    capability: str = Field(..., description="Capability to execute (e.g., provision_databricks)")
    workspace_name: str = Field(..., description="Workspace name")
    resource_group: str = Field(..., description="Resource group name")
    region: str = Field(..., description="Azure region")
    team: str = Field(..., description="Team name")
    environment: str = Field(..., description="Environment")
    enable_gpu: bool = Field(False, description="GPU enabled")
    workload_type: str = Field("data_engineering", description="Workload type")
    estimated_cost: float = Field(..., description="Estimated monthly cost in USD")
    requires_approval: bool = Field(True, description="Whether user approval is needed")


class ConversationState(BaseModel):
    """State of the orchestrator conversation."""

    messages_count: int = Field(default=0, description="Number of messages exchanged")
    has_complete_info: bool = Field(default=False, description="Whether we have all required info")
    plan_proposed: bool = Field(default=False, description="Whether plan has been proposed")
    plan_approved: bool = Field(default=False, description="Whether user approved plan")
    deployment_complete: bool = Field(default=False, description="Whether deployment has finished")
    current_plan: Optional[ProvisioningPlan] = Field(default=None, description="Current plan")

    # Gathered parameters from conversation
    team: Optional[str] = Field(default=None, description="Team name")
    environment: Optional[str] = Field(default=None, description="Environment")
    region: Optional[str] = Field(default=None, description="Azure region")
    workspace_name: Optional[str] = Field(default=None, description="Workspace name")
    enable_gpu: Optional[bool] = Field(default=None, description="GPU enabled")
    workload_type: Optional[str] = Field(default=None, description="Workload type")
