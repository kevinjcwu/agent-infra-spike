"""
Tests for the Terraform generator.

Tests the TerraformGenerator's ability to generate valid Terraform HCL
files from InfrastructureDecision objects.
"""

import tempfile
from pathlib import Path

import pytest
from jinja2 import TemplateNotFound

from agent.models import InfrastructureDecision
from agent.terraform_generator import TerraformGenerator


class TestTerraformGenerator:
    """Tests for TerraformGenerator class."""

    @pytest.fixture
    def sample_decision(self) -> InfrastructureDecision:
        """Create a sample infrastructure decision for testing."""
        return InfrastructureDecision(
            workspace_name="test-workspace",
            resource_group_name="rg-test-workspace",
            region="eastus",
            databricks_sku="premium",
            min_workers=2,
            max_workers=8,
            driver_instance_type="Standard_DS4_v2",
            worker_instance_type="Standard_DS4_v2",
            spark_version="13.3.x-scala2.12",
            autotermination_minutes=60,
            enable_gpu=False,
            estimated_monthly_cost=2500.0,
            cost_breakdown={
                "compute": 1500.0,
                "databricks_dbu": 800.0,
                "storage": 200.0,
            },
            justification="Standard configuration for test environment",
        )

    @pytest.fixture
    def gpu_decision(self) -> InfrastructureDecision:
        """Create a GPU-enabled infrastructure decision."""
        return InfrastructureDecision(
            workspace_name="ml-team-prod",
            resource_group_name="rg-ml-team-prod",
            region="westus2",
            databricks_sku="premium",
            min_workers=2,
            max_workers=16,
            driver_instance_type="Standard_DS5_v2",
            worker_instance_type="Standard_NC24s_v3",
            spark_version="13.3.x-gpu-ml-scala2.12",
            autotermination_minutes=120,
            enable_gpu=True,
            estimated_monthly_cost=46663.04,
            cost_breakdown={
                "compute": 40769.04,
                "databricks_dbu": 5694.0,
                "storage": 200.0,
            },
            justification="GPU instances for ML training workloads",
        )

    def test_generator_initialization(self):
        """Test that generator initializes correctly."""
        generator = TerraformGenerator()
        assert generator.templates_dir.exists()
        assert generator.env is not None

    def test_generator_with_custom_templates_dir(self, tmp_path):
        """Test initialization with custom templates directory."""
        # Create a temporary templates directory
        templates_dir = tmp_path / "custom_templates"
        templates_dir.mkdir()

        generator = TerraformGenerator(templates_dir=templates_dir)
        assert generator.templates_dir == templates_dir

    def test_generator_invalid_templates_dir(self):
        """Test that invalid templates directory raises error."""
        with pytest.raises(FileNotFoundError, match="Templates directory not found"):
            TerraformGenerator(templates_dir="/nonexistent/path")

    def test_generate_basic_terraform_files(self, sample_decision):
        """Test generating basic Terraform files."""
        generator = TerraformGenerator()
        files = generator.generate(sample_decision)

        # Check all files are generated
        assert files.main_tf is not None
        assert files.variables_tf is not None
        assert files.outputs_tf is not None
        assert files.terraform_tfvars is not None
        assert files.provider_tf is not None

        # Check files are non-empty
        assert len(files.main_tf) > 0
        assert len(files.variables_tf) > 0
        assert len(files.outputs_tf) > 0
        assert len(files.terraform_tfvars) > 0
        assert len(files.provider_tf) > 0

    def test_main_tf_contains_required_resources(self, sample_decision):
        """Test that main.tf contains required Terraform resources."""
        generator = TerraformGenerator()
        files = generator.generate(sample_decision)

        # Check for required resource blocks
        assert "azurerm_resource_group" in files.main_tf
        assert "azurerm_databricks_workspace" in files.main_tf
        assert "databricks_cluster" in files.main_tf

        # Check that variables are used (not hardcoded values)
        assert "var.workspace_name" in files.main_tf
        assert "var.resource_group_name" in files.main_tf

    def test_variables_tf_structure(self, sample_decision):
        """Test that variables.tf has proper structure."""
        generator = TerraformGenerator()
        files = generator.generate(sample_decision)

        # Check for required variable declarations
        required_vars = [
            "workspace_name",
            "resource_group_name",
            "region",
            "databricks_sku",
            "min_workers",
            "max_workers",
            "driver_instance_type",
            "worker_instance_type",
            "spark_version",
            "autotermination_minutes",
        ]

        for var_name in required_vars:
            assert f'variable "{var_name}"' in files.variables_tf
            assert "description" in files.variables_tf
            assert "type" in files.variables_tf

    def test_outputs_tf_structure(self, sample_decision):
        """Test that outputs.tf has proper structure."""
        generator = TerraformGenerator()
        files = generator.generate(sample_decision)

        # Check for required outputs
        required_outputs = [
            "workspace_url",
            "workspace_id",
            "resource_group_name",
            "cluster_id",
        ]

        for output_name in required_outputs:
            assert f'output "{output_name}"' in files.outputs_tf
            assert "description" in files.outputs_tf
            assert "value" in files.outputs_tf

    def test_terraform_tfvars_values(self, sample_decision):
        """Test that terraform.tfvars contains correct values."""
        generator = TerraformGenerator()
        files = generator.generate(sample_decision, environment="staging", team="data_eng")

        # Check that values are set correctly
        assert f'workspace_name             = "{sample_decision.workspace_name}"' in files.terraform_tfvars
        assert f'region                     = "{sample_decision.region}"' in files.terraform_tfvars
        assert f'databricks_sku             = "{sample_decision.databricks_sku}"' in files.terraform_tfvars
        assert f"min_workers                = {sample_decision.min_workers}" in files.terraform_tfvars
        assert f"max_workers                = {sample_decision.max_workers}" in files.terraform_tfvars

        # Check tags
        assert "staging" in files.terraform_tfvars
        assert "data_eng" in files.terraform_tfvars

    def test_provider_tf_structure(self, sample_decision):
        """Test that provider.tf has proper structure."""
        generator = TerraformGenerator()
        files = generator.generate(sample_decision)

        # Check for required provider configuration
        assert "terraform" in files.provider_tf
        assert "required_providers" in files.provider_tf
        assert "azurerm" in files.provider_tf
        assert "databricks" in files.provider_tf
        assert "required_version" in files.provider_tf

    def test_gpu_configuration(self, gpu_decision):
        """Test generation with GPU-enabled decision."""
        generator = TerraformGenerator()
        files = generator.generate(gpu_decision)

        # Check GPU instance type appears
        assert gpu_decision.worker_instance_type in files.terraform_tfvars
        assert "NC24s_v3" in files.terraform_tfvars

        # Check GPU Spark version
        assert gpu_decision.spark_version in files.terraform_tfvars
        assert "gpu" in files.terraform_tfvars

    def test_different_regions(self, sample_decision):
        """Test generation with different Azure regions."""
        generator = TerraformGenerator()

        regions = ["eastus", "westus2", "centralus", "northeurope"]

        for region in regions:
            sample_decision.region = region
            files = generator.generate(sample_decision)
            assert region in files.terraform_tfvars

    def test_different_skus(self, sample_decision):
        """Test generation with different Databricks SKUs."""
        generator = TerraformGenerator()

        skus = ["standard", "premium", "trial"]

        for sku in skus:
            sample_decision.databricks_sku = sku
            files = generator.generate(sample_decision)
            assert sku in files.terraform_tfvars

    def test_validate_templates(self):
        """Test template validation."""
        generator = TerraformGenerator()
        status = generator.validate_templates()

        # Check all required templates are found
        required_templates = [
            "main.tf.j2",
            "variables.tf.j2",
            "outputs.tf.j2",
            "terraform.tfvars.j2",
            "provider.tf.j2",
        ]

        for template in required_templates:
            assert template in status
            assert status[template] is True, f"Template {template} not found"

    def test_generate_to_directory(self, sample_decision):
        """Test generating files to a directory."""
        generator = TerraformGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = generator.generate_to_directory(
                sample_decision,
                tmpdir,
                environment="dev",
                team="test_team"
            )

            # Check that directory exists
            assert output_path.exists()
            assert output_path.is_dir()

            # Check that all files are created
            expected_files = [
                "main.tf",
                "variables.tf",
                "outputs.tf",
                "terraform.tfvars",
                "provider.tf",
            ]

            for filename in expected_files:
                file_path = output_path / filename
                assert file_path.exists(), f"File {filename} not created"
                assert file_path.stat().st_size > 0, f"File {filename} is empty"

    def test_generate_to_directory_creates_parent_dirs(self, sample_decision):
        """Test that generate_to_directory creates parent directories."""
        generator = TerraformGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "level1" / "level2" / "terraform"
            output_path = generator.generate_to_directory(sample_decision, nested_path)

            assert output_path.exists()
            assert (output_path / "main.tf").exists()

    def test_cost_estimation_in_tags(self, sample_decision):
        """Test that cost estimation appears in tags."""
        generator = TerraformGenerator()
        files = generator.generate(sample_decision)

        # Check cost appears in tags
        assert f"${sample_decision.estimated_monthly_cost:.2f}" in files.terraform_tfvars
        assert "EstimatedCost" in files.terraform_tfvars

    def test_custom_environment_and_team(self, sample_decision):
        """Test generation with custom environment and team."""
        generator = TerraformGenerator()
        files = generator.generate(
            sample_decision,
            environment="production",
            workload_type="ml",
            team="data_science"
        )

        assert "production" in files.terraform_tfvars
        assert "ml" in files.terraform_tfvars
        assert "data_science" in files.terraform_tfvars

    def test_cluster_configuration(self, sample_decision):
        """Test cluster configuration in main.tf."""
        generator = TerraformGenerator()
        files = generator.generate(sample_decision)

        # Check cluster resource configuration
        assert "databricks_cluster" in files.main_tf
        assert "autoscale" in files.main_tf
        assert "azure_attributes" in files.main_tf
        assert "spark_conf" in files.main_tf

    def test_autotermination_configuration(self, sample_decision):
        """Test autotermination is configured correctly."""
        generator = TerraformGenerator()

        # Test different autotermination values
        for minutes in [30, 60, 120]:
            sample_decision.autotermination_minutes = minutes
            files = generator.generate(sample_decision)
            assert f"autotermination_minutes    = {minutes}" in files.terraform_tfvars

    def test_render_template_error_handling(self):
        """Test error handling when template is missing."""
        generator = TerraformGenerator()

        # Try to render a non-existent template
        with pytest.raises(TemplateNotFound):
            generator._render_template("nonexistent.tf.j2", {})

    def test_generate_with_invalid_decision(self):
        """Test generation with missing template should raise appropriate error."""
        # Create generator with empty templates directory
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(TemplateNotFound):
                generator = TerraformGenerator(templates_dir=tmpdir)
                decision = InfrastructureDecision(
                    workspace_name="test",
                    resource_group_name="rg-test",
                    region="eastus",
                    databricks_sku="standard",
                    min_workers=1,
                    max_workers=4,
                    driver_instance_type="Standard_DS3_v2",
                    worker_instance_type="Standard_DS3_v2",
                    spark_version="13.3.x-scala2.12",
                    autotermination_minutes=30,
                    enable_gpu=False,
                    estimated_monthly_cost=1000.0,
                    cost_breakdown={},
                    justification="Test"
                )
                generator.generate(decision)
