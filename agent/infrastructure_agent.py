"""
Main Infrastructure Agent orchestrator.

This module provides the InfrastructureAgent class that orchestrates the entire
provisioning pipeline from natural language request to deployed infrastructure.

NOTE: This is a thin wrapper around capabilities.databricks for backward compatibility.
New code should use the orchestrator + capability pattern directly.
"""

import logging
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular import at runtime
if TYPE_CHECKING:
    from capabilities.databricks import (
        DecisionEngine,
        DeploymentResult,
        IntentRecognizer,
        TerraformExecutor,
        TerraformGenerator,
    )

logger = logging.getLogger(__name__)


class AgentError(Exception):
    """Base exception for agent errors."""

    pass


class ValidationError(AgentError):
    """Validation failed."""

    pass


class InfrastructureAgent:
    """
    Main orchestrator for infrastructure provisioning.

    This class coordinates all components to provision Databricks workspaces
    from natural language requests.

    Example:
        >>> agent = InfrastructureAgent()
        >>> result = agent.provision_workspace(
        ...     "Create prod workspace for ML team in East US",
        ...     auto_approve=True
        ... )
        >>> print(result.workspace_url)
    """

    def __init__(
        self,
        intent_recognizer: "IntentRecognizer | None" = None,
        decision_engine: "DecisionEngine | None" = None,
        terraform_generator: "TerraformGenerator | None" = None,
        terraform_executor: "TerraformExecutor | None" = None,
        working_dir: Path | None = None,
    ):
        """
        Initialize the Infrastructure Agent.

        Args:
            intent_recognizer: Component for parsing natural language.
                             If None, creates default instance.
            decision_engine: Component for making config decisions.
                           If None, creates default instance.
            terraform_generator: Component for generating Terraform files.
                               If None, creates default instance.
            terraform_executor: Component for executing Terraform.
                              If None, creates default instance.
            working_dir: Directory for Terraform files. If None, uses temp dir.
        """
        # Import here to avoid circular import
        from capabilities.databricks import (
            DecisionEngine,
            IntentRecognizer,
            TerraformExecutor,
            TerraformGenerator,
        )

        self.intent_recognizer = intent_recognizer or IntentRecognizer()
        self.decision_engine = decision_engine or DecisionEngine()
        self.terraform_generator = terraform_generator or TerraformGenerator()
        self.terraform_executor = terraform_executor or TerraformExecutor()
        self.working_dir = working_dir

        logger.info("InfrastructureAgent initialized")

    def provision_workspace(
        self,
        user_message: str,
        auto_approve: bool = False,
        dry_run: bool = False,
    ) -> "DeploymentResult":
        """
        Provision a Databricks workspace from natural language request.

        This is the main entry point that orchestrates the full pipeline:
        1. Parse natural language → InfrastructureRequest
        2. Make configuration decisions → InfrastructureDecision
        3. Generate Terraform files → TerraformFiles
        4. Execute Terraform deployment → DeploymentResult

        Args:
            user_message: Natural language request describing the workspace.
                         Example: "Create prod workspace for ML team in East US"
            auto_approve: If True, skip approval prompt and deploy automatically.
                         If False, prompt user for approval before deployment.
            dry_run: If True, only run terraform plan without applying changes.

        Returns:
            DeploymentResult containing workspace details and deployment status.

        Raises:
            ValidationError: If the request cannot be parsed or validated.
            AgentError: If any step in the pipeline fails.

        Example:
            >>> agent = InfrastructureAgent()
            >>> result = agent.provision_workspace(
            ...     "Create dev workspace for data engineering team",
            ...     auto_approve=True
            ... )
            >>> print(f"Workspace URL: {result.workspace_url}")
        """
        start_time = time.time()
        logger.info("=" * 80)
        logger.info("Starting workspace provisioning")
        logger.info(f"Request: {user_message}")
        logger.info(f"Auto-approve: {auto_approve}, Dry-run: {dry_run}")
        logger.info("=" * 80)

        try:
            # Step 1: Parse natural language request
            logger.info("\n[1/4] Parsing natural language request...")
            infrastructure_request = self.intent_recognizer.recognize_intent(
                user_message
            )
            logger.info("✓ Parsed request:")
            logger.info(f"  - Workspace: {infrastructure_request.workspace_name}")
            logger.info(f"  - Team: {infrastructure_request.team}")
            logger.info(f"  - Environment: {infrastructure_request.environment}")
            logger.info(f"  - Region: {infrastructure_request.region}")
            logger.info(f"  - GPU enabled: {infrastructure_request.enable_gpu}")
            logger.info(f"  - Workload: {infrastructure_request.workload_type}")

            # Step 2: Make configuration decisions
            logger.info("\n[2/4] Making infrastructure configuration decisions...")
            infrastructure_decision = self.decision_engine.make_decision(
                infrastructure_request
            )
            logger.info("✓ Configuration decided:")
            logger.info(f"  - Driver: {infrastructure_decision.driver_instance_type}")
            logger.info(f"  - Workers: {infrastructure_decision.worker_instance_type}")
            logger.info(f"  - SKU: {infrastructure_decision.databricks_sku}")
            logger.info(
                f"  - Estimated cost: ${infrastructure_decision.estimated_monthly_cost:.2f}/month"
            )
            logger.info(
                f"  - Resource group: {infrastructure_decision.resource_group_name}"
            )

            # Step 3: Generate Terraform files
            logger.info("\n[3/4] Generating Terraform configuration files...")
            terraform_files = self.terraform_generator.generate(
                infrastructure_decision
            )
            logger.info("✓ Generated Terraform files:")
            logger.info(f"  - provider.tf ({len(terraform_files.provider_tf)} bytes)")
            logger.info(f"  - main.tf ({len(terraform_files.main_tf)} bytes)")
            logger.info(
                f"  - variables.tf ({len(terraform_files.variables_tf)} bytes)"
            )
            logger.info(f"  - outputs.tf ({len(terraform_files.outputs_tf)} bytes)")
            logger.info(
                f"  - terraform.tfvars ({len(terraform_files.terraform_tfvars)} bytes)"
            )

            # Step 4: Execute Terraform deployment
            logger.info("\n[4/4] Executing Terraform deployment...")
            if dry_run:
                logger.info("Running in DRY-RUN mode (plan only, no apply)")

            # Use provided working_dir or create temporary directory
            if self.working_dir:
                working_dir = self.working_dir
                logger.info(f"Using working directory: {working_dir}")
                result = self.terraform_executor.execute_deployment(
                    terraform_files=terraform_files,
                    working_dir=working_dir,
                    auto_approve=auto_approve,
                    dry_run=dry_run,
                )
            else:
                # Use temporary directory that auto-cleans up
                logger.info("Using temporary working directory")
                with TemporaryDirectory() as tmpdir:
                    working_dir = Path(tmpdir)
                    result = self.terraform_executor.execute_deployment(
                        terraform_files=terraform_files,
                        working_dir=working_dir,
                        auto_approve=auto_approve,
                        dry_run=dry_run,
                    )

            # Log final results
            total_time = time.time() - start_time
            logger.info("\n" + "=" * 80)
            if result.success:
                logger.info("✓ PROVISIONING SUCCESSFUL")
                if not dry_run and result.workspace_url:
                    logger.info(f"Workspace URL: {result.workspace_url}")
                    logger.info(f"Resource Group: {result.resource_group_name}")
                elif dry_run:
                    logger.info("Dry-run completed successfully (plan validated)")
            else:
                logger.error("✗ PROVISIONING FAILED")
                logger.error(f"Error: {result.error_message}")

            logger.info(f"Total time: {total_time:.1f} seconds")
            logger.info("=" * 80)

            return result

        except Exception as e:
            total_time = time.time() - start_time
            logger.error("\n" + "=" * 80)
            logger.error("✗ PROVISIONING FAILED")
            logger.error(f"Error: {str(e)}")
            logger.error(f"Total time: {total_time:.1f} seconds")
            logger.error("=" * 80)

            # Import here to avoid circular dependency
            from capabilities.databricks import DeploymentResult

            # Return failed result
            return DeploymentResult(
                success=False,
                workspace_url=None,
                workspace_id=None,
                resource_group_name=None,
                deployment_time_seconds=total_time,
                terraform_plan=None,
                terraform_outputs=None,
                error_message=f"Agent error: {str(e)}",
            )

    def destroy_workspace(
        self,
        working_dir: Path,
        auto_approve: bool = False,
    ) -> "DeploymentResult":
        """
        Destroy a previously provisioned workspace.

        Args:
            working_dir: Directory containing the Terraform state for the workspace.
            auto_approve: If True, skip approval prompt and destroy automatically.

        Returns:
            DeploymentResult indicating success or failure.

        Example:
            >>> agent = InfrastructureAgent()
            >>> result = agent.destroy_workspace(
            ...     working_dir=Path("/path/to/terraform"),
            ...     auto_approve=True
            ... )
        """
        logger.info("=" * 80)
        logger.info("Starting workspace destruction")
        logger.info(f"Working directory: {working_dir}")
        logger.info(f"Auto-approve: {auto_approve}")
        logger.info("=" * 80)

        try:
            result = self.terraform_executor.destroy_deployment(
                working_dir=working_dir,
                auto_approve=auto_approve,
            )

            logger.info("\n" + "=" * 80)
            if result.success:
                logger.info("✓ DESTRUCTION SUCCESSFUL")
            else:
                logger.error("✗ DESTRUCTION FAILED")
                logger.error(f"Error: {result.error_message}")
            logger.info("=" * 80)

            return result

        except Exception as e:
            logger.error("\n" + "=" * 80)
            logger.error("✗ DESTRUCTION FAILED")
            logger.error(f"Error: {str(e)}")
            logger.error("=" * 80)

            # Import here to avoid circular dependency
            from capabilities.databricks import DeploymentResult

            return DeploymentResult(
                success=False,
                workspace_url=None,
                workspace_id=None,
                resource_group_name=None,
                deployment_time_seconds=0,
                terraform_plan=None,
                terraform_outputs=None,
                error_message=f"Agent error: {str(e)}",
            )
