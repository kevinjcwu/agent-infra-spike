"""
Tests for configuration module.

Tests the Config class and its methods.
"""

from agent.config import Config


class TestConfig:
    """Tests for Config class."""

    def test_instance_types_cpu_small(self):
        """Test getting small CPU instance types."""
        instance_types = Config.get_instance_types(enable_gpu=False, size="small")

        assert instance_types["driver"] == "Standard_DS3_v2"
        assert instance_types["worker"] == "Standard_DS3_v2"

    def test_instance_types_cpu_medium(self):
        """Test getting medium CPU instance types."""
        instance_types = Config.get_instance_types(enable_gpu=False, size="medium")

        assert instance_types["driver"] == "Standard_DS4_v2"
        assert instance_types["worker"] == "Standard_DS4_v2"

    def test_instance_types_cpu_large(self):
        """Test getting large CPU instance types."""
        instance_types = Config.get_instance_types(enable_gpu=False, size="large")

        assert instance_types["driver"] == "Standard_DS5_v2"
        assert instance_types["worker"] == "Standard_DS5_v2"

    def test_instance_types_gpu_small(self):
        """Test getting small GPU instance types."""
        instance_types = Config.get_instance_types(enable_gpu=True, size="small")

        assert instance_types["driver"] == "Standard_DS3_v2"  # Driver doesn't need GPU
        assert instance_types["worker"] == "Standard_NC6s_v3"

    def test_instance_types_gpu_medium(self):
        """Test getting medium GPU instance types."""
        instance_types = Config.get_instance_types(enable_gpu=True, size="medium")

        assert instance_types["driver"] == "Standard_DS4_v2"
        assert instance_types["worker"] == "Standard_NC12s_v3"

    def test_instance_types_gpu_large(self):
        """Test getting large GPU instance types."""
        instance_types = Config.get_instance_types(enable_gpu=True, size="large")

        assert instance_types["driver"] == "Standard_DS5_v2"
        assert instance_types["worker"] == "Standard_NC24s_v3"

    def test_cost_estimation_basic(self):
        """Test basic cost estimation."""
        cost_breakdown = Config.estimate_monthly_cost(
            worker_instance_type="Standard_DS3_v2",
            driver_instance_type="Standard_DS3_v2",
            min_workers=2,
            max_workers=8,
            databricks_sku="standard",
            hours_per_month=730,
            utilization_factor=0.5,
        )

        assert "compute" in cost_breakdown
        assert "databricks_dbu" in cost_breakdown
        assert "storage" in cost_breakdown
        assert "total" in cost_breakdown
        assert cost_breakdown["total"] > 0
        assert cost_breakdown["storage"] == 200.0

    def test_cost_estimation_gpu(self):
        """Test cost estimation with GPU instances."""
        cost_breakdown = Config.estimate_monthly_cost(
            worker_instance_type="Standard_NC6s_v3",
            driver_instance_type="Standard_DS4_v2",
            min_workers=2,
            max_workers=8,
            databricks_sku="premium",
            hours_per_month=730,
            utilization_factor=0.5,
        )

        # GPU instances should be more expensive
        assert cost_breakdown["total"] > 3000.0
        assert cost_breakdown["compute"] > 2000.0

    def test_databricks_sku_map(self):
        """Test Databricks SKU mappings."""
        assert Config.DATABRICKS_SKU_MAP["dev"] == "standard"
        assert Config.DATABRICKS_SKU_MAP["staging"] == "standard"
        assert Config.DATABRICKS_SKU_MAP["prod"] == "premium"

    def test_cluster_config(self):
        """Test cluster configuration mappings."""
        dev_config = Config.CLUSTER_CONFIG["dev"]
        assert dev_config["min_workers"] == 1
        assert dev_config["max_workers"] == 4
        assert dev_config["autotermination_minutes"] == 30

        prod_config = Config.CLUSTER_CONFIG["prod"]
        assert prod_config["min_workers"] == 2
        assert prod_config["max_workers"] == 16
        assert prod_config["autotermination_minutes"] == 120

    def test_spark_versions(self):
        """Test Spark version mappings."""
        assert "scala2.12" in Config.SPARK_VERSIONS["cpu"]
        assert "gpu-ml" in Config.SPARK_VERSIONS["gpu"]
        assert Config.SPARK_VERSIONS["default"] == "13.3.x-scala2.12"

    def test_workload_size_map(self):
        """Test workload to size mappings."""
        assert Config.WORKLOAD_SIZE_MAP["data_engineering"] == "medium"
        assert Config.WORKLOAD_SIZE_MAP["ml"] == "large"
        assert Config.WORKLOAD_SIZE_MAP["analytics"] == "small"
