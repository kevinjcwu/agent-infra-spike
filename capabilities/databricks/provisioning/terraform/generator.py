"""Terraform HCL file generator.

This module generates Terraform configuration files from InfrastructureDecision
objects using Jinja2 templates.
"""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from ...models.schemas import InfrastructureDecision, TerraformFiles

logger = logging.getLogger(__name__)


class TerraformGenerator:
    """
    Generates Terraform HCL files from infrastructure decisions.

    Uses Jinja2 templates to render Terraform configuration files including
    main.tf, variables.tf, outputs.tf, terraform.tfvars, and provider.tf.
    """

    def __init__(self, templates_dir: str | Path | None = None):
        """
        Initialize the Terraform generator.

        Args:
            templates_dir: Directory containing Jinja2 templates.
                          Defaults to ./templates relative to project root.
        """
        if templates_dir is None:
            # Default to templates/ directory in project root
            # Since we're in capabilities/databricks/provisioning/terraform/, go up 5 levels to project root
            project_root = Path(__file__).parent.parent.parent.parent.parent
            templates_dir = project_root / "templates"
        else:
            templates_dir = Path(templates_dir)

        if not templates_dir.exists():
            raise FileNotFoundError(
                f"Templates directory not found: {templates_dir}\n"
                f"Please ensure Jinja2 templates exist in this directory."
            )

        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        logger.info(f"TerraformGenerator initialized with templates from: {templates_dir}")

    def generate(
        self,
        decision: InfrastructureDecision,
        environment: str = "prod",
        workload_type: str = "data_engineering",
        team: str = "infrastructure",
    ) -> TerraformFiles:
        """
        Generate Terraform configuration files from an infrastructure decision.

        Args:
            decision: Infrastructure decision containing configuration details
            environment: Environment name (dev, staging, prod) for tagging
            workload_type: Workload type for tagging
            team: Team name for tagging

        Returns:
            TerraformFiles object containing all generated HCL content

        Raises:
            TemplateNotFound: If required templates are missing
            ValueError: If template rendering fails

        Examples:
            >>> generator = TerraformGenerator()
            >>> decision = InfrastructureDecision(
            ...     workspace_name="ml-team-prod",
            ...     resource_group_name="rg-ml-team-prod",
            ...     region="eastus",
            ...     databricks_sku="premium",
            ...     min_workers=2,
            ...     max_workers=8,
            ...     driver_instance_type="Standard_DS4_v2",
            ...     worker_instance_type="Standard_NC6s_v3",
            ...     spark_version="13.3.x-gpu-ml-scala2.12",
            ...     autotermination_minutes=120,
            ...     enable_gpu=True,
            ...     estimated_monthly_cost=5000.0,
            ...     cost_breakdown={},
            ...     justification="GPU for ML workloads"
            ... )
            >>> files = generator.generate(decision)
            >>> "azurerm_databricks_workspace" in files.main_tf
            True
        """
        logger.info(f"Generating Terraform files for workspace: {decision.workspace_name}")

        # Prepare template context with all required variables
        context = {
            "workspace_name": decision.workspace_name,
            "resource_group_name": decision.resource_group_name,
            "region": decision.region,
            "databricks_sku": decision.databricks_sku,
            "min_workers": decision.min_workers,
            "max_workers": decision.max_workers,
            "driver_instance_type": decision.driver_instance_type,
            "worker_instance_type": decision.worker_instance_type,
            "spark_version": decision.spark_version,
            "autotermination_minutes": decision.autotermination_minutes,
            "enable_gpu": decision.enable_gpu,
            "estimated_monthly_cost": f"{decision.estimated_monthly_cost:.2f}",
            "environment": environment,
            "workload_type": workload_type,
            "team": team,
        }

        try:
            # Render each template
            main_tf = self._render_template("main.tf.j2", context)
            variables_tf = self._render_template("variables.tf.j2", context)
            outputs_tf = self._render_template("outputs.tf.j2", context)
            terraform_tfvars = self._render_template("terraform.tfvars.j2", context)
            provider_tf = self._render_template("provider.tf.j2", context)

            logger.info("Successfully generated all Terraform files")

            return TerraformFiles(
                main_tf=main_tf,
                variables_tf=variables_tf,
                outputs_tf=outputs_tf,
                terraform_tfvars=terraform_tfvars,
                provider_tf=provider_tf,
            )

        except TemplateNotFound as e:
            logger.error(f"Template not found: {e}")
            raise TemplateNotFound(
                f"Required template not found: {e.name}\n"
                f"Ensure all templates exist in {self.templates_dir}"
            ) from e
        except Exception as e:
            logger.error(f"Error generating Terraform files: {e}")
            raise ValueError(f"Failed to generate Terraform files: {e}") from e

    def _render_template(self, template_name: str, context: dict) -> str:
        """
        Render a Jinja2 template with the given context.

        Args:
            template_name: Name of the template file
            context: Variables to pass to the template

        Returns:
            Rendered template content as string

        Raises:
            TemplateNotFound: If template file doesn't exist
        """
        logger.debug(f"Rendering template: {template_name}")
        template = self.env.get_template(template_name)
        return template.render(**context)

    def validate_templates(self) -> dict[str, bool]:
        """
        Validate that all required templates exist and can be loaded.

        Returns:
            Dictionary mapping template names to existence status

        Examples:
            >>> generator = TerraformGenerator()
            >>> status = generator.validate_templates()
            >>> all(status.values())
            True
        """
        required_templates = [
            "main.tf.j2",
            "variables.tf.j2",
            "outputs.tf.j2",
            "terraform.tfvars.j2",
            "provider.tf.j2",
        ]

        status = {}
        for template_name in required_templates:
            template_path = self.templates_dir / template_name
            exists = template_path.exists()
            status[template_name] = exists

            if exists:
                logger.debug(f"Template found: {template_name}")
            else:
                logger.warning(f"Template missing: {template_name}")

        return status

    def generate_to_directory(
        self,
        decision: InfrastructureDecision,
        output_dir: str | Path,
        environment: str = "prod",
        workload_type: str = "data_engineering",
        team: str = "infrastructure",
    ) -> Path:
        """
        Generate Terraform files and write them to a directory.

        Args:
            decision: Infrastructure decision
            output_dir: Directory to write files to
            environment: Environment name for tagging
            workload_type: Workload type for tagging
            team: Team name for tagging

        Returns:
            Path to the output directory

        Examples:
            >>> generator = TerraformGenerator()
            >>> decision = InfrastructureDecision(...)
            >>> output_path = generator.generate_to_directory(
            ...     decision,
            ...     "/tmp/terraform"
            ... )
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating Terraform files to: {output_path}")

        # Generate files
        files = self.generate(
            decision=decision,
            environment=environment,
            workload_type=workload_type,
            team=team,
        )

        # Write each file
        file_mapping = {
            "main.tf": files.main_tf,
            "variables.tf": files.variables_tf,
            "outputs.tf": files.outputs_tf,
            "terraform.tfvars": files.terraform_tfvars,
            "provider.tf": files.provider_tf,
        }

        for filename, content in file_mapping.items():
            file_path = output_path / filename
            file_path.write_text(content)
            logger.debug(f"Wrote file: {file_path}")

        logger.info(f"Successfully wrote {len(file_mapping)} Terraform files to {output_path}")

        return output_path
