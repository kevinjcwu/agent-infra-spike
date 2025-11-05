"""
Tests for the decision engine.

Tests the DecisionEngine's ability to make appropriate infrastructure
configuration decisions based on various request parameters.
"""

from agent.decision_engine import DecisionEngine
from agent.models import InfrastructureRequest


class TestDecisionEngine:
    """Tests for DecisionEngine class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = DecisionEngine()

    def test_basic_dev_workspace(self):
        """Test decisions for a basic dev workspace."""
        request = InfrastructureRequest(
            workspace_name="test-dev",
            team="data_engineering",
            environment="dev",
            region="eastus",
            workload_type="data_engineering",
        )

        decision = self.engine.make_decision(request)

        assert decision.workspace_name == "test-dev"
        assert decision.databricks_sku == "standard"
        assert decision.enable_gpu is False
        assert decision.min_workers == 1
        assert decision.max_workers == 4
        assert decision.autotermination_minutes == 30
        assert "CPU instances" in decision.justification

    def test_prod_ml_workspace_with_gpu(self):
        """Test decisions for production ML workspace with GPU."""
        request = InfrastructureRequest(
            workspace_name="ml-team-prod",
            team="ml",
            environment="prod",
            region="eastus",
            enable_gpu=True,
            workload_type="ml",
        )

        decision = self.engine.make_decision(request)

        assert decision.workspace_name == "ml-team-prod"
        assert decision.databricks_sku == "premium"
        assert decision.enable_gpu is True
        assert "NC" in decision.worker_instance_type  # GPU instance
        assert decision.min_workers == 2
        assert decision.max_workers == 16
        assert decision.autotermination_minutes == 120
        assert "gpu-ml" in decision.spark_version.lower()
        assert "GPU instances" in decision.justification
        assert "premium" in decision.justification.lower()

    def test_staging_analytics_workspace(self):
        """Test decisions for staging analytics workspace."""
        request = InfrastructureRequest(
            workspace_name="analytics-staging",
            team="analytics",
            environment="staging",
            region="westus2",
            workload_type="analytics",
        )

        decision = self.engine.make_decision(request)

        assert decision.workspace_name == "analytics-staging"
        assert decision.databricks_sku == "standard"
        assert decision.enable_gpu is False
        assert decision.min_workers == 2
        assert decision.max_workers == 8
        assert decision.autotermination_minutes == 60
        assert decision.estimated_monthly_cost > 0

    def test_cost_limit_enforcement(self):
        """Test that cost limits trigger instance downgrades."""
        request = InfrastructureRequest(
            workspace_name="budget-workspace",
            team="data_engineering",
            environment="dev",
            region="eastus",
            workload_type="data_engineering",
            cost_limit=500.0,  # Low cost limit
        )

        decision = self.engine.make_decision(request)

        # Should use small instances to stay within budget
        assert decision.estimated_monthly_cost <= 1000.0  # Reasonable after downgrade
        assert "budget" in decision.justification.lower() or "cost" in decision.justification.lower()

    def test_resource_group_naming(self):
        """Test resource group naming convention."""
        request = InfrastructureRequest(
            workspace_name="my-workspace",
            team="team",
            environment="dev",
            region="eastus",
        )

        decision = self.engine.make_decision(request)

        assert decision.resource_group_name == "rg-my-workspace"

    def test_gpu_spark_version_selection(self):
        """Test that GPU workloads get GPU-enabled Spark version."""
        request_gpu = InfrastructureRequest(
            workspace_name="gpu-workspace",
            team="ml",
            environment="dev",
            region="eastus",
            enable_gpu=True,
            workload_type="ml",
        )

        request_cpu = InfrastructureRequest(
            workspace_name="cpu-workspace",
            team="data_engineering",
            environment="dev",
            region="eastus",
            enable_gpu=False,
            workload_type="data_engineering",
        )

        decision_gpu = self.engine.make_decision(request_gpu)
        decision_cpu = self.engine.make_decision(request_cpu)

        assert "gpu" in decision_gpu.spark_version.lower()
        assert "gpu" not in decision_cpu.spark_version.lower()

    def test_prod_environment_premium_sku(self):
        """Test that production environments always get premium SKU."""
        request = InfrastructureRequest(
            workspace_name="prod-workspace",
            team="data_engineering",
            environment="prod",
            region="eastus",
            workload_type="data_engineering",
        )

        decision = self.engine.make_decision(request)

        assert decision.databricks_sku == "premium"
        assert "premium" in decision.justification.lower()

    def test_instance_size_determination(self):
        """Test instance size selection based on workload."""
        # ML workload should get large instances
        request_ml = InfrastructureRequest(
            workspace_name="ml-workspace",
            team="ml",
            environment="staging",
            region="eastus",
            workload_type="ml",
        )

        # Analytics workload should get small instances
        request_analytics = InfrastructureRequest(
            workspace_name="analytics-workspace",
            team="analytics",
            environment="staging",
            region="eastus",
            workload_type="analytics",
        )

        decision_ml = self.engine.make_decision(request_ml)
        decision_analytics = self.engine.make_decision(request_analytics)

        # ML should use larger instances than analytics
        ml_worker = decision_ml.worker_instance_type
        analytics_worker = decision_analytics.worker_instance_type

        # Check that ML uses DS4 or larger, analytics uses DS3
        assert "DS4" in ml_worker or "DS5" in ml_worker or "NC" in ml_worker
        assert "DS3" in analytics_worker

    def test_cost_breakdown_structure(self):
        """Test that cost breakdown includes all required components."""
        request = InfrastructureRequest(
            workspace_name="test-workspace",
            team="team",
            environment="dev",
            region="eastus",
        )

        decision = self.engine.make_decision(request)

        assert "compute" in decision.cost_breakdown
        assert "databricks_dbu" in decision.cost_breakdown
        assert "storage" in decision.cost_breakdown
        assert "total" in decision.cost_breakdown
        assert decision.cost_breakdown["total"] == decision.estimated_monthly_cost

    def test_additional_requirements_in_justification(self):
        """Test that additional requirements appear in justification."""
        request = InfrastructureRequest(
            workspace_name="special-workspace",
            team="team",
            environment="dev",
            region="eastus",
            additional_requirements="Need extra security features",
        )

        decision = self.engine.make_decision(request)

        assert "extra security features" in decision.justification.lower()

    def test_different_regions(self):
        """Test that region is properly passed through."""
        regions = ["eastus", "westus2", "centralus"]

        for region in regions:
            request = InfrastructureRequest(
                workspace_name=f"workspace-{region}",
                team="team",
                environment="dev",
                region=region,
            )

            decision = self.engine.make_decision(request)
            assert decision.region == region
