"""
Data models for the infrastructure provisioning agent.

These Pydantic dataclasses define the contracts between components:
- InfrastructureRequest: Parsed user intent
- InfrastructureDecision: Configuration decisions
- TerraformFiles: Generated Terraform HCL
- DeploymentResult: Final deployment output
"""

from pydantic.dataclasses import dataclass


@dataclass
class InfrastructureRequest:
    """
    User's infrastructure request parsed from natural language.

    This is the output of the IntentRecognizer component.

    Attributes:
        workspace_name: Name for the Databricks workspace
        team: Team name (e.g., "data_science", "ml", "data_engineering")
        environment: Deployment environment (dev, staging, prod)
        region: Azure region (e.g., "eastus", "westus2")
        enable_gpu: Whether GPU instances are required
        workload_type: Type of workload (data_engineering, ml, analytics)
        cost_limit: Optional monthly cost limit in USD
        additional_requirements: Any extra requirements from user

    Examples:
        >>> req = InfrastructureRequest(
        ...     workspace_name="ml-team-prod",
        ...     team="ml",
        ...     environment="prod",
        ...     region="eastus",
        ...     enable_gpu=True,
        ...     workload_type="ml"
        ... )
    """

    workspace_name: str
    team: str
    environment: str  # dev, staging, prod
    region: str
    enable_gpu: bool = False
    workload_type: str = "data_engineering"  # data_engineering, ml, analytics
    cost_limit: float | None = None
    additional_requirements: str | None = None


@dataclass
class InfrastructureDecision:
    """
    Configuration decisions made by the DecisionEngine.

    This is the output of the DecisionEngine component and input to
    TerraformGenerator.

    Attributes:
        workspace_name: Name for the workspace
        resource_group_name: Azure resource group name
        region: Azure region
        databricks_sku: Databricks SKU (standard, premium, trial)
        min_workers: Minimum number of cluster workers
        max_workers: Maximum number of cluster workers
        driver_instance_type: VM size for cluster driver
        worker_instance_type: VM size for cluster workers
        spark_version: Databricks runtime version
        autotermination_minutes: Auto-termination timeout
        enable_gpu: Whether GPU instances are enabled
        estimated_monthly_cost: Estimated monthly cost in USD
        cost_breakdown: Detailed cost breakdown by component
        justification: Explanation of configuration choices

    Examples:
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
        ...     estimated_monthly_cost=3500.0,
        ...     cost_breakdown={
        ...         "databricks_dbu": 1200.0,
        ...         "compute": 2100.0,
        ...         "storage": 200.0
        ...     },
        ...     justification="GPU instances for ML workload"
        ... )
    """

    workspace_name: str
    resource_group_name: str
    region: str
    databricks_sku: str  # standard, premium, trial
    min_workers: int
    max_workers: int
    driver_instance_type: str  # Azure VM size
    worker_instance_type: str  # Azure VM size
    spark_version: str
    autotermination_minutes: int
    enable_gpu: bool
    estimated_monthly_cost: float
    cost_breakdown: dict[str, float]
    justification: str


@dataclass
class TerraformFiles:
    """
    Generated Terraform HCL files.

    This is the output of the TerraformGenerator component.

    Attributes:
        main_tf: Contents of main.tf (resource definitions)
        variables_tf: Contents of variables.tf (input variables)
        outputs_tf: Contents of outputs.tf (output values)
        terraform_tfvars: Contents of terraform.tfvars (variable values)
        provider_tf: Contents of provider.tf (provider configuration)

    Examples:
        >>> files = TerraformFiles(
        ...     main_tf="resource \"azurerm_resource_group\" \"main\" {...}",
        ...     variables_tf="variable \"workspace_name\" {...}",
        ...     outputs_tf="output \"workspace_url\" {...}",
        ...     terraform_tfvars="workspace_name = \"test\"",
        ...     provider_tf="terraform { required_providers {...} }"
        ... )
    """

    main_tf: str
    variables_tf: str
    outputs_tf: str
    terraform_tfvars: str
    provider_tf: str


@dataclass
class DeploymentResult:
    """
    Final deployment result.

    This is the output of the TerraformExecutor and the final output
    of the entire agent pipeline.

    Attributes:
        success: Whether deployment succeeded
        workspace_url: URL of the deployed Databricks workspace
        workspace_id: Azure resource ID of the workspace
        resource_group_name: Name of the resource group
        firewall_ip: Public IP address for firewall rules (if applicable)
        instance_pool_id: ID of the Databricks Instance Pool (if created)
        deployment_time_seconds: Time taken for deployment
        terraform_outputs: All Terraform output values
        error_message: Error message if deployment failed
        terraform_plan: Terraform plan output (for review)

    Examples:
        >>> result = DeploymentResult(
        ...     success=True,
        ...     workspace_url="https://adb-123456.azuredatabricks.net",
        ...     workspace_id="/subscriptions/.../resourceGroups/rg-ml/...",
        ...     resource_group_name="rg-ml-team-prod",
        ...     deployment_time_seconds=850.5,
        ...     terraform_outputs={"workspace_url": "https://..."},
        ...     terraform_plan="Terraform will perform..."
        ... )
    """

    success: bool
    workspace_url: str | None = None
    workspace_id: str | None = None
    resource_group_name: str | None = None
    firewall_ip: str | None = None
    instance_pool_id: str | None = None
    deployment_time_seconds: float | None = None
    terraform_outputs: dict[str, str] | None = None
    error_message: str | None = None
    terraform_plan: str | None = None
