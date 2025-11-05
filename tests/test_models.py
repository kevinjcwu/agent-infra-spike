"""
Tests for data models.

Tests the Pydantic dataclasses to ensure proper validation and serialization.
"""

from agent.models import (
    DeploymentResult,
    InfrastructureDecision,
    InfrastructureRequest,
    TerraformFiles,
)


class TestInfrastructureRequest:
    """Tests for InfrastructureRequest dataclass."""

    def test_basic_request_creation(self):
        """Test creating a basic infrastructure request."""
        request = InfrastructureRequest(
            workspace_name="test-workspace",
            team="data_engineering",
            environment="dev",
            region="eastus",
        )

        assert request.workspace_name == "test-workspace"
        assert request.team == "data_engineering"
        assert request.environment == "dev"
        assert request.region == "eastus"
        assert request.enable_gpu is False
        assert request.workload_type == "data_engineering"
        assert request.cost_limit is None

    def test_request_with_gpu(self):
        """Test creating a request with GPU enabled."""
        request = InfrastructureRequest(
            workspace_name="ml-workspace",
            team="ml",
            environment="prod",
            region="westus2",
            enable_gpu=True,
            workload_type="ml",
        )

        assert request.enable_gpu is True
        assert request.workload_type == "ml"

    def test_request_with_cost_limit(self):
        """Test creating a request with cost limit."""
        request = InfrastructureRequest(
            workspace_name="test",
            team="analytics",
            environment="dev",
            region="eastus",
            cost_limit=1000.0,
        )

        assert request.cost_limit == 1000.0


class TestInfrastructureDecision:
    """Tests for InfrastructureDecision dataclass."""

    def test_basic_decision_creation(self):
        """Test creating a basic infrastructure decision."""
        decision = InfrastructureDecision(
            workspace_name="test-workspace",
            resource_group_name="rg-test-workspace",
            region="eastus",
            databricks_sku="standard",
            min_workers=2,
            max_workers=8,
            driver_instance_type="Standard_DS3_v2",
            worker_instance_type="Standard_DS3_v2",
            spark_version="13.3.x-scala2.12",
            autotermination_minutes=60,
            enable_gpu=False,
            estimated_monthly_cost=1500.0,
            cost_breakdown={
                "compute": 800.0,
                "databricks_dbu": 500.0,
                "storage": 200.0,
            },
            justification="Standard configuration for dev environment",
        )

        assert decision.workspace_name == "test-workspace"
        assert decision.databricks_sku == "standard"
        assert decision.min_workers == 2
        assert decision.max_workers == 8
        assert decision.estimated_monthly_cost == 1500.0

    def test_decision_with_gpu_instances(self):
        """Test creating a decision with GPU instances."""
        decision = InfrastructureDecision(
            workspace_name="ml-workspace",
            resource_group_name="rg-ml-workspace",
            region="eastus",
            databricks_sku="premium",
            min_workers=2,
            max_workers=8,
            driver_instance_type="Standard_DS4_v2",
            worker_instance_type="Standard_NC6s_v3",
            spark_version="13.3.x-gpu-ml-scala2.12",
            autotermination_minutes=120,
            enable_gpu=True,
            estimated_monthly_cost=5000.0,
            cost_breakdown={
                "compute": 3500.0,
                "databricks_dbu": 1300.0,
                "storage": 200.0,
            },
            justification="GPU instances for ML training workloads",
        )

        assert decision.enable_gpu is True
        assert decision.worker_instance_type == "Standard_NC6s_v3"
        assert decision.spark_version == "13.3.x-gpu-ml-scala2.12"


class TestTerraformFiles:
    """Tests for TerraformFiles dataclass."""

    def test_terraform_files_creation(self):
        """Test creating terraform files object."""
        files = TerraformFiles(
            main_tf="resource \"azurerm_resource_group\" {}",
            variables_tf="variable \"workspace_name\" {}",
            outputs_tf="output \"workspace_url\" {}",
            terraform_tfvars='workspace_name = "test"',
            provider_tf="terraform { required_providers {} }",
        )

        assert "azurerm_resource_group" in files.main_tf
        assert "workspace_name" in files.variables_tf
        assert "workspace_url" in files.outputs_tf
        assert "test" in files.terraform_tfvars
        assert "required_providers" in files.provider_tf


class TestDeploymentResult:
    """Tests for DeploymentResult dataclass."""

    def test_successful_deployment(self):
        """Test creating a successful deployment result."""
        result = DeploymentResult(
            success=True,
            workspace_url="https://adb-123456.azuredatabricks.net",
            workspace_id="/subscriptions/sub-id/resourceGroups/rg/...",
            resource_group_name="rg-test-workspace",
            deployment_time_seconds=850.5,
            terraform_outputs={
                "workspace_url": "https://adb-123456.azuredatabricks.net"
            },
        )

        assert result.success is True
        assert result.workspace_url == "https://adb-123456.azuredatabricks.net"
        assert result.deployment_time_seconds == 850.5
        assert result.error_message is None

    def test_failed_deployment(self):
        """Test creating a failed deployment result."""
        result = DeploymentResult(
            success=False,
            error_message="Terraform apply failed: resource already exists",
            terraform_plan="Plan output...",
        )

        assert result.success is False
        assert result.error_message is not None
        assert "resource already exists" in result.error_message
        assert result.workspace_url is None

    def test_deployment_with_all_fields(self):
        """Test creating a deployment result with all optional fields."""
        result = DeploymentResult(
            success=True,
            workspace_url="https://adb-123456.azuredatabricks.net",
            workspace_id="/subscriptions/sub-id/resourceGroups/rg/...",
            resource_group_name="rg-ml-prod",
            firewall_ip="20.30.40.50",
            cluster_id="1234-567890-abcdef",
            deployment_time_seconds=1205.3,
            terraform_outputs={
                "workspace_url": "https://adb-123456.azuredatabricks.net",
                "workspace_id": "/subscriptions/sub-id/...",
            },
            terraform_plan="Terraform will perform the following actions...",
        )

        assert result.success is True
        assert result.firewall_ip == "20.30.40.50"
        assert result.cluster_id == "1234-567890-abcdef"
        assert result.terraform_outputs is not None
        assert len(result.terraform_outputs) == 2
