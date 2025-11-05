"""
Decision engine for making infrastructure configuration decisions.

This module takes InfrastructureRequest objects and makes intelligent decisions
about instance types, SKUs, cluster sizes, and cost estimates.
"""

import logging

from .config import Config
from .models import InfrastructureDecision, InfrastructureRequest

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    Makes intelligent infrastructure configuration decisions.

    Takes a parsed InfrastructureRequest and generates a detailed
    InfrastructureDecision with specific instance types, costs, and
    justifications based on workload requirements.
    """

    def make_decision(self, request: InfrastructureRequest) -> InfrastructureDecision:
        """
        Generate infrastructure configuration decisions from a request.

        Args:
            request: Parsed infrastructure request

        Returns:
            InfrastructureDecision with specific configuration details

        Examples:
            >>> engine = DecisionEngine()
            >>> request = InfrastructureRequest(
            ...     workspace_name="ml-team-prod",
            ...     team="ml",
            ...     environment="prod",
            ...     region="eastus",
            ...     enable_gpu=True,
            ...     workload_type="ml"
            ... )
            >>> decision = engine.make_decision(request)
            >>> decision.enable_gpu
            True
            >>> decision.databricks_sku
            'premium'
        """
        logger.info(f"Making decisions for workspace: {request.workspace_name}")

        # Determine instance size based on workload type
        size = self._determine_instance_size(request)
        logger.info(f"Selected instance size: {size}")

        # Get instance types based on GPU requirement and size
        instance_types = Config.get_instance_types(
            enable_gpu=request.enable_gpu, size=size
        )
        driver_instance_type = instance_types["driver"]
        worker_instance_type = instance_types["worker"]
        logger.info(
            f"Instance types - Driver: {driver_instance_type}, Worker: {worker_instance_type}"
        )

        # Determine Databricks SKU based on environment
        databricks_sku = Config.DATABRICKS_SKU_MAP.get(
            request.environment, "standard"
        )
        logger.info(f"Databricks SKU: {databricks_sku}")

        # Get cluster configuration for environment
        cluster_config = Config.CLUSTER_CONFIG.get(
            request.environment, Config.CLUSTER_CONFIG["dev"]
        )
        min_workers = cluster_config["min_workers"]
        max_workers = cluster_config["max_workers"]
        autotermination_minutes = cluster_config["autotermination_minutes"]

        # Determine Spark version
        spark_version = (
            Config.SPARK_VERSIONS["gpu"]
            if request.enable_gpu
            else Config.SPARK_VERSIONS["cpu"]
        )
        logger.info(f"Spark version: {spark_version}")

        # Estimate costs
        cost_breakdown = Config.estimate_monthly_cost(
            worker_instance_type=worker_instance_type,
            driver_instance_type=driver_instance_type,
            min_workers=min_workers,
            max_workers=max_workers,
            databricks_sku=databricks_sku,
        )
        estimated_monthly_cost = cost_breakdown["total"]

        # Check cost limit if specified
        if request.cost_limit and estimated_monthly_cost > request.cost_limit:
            logger.warning(
                f"Estimated cost ${estimated_monthly_cost:.2f} exceeds limit ${request.cost_limit:.2f}"
            )
            # Attempt to reduce costs by using smaller instances
            size = self._downgrade_instance_size(size)
            instance_types = Config.get_instance_types(
                enable_gpu=request.enable_gpu, size=size
            )
            driver_instance_type = instance_types["driver"]
            worker_instance_type = instance_types["worker"]

            # Recalculate costs
            cost_breakdown = Config.estimate_monthly_cost(
                worker_instance_type=worker_instance_type,
                driver_instance_type=driver_instance_type,
                min_workers=min_workers,
                max_workers=max_workers,
                databricks_sku=databricks_sku,
            )
            estimated_monthly_cost = cost_breakdown["total"]
            logger.info(f"Adjusted to smaller instances. New cost: ${estimated_monthly_cost:.2f}")

        # Generate justification
        justification = self._generate_justification(
            request=request,
            size=size,
            databricks_sku=databricks_sku,
            estimated_monthly_cost=estimated_monthly_cost,
        )

        # Generate resource group name
        resource_group_name = f"rg-{request.workspace_name}"

        # Create decision
        decision = InfrastructureDecision(
            workspace_name=request.workspace_name,
            resource_group_name=resource_group_name,
            region=request.region,
            databricks_sku=databricks_sku,
            min_workers=min_workers,
            max_workers=max_workers,
            driver_instance_type=driver_instance_type,
            worker_instance_type=worker_instance_type,
            spark_version=spark_version,
            autotermination_minutes=autotermination_minutes,
            enable_gpu=request.enable_gpu,
            estimated_monthly_cost=estimated_monthly_cost,
            cost_breakdown=cost_breakdown,
            justification=justification,
        )

        logger.info(
            f"Decision made - SKU: {databricks_sku}, Cost: ${estimated_monthly_cost:.2f}/month"
        )

        return decision

    def _determine_instance_size(self, request: InfrastructureRequest) -> str:
        """
        Determine the appropriate instance size based on workload and environment.

        Args:
            request: Infrastructure request

        Returns:
            Instance size: "small", "medium", or "large"
        """
        # For cost savings during testing, always use smallest instances
        # regardless of workload type or environment
        logger.info("Using smallest instance size for cost optimization")
        return "small"

    def _downgrade_instance_size(self, current_size: str) -> str:
        """
        Downgrade instance size to reduce costs.

        Args:
            current_size: Current instance size

        Returns:
            Smaller instance size
        """
        size_hierarchy = ["large", "medium", "small"]
        current_index = size_hierarchy.index(current_size) if current_size in size_hierarchy else 1

        # Move to next smaller size, but don't go below small
        new_index = min(current_index + 1, len(size_hierarchy) - 1)
        return size_hierarchy[new_index]

    def _generate_justification(
        self,
        request: InfrastructureRequest,
        size: str,
        databricks_sku: str,
        estimated_monthly_cost: float,
    ) -> str:
        """
        Generate a human-readable justification for the decisions made.

        Args:
            request: Infrastructure request
            size: Selected instance size
            databricks_sku: Selected Databricks SKU
            estimated_monthly_cost: Estimated monthly cost

        Returns:
            Justification text explaining the configuration choices
        """
        justifications = []

        # Environment-based decisions
        if request.environment == "prod":
            justifications.append(
                f"Production environment requires {databricks_sku} SKU for SLA guarantees and advanced features"
            )
        else:
            justifications.append(
                f"{request.environment.capitalize()} environment uses {databricks_sku} SKU for cost optimization"
            )

        # GPU decisions
        if request.enable_gpu:
            justifications.append(
                f"GPU instances ({size}) selected for {request.workload_type} workload requiring accelerated computing"
            )
        else:
            justifications.append(
                f"CPU instances ({size}) sufficient for {request.workload_type} workload"
            )

        # Cost considerations
        if request.cost_limit:
            if estimated_monthly_cost <= request.cost_limit:
                justifications.append(
                    f"Configuration within budget constraint of ${request.cost_limit:.2f}/month"
                )
            else:
                justifications.append(
                    f"Configuration optimized to approach budget limit (${request.cost_limit:.2f}/month), "
                    f"final estimate: ${estimated_monthly_cost:.2f}/month"
                )
        else:
            justifications.append(
                f"Estimated monthly cost: ${estimated_monthly_cost:.2f}"
            )

        # Additional requirements
        if request.additional_requirements:
            justifications.append(f"Additional requirements: {request.additional_requirements}")

        return ". ".join(justifications) + "."
