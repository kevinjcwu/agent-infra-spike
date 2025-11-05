"""
Terraform executor for running Terraform commands and managing deployments.

This module executes Terraform workflows (init, plan, apply) and parses outputs
to return structured DeploymentResult objects.
"""

import json
import logging
import subprocess
import time
from pathlib import Path

from .config import Config
from .models import DeploymentResult, TerraformFiles

logger = logging.getLogger(__name__)


class TerraformExecutor:
    """
    Executes Terraform commands and manages infrastructure deployments.

    Handles the complete Terraform workflow: init → plan → apply,
    with proper error handling, timeout management, and output parsing.
    """

    def __init__(self, timeout_seconds: int | None = None):
        """
        Initialize the Terraform executor.

        Args:
            timeout_seconds: Maximum time allowed for Terraform operations.
                            Defaults to Config.TERRAFORM_TIMEOUT_SECONDS.
        """
        self.timeout_seconds = timeout_seconds or Config.TERRAFORM_TIMEOUT_SECONDS
        logger.info(f"TerraformExecutor initialized with timeout: {self.timeout_seconds}s")

    def execute_deployment(
        self,
        terraform_files: TerraformFiles,
        working_dir: str | Path,
        auto_approve: bool = False,
        dry_run: bool = False,
    ) -> DeploymentResult:
        """
        Execute complete Terraform deployment workflow.

        Steps:
        1. Write Terraform files to working directory
        2. Run terraform init
        3. Run terraform plan
        4. Optionally wait for approval
        5. Run terraform apply (if approved and not dry_run)
        6. Parse outputs and return DeploymentResult

        Args:
            terraform_files: Generated Terraform HCL files
            working_dir: Directory to write files and run Terraform
            auto_approve: If True, skip approval and apply automatically
            dry_run: If True, only run plan (no apply)

        Returns:
            DeploymentResult with deployment status and outputs

        Raises:
            TerraformError: If any Terraform command fails

        Examples:
            >>> executor = TerraformExecutor()
            >>> result = executor.execute_deployment(
            ...     terraform_files=files,
            ...     working_dir="/tmp/workspace",
            ...     auto_approve=True
            ... )
            >>> result.success
            True
        """
        working_dir = Path(working_dir)
        start_time = time.time()

        logger.info(f"Starting Terraform deployment in: {working_dir}")

        try:
            # Step 1: Write Terraform files
            self._write_terraform_files(terraform_files, working_dir)

            # Step 2: Terraform init
            logger.info("Running terraform init...")
            init_result = self._run_terraform_command(
                ["terraform", "init"],
                working_dir=working_dir,
            )
            if init_result.returncode != 0:
                return DeploymentResult(
                    success=False,
                    error_message=f"terraform init failed: {init_result.stderr}",
                    deployment_time_seconds=time.time() - start_time,
                )

            # Step 3: Terraform plan
            logger.info("Running terraform plan...")
            plan_result = self._run_terraform_command(
                ["terraform", "plan", "-out=tfplan"],
                working_dir=working_dir,
            )
            if plan_result.returncode != 0:
                return DeploymentResult(
                    success=False,
                    error_message=f"terraform plan failed: {plan_result.stderr}",
                    terraform_plan=plan_result.stdout,
                    deployment_time_seconds=time.time() - start_time,
                )

            terraform_plan = plan_result.stdout

            # If dry-run, stop here
            if dry_run:
                logger.info("Dry-run mode: skipping terraform apply")
                return DeploymentResult(
                    success=True,
                    terraform_plan=terraform_plan,
                    deployment_time_seconds=time.time() - start_time,
                )

            # Step 4: Approval check
            if not auto_approve:
                logger.info("Waiting for manual approval...")
                approval = self._request_approval(terraform_plan)
                if not approval:
                    logger.info("Deployment cancelled by user")
                    return DeploymentResult(
                        success=False,
                        error_message="Deployment cancelled by user",
                        terraform_plan=terraform_plan,
                        deployment_time_seconds=time.time() - start_time,
                    )

            # Step 5: Terraform apply
            logger.info("Running terraform apply...")
            apply_result = self._run_terraform_command(
                ["terraform", "apply", "-auto-approve", "tfplan"],
                working_dir=working_dir,
            )
            if apply_result.returncode != 0:
                return DeploymentResult(
                    success=False,
                    error_message=f"terraform apply failed: {apply_result.stderr}",
                    terraform_plan=terraform_plan,
                    deployment_time_seconds=time.time() - start_time,
                )

            # Step 6: Parse outputs
            logger.info("Parsing terraform outputs...")
            outputs = self._parse_terraform_outputs(working_dir)

            deployment_time = time.time() - start_time
            logger.info(f"Deployment completed successfully in {deployment_time:.2f}s")

            return DeploymentResult(
                success=True,
                workspace_url=outputs.get("workspace_url"),
                workspace_id=outputs.get("workspace_id"),
                resource_group_name=outputs.get("resource_group_name"),
                instance_pool_id=outputs.get("instance_pool_id"),
                deployment_time_seconds=deployment_time,
                terraform_outputs=outputs,
                terraform_plan=terraform_plan,
            )

        except subprocess.TimeoutExpired as e:
            logger.error(f"Terraform command timeout: {e}")
            return DeploymentResult(
                success=False,
                error_message=f"Terraform command timeout after {self.timeout_seconds}s",
                deployment_time_seconds=time.time() - start_time,
            )
        except Exception as e:
            logger.error(f"Unexpected error during deployment: {e}")
            return DeploymentResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                deployment_time_seconds=time.time() - start_time,
            )

    def _write_terraform_files(
        self, terraform_files: TerraformFiles, working_dir: Path
    ) -> None:
        """
        Write Terraform files to the working directory.

        Args:
            terraform_files: Generated Terraform HCL files
            working_dir: Directory to write files to
        """
        working_dir.mkdir(parents=True, exist_ok=True)

        files_to_write = {
            "provider.tf": terraform_files.provider_tf,
            "main.tf": terraform_files.main_tf,
            "variables.tf": terraform_files.variables_tf,
            "outputs.tf": terraform_files.outputs_tf,
            "terraform.tfvars": terraform_files.terraform_tfvars,
        }

        for filename, content in files_to_write.items():
            file_path = working_dir / filename
            file_path.write_text(content)
            logger.debug(f"Wrote {filename} ({len(content)} bytes)")

        logger.info(f"Wrote {len(files_to_write)} Terraform files to {working_dir}")

    def _run_terraform_command(
        self, command: list[str], working_dir: Path
    ) -> subprocess.CompletedProcess:
        """
        Run a Terraform command with proper error handling.

        Args:
            command: Terraform command to run (e.g., ["terraform", "init"])
            working_dir: Directory to run command in

        Returns:
            CompletedProcess with stdout, stderr, and return code
        """
        logger.debug(f"Running command: {' '.join(command)}")

        result = subprocess.run(
            command,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
        )

        if result.returncode != 0:
            logger.error(f"Command failed with code {result.returncode}")
            logger.error(f"stderr: {result.stderr}")
        else:
            logger.debug("Command succeeded")

        return result

    def _parse_terraform_outputs(self, working_dir: Path) -> dict[str, str]:
        """
        Parse Terraform outputs using 'terraform output -json'.

        Args:
            working_dir: Directory containing Terraform state

        Returns:
            Dictionary of output names to values
        """
        try:
            result = self._run_terraform_command(
                ["terraform", "output", "-json"],
                working_dir=working_dir,
            )

            if result.returncode != 0:
                logger.warning("Failed to parse terraform outputs")
                return {}

            # Parse JSON output
            outputs_raw = json.loads(result.stdout)

            # Extract values from Terraform output format
            # Terraform outputs are in format: {"output_name": {"value": "actual_value"}}
            outputs = {}
            for key, value_obj in outputs_raw.items():
                if isinstance(value_obj, dict) and "value" in value_obj:
                    outputs[key] = str(value_obj["value"])
                else:
                    outputs[key] = str(value_obj)

            logger.info(f"Parsed {len(outputs)} terraform outputs")
            return outputs

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse terraform output JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error parsing terraform outputs: {e}")
            return {}

    def _request_approval(self, terraform_plan: str) -> bool:
        """
        Request user approval for deployment.

        Args:
            terraform_plan: Terraform plan output to show user

        Returns:
            True if approved, False if rejected
        """
        print("\n" + "=" * 80)
        print("TERRAFORM PLAN")
        print("=" * 80)
        print(terraform_plan)
        print("=" * 80)
        print("\nDo you want to apply this plan?")

        while True:
            response = input("Type 'yes' to approve, 'no' to cancel: ").strip().lower()
            if response == "yes":
                return True
            elif response == "no":
                return False
            else:
                print("Please type 'yes' or 'no'")

    def destroy_deployment(
        self, working_dir: str | Path, auto_approve: bool = False
    ) -> DeploymentResult:
        """
        Destroy a Terraform-managed deployment.

        Args:
            working_dir: Directory containing Terraform state
            auto_approve: If True, skip approval and destroy automatically

        Returns:
            DeploymentResult with destruction status
        """
        working_dir = Path(working_dir)
        start_time = time.time()

        logger.info(f"Starting Terraform destroy in: {working_dir}")

        try:
            # Request approval if needed
            if not auto_approve:
                logger.info("Waiting for destroy approval...")
                print("\n" + "=" * 80)
                print("WARNING: This will DESTROY all resources!")
                print("=" * 80)
                approval = input("Type 'yes' to destroy: ").strip().lower()
                if approval != "yes":
                    logger.info("Destroy cancelled by user")
                    return DeploymentResult(
                        success=False,
                        error_message="Destroy cancelled by user",
                        deployment_time_seconds=time.time() - start_time,
                    )

            # Run terraform destroy
            destroy_result = self._run_terraform_command(
                ["terraform", "destroy", "-auto-approve"],
                working_dir=working_dir,
            )

            if destroy_result.returncode != 0:
                return DeploymentResult(
                    success=False,
                    error_message=f"terraform destroy failed: {destroy_result.stderr}",
                    deployment_time_seconds=time.time() - start_time,
                )

            deployment_time = time.time() - start_time
            logger.info(f"Destroy completed successfully in {deployment_time:.2f}s")

            return DeploymentResult(
                success=True,
                deployment_time_seconds=deployment_time,
            )

        except Exception as e:
            logger.error(f"Error during destroy: {e}")
            return DeploymentResult(
                success=False,
                error_message=f"Destroy failed: {str(e)}",
                deployment_time_seconds=time.time() - start_time,
            )
