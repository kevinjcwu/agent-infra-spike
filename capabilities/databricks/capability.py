"""Databricks provisioning capability.

This capability provides a standard capability interface for the orchestrator,
implementing Databricks workspace and cluster provisioning.
"""

import json
import time
from pathlib import Path
from typing import Any

from capabilities.base import (
    BaseCapability,
    CapabilityContext,
    CapabilityPlan,
    CapabilityResult,
)

from .core.decision_maker import DecisionMaker
from .core.intent_parser import IntentParser
from .models.schemas import InfrastructureRequest
from .provisioning.terraform.executor import TerraformExecutor
from .provisioning.terraform.generator import TerraformGenerator


class DatabricksCapability(BaseCapability):
    """Provision Azure Databricks workspace with compute clusters.

    This capability implements the full provisioning workflow:
    1. Parse user requirements (IntentParser)
    2. Make configuration decisions (DecisionMaker)
    3. Generate Terraform code (TerraformGenerator)
    4. Execute deployment (TerraformExecutor)
    """

    def __init__(self):
        """Initialize Databricks capability with core components."""
        self.intent_parser = IntentParser()
        self.decision_maker = DecisionMaker()
        self.terraform_generator = TerraformGenerator()
        self.terraform_executor = TerraformExecutor()

    @property
    def name(self) -> str:
        """Capability identifier."""
        return "provision_databricks"

    @property
    def description(self) -> str:
        """Human-readable description."""
        return "Provision Azure Databricks workspace with compute infrastructure"

    def get_required_parameters(self) -> list[str]:
        """Get required parameters for Databricks provisioning.

        Returns:
            List of required parameter names
        """
        return ["team", "environment", "region"]

    def get_optional_parameters(self) -> dict[str, Any]:
        """Get optional parameters and their defaults for Databricks.

        Returns:
            Dict of parameter names to default values
        """
        return {
            "workspace_name": None,  # Auto-generated if not provided
            "enable_gpu": False,
            "workload_type": "data_engineering",
            "instance_pool_enabled": False,
        }

    async def plan(self, context: CapabilityContext) -> CapabilityPlan:
        """Generate Databricks provisioning plan.

        Uses existing agent components to:
        1. Parse user requirements into InfrastructureRequest
        2. Make configuration decisions
        3. Generate Terraform plan (dry-run)
        4. Extract resource information and cost estimates

        Args:
            context: Contains user request and parameters from conversation

        Returns:
            CapabilityPlan with resources, costs, and terraform details
        """
        # Step 1: Parse user request into infrastructure requirements
        # Use parameters from orchestrator conversation if available
        request_text = self._build_request_text(context)
        infra_request = self.intent_parser.recognize_intent(request_text)

        # Override with explicit parameters from conversation
        if "team" in context.parameters:
            infra_request.team = context.parameters["team"]
        if "environment" in context.parameters:
            infra_request.environment = context.parameters["environment"]
        if "region" in context.parameters:
            infra_request.region = context.parameters["region"]
        if "workspace_name" in context.parameters:
            infra_request.workspace_name = context.parameters["workspace_name"]

        # Step 2: Make configuration decisions
        decision = self.decision_maker.make_decision(infra_request)

        # Step 3: Generate Terraform files
        terraform_files = self.terraform_generator.generate(decision)

        # Step 4: Create working directory and run terraform plan
        working_dir = Path("terraform_workspaces") / f"{decision.workspace_name}_plan"
        working_dir.mkdir(parents=True, exist_ok=True)

        # Execute deployment in dry-run mode to get plan
        # This writes files and runs terraform plan
        plan_result = self.terraform_executor.execute_deployment(
            terraform_files=terraform_files,
            working_dir=working_dir,
            auto_approve=False,
            dry_run=True,  # Plan only, don't apply
        )

        # Step 5: Extract resources and build CapabilityPlan
        resources = self._extract_resources(decision)
        estimated_cost = self._estimate_cost(decision)

        plan = CapabilityPlan(
            capability_name=self.name,
            description=f"Provision Databricks workspace for {infra_request.team} team ({infra_request.environment} environment)",
            resources=resources,
            estimated_cost=estimated_cost,
            estimated_duration=15,  # ~15 minutes typical deployment
            requires_approval=True,
            details={
                "decision": decision.__dict__,
                "terraform_files": {
                    "main.tf": terraform_files.main_tf,
                    "variables.tf": terraform_files.variables_tf,
                    "outputs.tf": terraform_files.outputs_tf,
                    "provider.tf": terraform_files.provider_tf,
                    "terraform.tfvars": terraform_files.terraform_tfvars,
                },
                "terraform_plan": plan_result.terraform_plan if plan_result.success else "Plan failed",
                "working_dir": str(working_dir),
            }
        )

        return plan

    async def execute(self, plan: CapabilityPlan) -> CapabilityResult:
        """Execute Databricks workspace deployment.

        Runs terraform apply using the plan generated earlier.

        Args:
            plan: Approved capability plan from plan() method

        Returns:
            CapabilityResult with deployment status and outputs
        """
        start_time = time.time()

        try:
            # Get working directory and terraform files from plan details
            working_dir = Path(plan.details["working_dir"])

            # Reconstruct terraform files from plan details
            terraform_files_data = plan.details["terraform_files"]

            # Reconstruct TerraformFiles object
            from .models import TerraformFiles
            terraform_files = TerraformFiles(
                main_tf=terraform_files_data["main.tf"],
                variables_tf=terraform_files_data["variables.tf"],
                outputs_tf=terraform_files_data["outputs.tf"],
                terraform_tfvars=terraform_files_data.get("terraform.tfvars", ""),
                provider_tf=terraform_files_data.get("provider.tf", ""),
            )

            # Execute terraform apply (dry_run=False)
            # Files were written during planning, but pass them anyway for safety
            result = self.terraform_executor.execute_deployment(
                terraform_files=terraform_files,
                working_dir=working_dir,
                auto_approve=True,  # Already approved by user
                dry_run=False,  # Actually deploy
            )

            # Build capability result from deployment result
            duration = time.time() - start_time

            if result.success:
                capability_result = CapabilityResult(
                    capability_name=self.name,
                    success=True,
                    message="Successfully deployed Databricks workspace",
                    resources_created=plan.resources,
                    outputs={
                        "workspace_url": result.workspace_url or "",
                        "workspace_id": result.workspace_id or "",
                        "resource_group": result.resource_group_name or "",
                    },
                    duration_seconds=duration,
                )
            else:
                capability_result = CapabilityResult(
                    capability_name=self.name,
                    success=False,
                    message="Failed to deploy Databricks workspace",
                    error=result.error_message,
                    duration_seconds=duration,
                )

            return capability_result

        except Exception as e:
            duration = time.time() - start_time

            result = CapabilityResult(
                capability_name=self.name,
                success=False,
                message="Failed to deploy Databricks workspace",
                error=str(e),
                duration_seconds=duration,
            )

            return result

    async def validate(self, context: CapabilityContext) -> tuple[bool, list[str]]:
        """Validate Databricks-specific requirements.

        Checks that essential parameters are present for Databricks provisioning.

        Args:
            context: Context to validate

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        # Check for required Azure configuration
        # Note: Actual Azure credentials are validated by Terraform
        # Here we just check for logical requirements

        # Could add validation like:
        # - Team name format
        # - Environment is valid (dev/staging/prod)
        # - Region is a valid Azure region
        # etc.

        return len(errors) == 0, errors

    def _build_request_text(self, context: CapabilityContext) -> str:
        """Build request text from context for intent recognizer.

        Combines original user request with parameters from conversation.
        """
        parts = [context.user_request]

        if "team" in context.parameters:
            parts.append(f"Team: {context.parameters['team']}")
        if "environment" in context.parameters:
            parts.append(f"Environment: {context.parameters['environment']}")
        if "region" in context.parameters:
            parts.append(f"Region: {context.parameters['region']}")

        return " | ".join(parts)

    def _extract_resources(self, decision) -> list[dict]:
        """Extract resource list from decision for plan display."""
        resources = [
            {
                "type": "Resource Group",
                "name": decision.resource_group_name,
            },
            {
                "type": "Databricks Workspace",
                "name": decision.workspace_name,
                "sku": decision.databricks_sku,
            },
        ]

        # Cluster is created if workers are configured
        if decision.max_workers > 0:
            resources.append({
                "type": "Databricks Cluster",
                "name": f"{decision.workspace_name}-cluster",
                "instance_type": decision.driver_instance_type,
                "workers": f"{decision.min_workers}-{decision.max_workers}",
            })

        return resources

    def _estimate_cost(self, decision) -> float:
        """Estimate monthly cost based on configuration.

        Rough estimates based on Azure pricing (as of 2024).
        """
        cost = 0.0

        # Databricks workspace: Premium SKU ~$100-200/month base
        if decision.databricks_sku == "premium":
            cost += 150.0
        else:
            cost += 75.0

        # Cluster compute costs (if cluster configured)
        if decision.max_workers > 0:
            # Rough VM costs per hour * average workers * hours/month
            # Standard_DS3_v2 ~$0.19/hour, NC6s_v3 (GPU) ~$1.14/hour
            instance_type = decision.driver_instance_type

            if "NC" in instance_type or "GPU" in instance_type:
                # GPU instance
                cost_per_hour = 1.14
            else:
                # Standard compute
                cost_per_hour = 0.19

            # Average workers (mid-point of min/max)
            avg_workers = (decision.min_workers + decision.max_workers) / 2

            # Assume running 12 hours/day, 22 days/month
            hours_per_month = 12 * 22

            # Driver + workers
            compute_cost = cost_per_hour * (1 + avg_workers) * hours_per_month
            cost += compute_cost

        return round(cost, 2)
