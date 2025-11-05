"""
Configuration management for the infrastructure agent.

This module loads environment variables and defines constants used throughout
the agent, including Azure credentials, OpenAI API keys, instance type mappings,
and cost tables.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Config:
    """
    Central configuration class for the infrastructure agent.

    Loads settings from environment variables and provides constants
    for instance types, costs, and region mappings.
    """

    # =============================================================================
    # Environment Variables (from .env)
    # =============================================================================

    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    AZURE_OPENAI_TEMPERATURE: float = float(os.getenv("AZURE_OPENAI_TEMPERATURE", "0.2"))

    # Azure Configuration
    AZURE_SUBSCRIPTION_ID: str = os.getenv("AZURE_SUBSCRIPTION_ID", "")
    AZURE_TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "")
    AZURE_CLIENT_ID: str = os.getenv("AZURE_CLIENT_ID", "")
    AZURE_CLIENT_SECRET: str = os.getenv("AZURE_CLIENT_SECRET", "")

    # Databricks Configuration
    DATABRICKS_ACCOUNT_ID: str = os.getenv("DATABRICKS_ACCOUNT_ID", "")

    # Terraform Configuration
    TERRAFORM_WORKING_DIR: Path = Path(
        os.getenv("TERRAFORM_WORKING_DIR", "./terraform_workspaces")
    )
    TERRAFORM_TIMEOUT_SECONDS: int = int(
        os.getenv("TERRAFORM_TIMEOUT_SECONDS", "1800")
    )

    # Agent Configuration
    REQUIRE_APPROVAL: bool = os.getenv("REQUIRE_APPROVAL", "false").lower() == "true"
    DRY_RUN: bool = os.getenv("DRY_RUN", "false").lower() == "true"

    # =============================================================================
    # Azure VM Instance Types
    # =============================================================================

    # CPU-based instance types for different workload sizes
    INSTANCE_TYPES_CPU = {
        "small": {
            "driver": "Standard_D4s_v5",  # 4 vCPUs, 16 GB RAM (Databricks supported)
            "worker": "Standard_D4s_v5",
        },
        "medium": {
            "driver": "Standard_DS4_v2",  # 8 vCPUs, 28 GB RAM
            "worker": "Standard_DS4_v2",
        },
        "large": {
            "driver": "Standard_DS5_v2",  # 16 vCPUs, 56 GB RAM
            "worker": "Standard_DS5_v2",
        },
    }

    # GPU-based instance types for ML workloads
    INSTANCE_TYPES_GPU = {
        "small": {
            "driver": "Standard_DS3_v2",  # Driver doesn't need GPU
            "worker": "Standard_NC6s_v3",  # 1x V100 GPU, 6 vCPUs, 112 GB RAM
        },
        "medium": {
            "driver": "Standard_DS4_v2",
            "worker": "Standard_NC12s_v3",  # 2x V100 GPU, 12 vCPUs, 224 GB RAM
        },
        "large": {
            "driver": "Standard_DS5_v2",
            "worker": "Standard_NC24s_v3",  # 4x V100 GPU, 24 vCPUs, 448 GB RAM
        },
    }

    # =============================================================================
    # Databricks SKU Mappings
    # =============================================================================

    DATABRICKS_SKU_MAP = {
        "dev": "standard",  # Development environments use standard SKU
        "staging": "standard",  # Staging can use standard
        "prod": "premium",  # Production requires premium for SLA, RBAC, etc.
    }

    # =============================================================================
    # Spark Version Mappings
    # =============================================================================

    SPARK_VERSIONS = {
        "cpu": "13.3.x-scala2.12",  # Latest stable for CPU workloads
        "gpu": "13.3.x-gpu-ml-scala2.12",  # GPU-enabled for ML workloads
        "default": "13.3.x-scala2.12",
    }

    # =============================================================================
    # Cluster Configuration
    # =============================================================================

    CLUSTER_CONFIG = {
        "dev": {
            "min_workers": 1,
            "max_workers": 2,  # Reduced from 4 for cost savings
            "autotermination_minutes": 10,  # Reduced from 30 for faster termination
        },
        "staging": {
            "min_workers": 1,
            "max_workers": 3,  # Reduced from 8 for cost savings
            "autotermination_minutes": 10,  # Reduced from 60 for faster termination
        },
        "prod": {
            "min_workers": 1,
            "max_workers": 4,  # Reduced from 16 for cost savings
            "autotermination_minutes": 10,  # Reduced from 120 for faster termination
        },
    }

    # =============================================================================
    # Cost Estimation Tables (USD per hour)
    # =============================================================================

    # VM costs per hour (approximate Azure pricing)
    VM_COSTS_PER_HOUR = {
        "Standard_DS3_v2": 0.192,
        "Standard_DS4_v2": 0.384,
        "Standard_DS5_v2": 0.768,
        "Standard_NC6s_v3": 3.06,
        "Standard_NC12s_v3": 6.12,
        "Standard_NC24s_v3": 12.24,
    }

    # Databricks Unit (DBU) costs per hour
    DBU_COSTS_PER_HOUR = {
        "standard": 0.15,  # Standard SKU
        "premium": 0.20,  # Premium SKU (higher cost for advanced features)
    }

    # Average DBU consumption per VM size (estimated)
    DBU_PER_VM_SIZE = {
        "Standard_DS3_v2": 0.75,
        "Standard_DS4_v2": 1.5,
        "Standard_DS5_v2": 3.0,
        "Standard_NC6s_v3": 2.0,
        "Standard_NC12s_v3": 4.0,
        "Standard_NC24s_v3": 8.0,
    }

    # =============================================================================
    # Azure Region Mappings
    # =============================================================================

    AZURE_REGIONS = {
        "eastus": "East US",
        "eastus2": "East US 2",
        "westus": "West US",
        "westus2": "West US 2",
        "westus3": "West US 3",
        "centralus": "Central US",
        "northcentralus": "North Central US",
        "southcentralus": "South Central US",
        "westcentralus": "West Central US",
    }

    # Default region if not specified
    DEFAULT_REGION = "eastus"

    # =============================================================================
    # Workload Type Mappings
    # =============================================================================

    WORKLOAD_SIZE_MAP = {
        # Team types to recommended instance size
        "data_engineering": "medium",
        "ml": "large",  # ML typically needs more resources
        "analytics": "small",
        "data_science": "medium",
        "etl": "medium",
    }

    # =============================================================================
    # Validation
    # =============================================================================

    @classmethod
    def validate(cls) -> None:
        """
        Validate that all required environment variables are set.

        Raises:
            ValueError: If required environment variables are missing.
        """
        required_vars = [
            ("AZURE_OPENAI_ENDPOINT", cls.AZURE_OPENAI_ENDPOINT),
            ("AZURE_OPENAI_API_KEY", cls.AZURE_OPENAI_API_KEY),
            ("AZURE_SUBSCRIPTION_ID", cls.AZURE_SUBSCRIPTION_ID),
            ("AZURE_TENANT_ID", cls.AZURE_TENANT_ID),
            ("AZURE_CLIENT_ID", cls.AZURE_CLIENT_ID),
            ("AZURE_CLIENT_SECRET", cls.AZURE_CLIENT_SECRET),
        ]

        missing_vars = [name for name, value in required_vars if not value]

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                f"Please set these in your .env file or environment."
            )

        logger.info("Configuration validated successfully")

    @classmethod
    def get_instance_types(cls, enable_gpu: bool, size: str = "medium") -> dict:
        """
        Get instance types based on GPU requirement and size.

        Args:
            enable_gpu: Whether GPU instances are needed
            size: Size of instances (small, medium, large)

        Returns:
            Dictionary with 'driver' and 'worker' instance types
        """
        if enable_gpu:
            return cls.INSTANCE_TYPES_GPU.get(size, cls.INSTANCE_TYPES_GPU["medium"])
        return cls.INSTANCE_TYPES_CPU.get(size, cls.INSTANCE_TYPES_CPU["medium"])

    @classmethod
    def estimate_monthly_cost(
        cls,
        worker_instance_type: str,
        driver_instance_type: str,
        min_workers: int,
        max_workers: int,
        databricks_sku: str,
        hours_per_month: int = 730,  # Average hours in a month
        utilization_factor: float = 0.5,  # Assume 50% utilization
    ) -> dict[str, float]:
        """
        Estimate monthly cost for a Databricks workspace.

        Args:
            worker_instance_type: Azure VM size for workers
            driver_instance_type: Azure VM size for driver
            min_workers: Minimum number of workers
            max_workers: Maximum number of workers
            databricks_sku: Databricks SKU (standard or premium)
            hours_per_month: Number of hours per month
            utilization_factor: Expected cluster utilization (0.0-1.0)

        Returns:
            Dictionary with cost breakdown
        """
        # Average number of workers (between min and max, factoring utilization)
        avg_workers = (min_workers + max_workers) / 2 * utilization_factor

        # VM costs
        worker_vm_cost = (
            cls.VM_COSTS_PER_HOUR.get(worker_instance_type, 0.5)
            * avg_workers
            * hours_per_month
        )
        driver_vm_cost = (
            cls.VM_COSTS_PER_HOUR.get(driver_instance_type, 0.2) * hours_per_month
        )
        total_vm_cost = worker_vm_cost + driver_vm_cost

        # DBU costs
        worker_dbu_cost = (
            cls.DBU_PER_VM_SIZE.get(worker_instance_type, 1.0)
            * cls.DBU_COSTS_PER_HOUR.get(databricks_sku, 0.15)
            * avg_workers
            * hours_per_month
        )
        driver_dbu_cost = (
            cls.DBU_PER_VM_SIZE.get(driver_instance_type, 0.75)
            * cls.DBU_COSTS_PER_HOUR.get(databricks_sku, 0.15)
            * hours_per_month
        )
        total_dbu_cost = worker_dbu_cost + driver_dbu_cost

        # Storage (rough estimate)
        storage_cost = 200.0  # ~$200/month for typical workspace storage

        # Total
        total_cost = total_vm_cost + total_dbu_cost + storage_cost

        return {
            "compute": round(total_vm_cost, 2),
            "databricks_dbu": round(total_dbu_cost, 2),
            "storage": round(storage_cost, 2),
            "total": round(total_cost, 2),
        }


# Validate configuration on import
try:
    Config.validate()
except ValueError as e:
    logger.warning(f"Configuration validation failed: {e}")
    logger.warning("Some features may not work without proper configuration")
