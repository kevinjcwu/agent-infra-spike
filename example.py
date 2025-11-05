#!/usr/bin/env python3
"""
Example script demonstrating the agent components.

This shows how to use the InfrastructureAgent to orchestrate the full pipeline
from natural language to (simulated) deployment.
"""

from agent import DecisionEngine, InfrastructureRequest, TerraformGenerator


def example_manual_pipeline():
    """Example using manually created request through individual components."""
    print("=" * 80)
    print("EXAMPLE 1: Manual Pipeline (Individual Components)")
    print("=" * 80)

    # Create a request manually
    request = InfrastructureRequest(
        workspace_name="ml-team-prod",
        team="ml",
        environment="prod",
        region="eastus",
        enable_gpu=True,
        workload_type="ml",
    )

    print("\n📋 Infrastructure Request:")
    print(f"  Workspace: {request.workspace_name}")
    print(f"  Team: {request.team}")
    print(f"  Environment: {request.environment}")
    print(f"  Region: {request.region}")
    print(f"  GPU Enabled: {request.enable_gpu}")
    print(f"  Workload: {request.workload_type}")

    # Make decision
    engine = DecisionEngine()
    decision = engine.make_decision(request)

    print("\n⚙️  Infrastructure Decision:")
    print(f"  Resource Group: {decision.resource_group_name}")
    print(f"  Databricks SKU: {decision.databricks_sku}")
    print(f"  Driver Instance: {decision.driver_instance_type}")
    print(f"  Worker Instance: {decision.worker_instance_type}")
    print(f"  Workers: {decision.min_workers}-{decision.max_workers}")
    print(f"  Spark Version: {decision.spark_version}")
    print(f"  Autotermination: {decision.autotermination_minutes} minutes")

    print("\n💰 Cost Estimate:")
    print(f"  Compute: ${decision.cost_breakdown['compute']:.2f}/month")
    print(f"  Databricks DBU: ${decision.cost_breakdown['databricks_dbu']:.2f}/month")
    print(f"  Storage: ${decision.cost_breakdown['storage']:.2f}/month")
    print(f"  Total: ${decision.estimated_monthly_cost:.2f}/month")

    print("\n📝 Justification:")
    print(f"  {decision.justification}")

    # Generate Terraform files
    print("\n🔧 Generating Terraform Files...")
    generator = TerraformGenerator()
    terraform_files = generator.generate(decision)

    print("\n📄 Generated Terraform Files:")
    print(f"  - provider.tf ({len(terraform_files.provider_tf)} bytes)")
    print(f"  - main.tf ({len(terraform_files.main_tf)} bytes)")
    print(f"  - variables.tf ({len(terraform_files.variables_tf)} bytes)")
    print(f"  - outputs.tf ({len(terraform_files.outputs_tf)} bytes)")
    print(f"  - terraform.tfvars ({len(terraform_files.terraform_tfvars)} bytes)")

    print("\n📋 Sample from main.tf:")
    print("  " + "\n  ".join(terraform_files.main_tf.split("\n")[:10]))


def example_infrastructure_agent_dry_run():
    """Example using InfrastructureAgent for dry-run deployment."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 2: InfrastructureAgent Dry-Run (Mock Deployment)")
    print("=" * 80)
    print("\n⚠️  Skipped: Requires Azure OpenAI credentials and Terraform")
    print("  Uncomment the code in example.py to test with real components\n")

    # Uncomment to test with real Azure OpenAI and Terraform dry-run:
    # try:
    #     agent = InfrastructureAgent()
    #
    #     user_request = "Create a dev workspace for data engineering team in East US"
    #     print(f"\n🗣️  User Request:")
    #     print(f'  "{user_request}"')
    #
    #     print("\n🚀 Starting dry-run deployment...")
    #     result = agent.provision_workspace(
    #         user_message=user_request,
    #         dry_run=True,  # Only run terraform plan
    #         auto_approve=True
    #     )
    #
    #     if result.success:
    #         print("\n✅ Dry-run successful!")
    #         print(f"  Terraform plan: {result.terraform_plan[:200]}...")
    #     else:
    #         print(f"\n❌ Dry-run failed: {result.error_message}")
    #
    # except Exception as e:
    #     print(f"\n⚠️  Error: {e}")
    #     print("  Note: Requires Azure OpenAI credentials and Terraform installed")


def example_infrastructure_agent_full():
    """Example showing how to use InfrastructureAgent for full deployment."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 3: InfrastructureAgent Full Deployment")
    print("=" * 80)
    print("\n⚠️  Informational: How to use InfrastructureAgent for real deployment")
    print()

    example_code = '''
    from agent import InfrastructureAgent
    from pathlib import Path

    # Initialize agent
    agent = InfrastructureAgent(
        working_dir=Path("./terraform-workspace")  # Optional: specify where to store Terraform files
    )

    # Option 1: Dry-run (plan only, no deployment)
    result = agent.provision_workspace(
        user_message="Create prod workspace for ML team in East US with GPU",
        dry_run=True,
        auto_approve=True
    )

    # Option 2: Interactive approval (prompts user)
    result = agent.provision_workspace(
        user_message="Create prod workspace for ML team in East US with GPU",
        auto_approve=False  # Will prompt for approval after showing plan
    )

    # Option 3: Auto-approve (fully automated)
    result = agent.provision_workspace(
        user_message="Create prod workspace for ML team in East US with GPU",
        auto_approve=True  # Deploys immediately without prompting
    )

    # Check results
    if result.success:
        print(f"✅ Deployment successful!")
        print(f"Workspace URL: {result.workspace_url}")
        print(f"Resource Group: {result.resource_group_name}")
        print(f"Deployment time: {result.deployment_time_seconds:.1f} seconds")
    else:
        print(f"❌ Deployment failed: {result.error_message}")

    # Later, destroy the workspace
    destroy_result = agent.destroy_workspace(
        working_dir=Path("./terraform-workspace"),
        auto_approve=True
    )
    '''

    print(example_code)

    print("\n📝 Notes:")
    print("  - Requires Azure OpenAI credentials in .env")
    print("  - Requires Terraform CLI installed")
    print("  - Requires Azure credentials configured (az login)")
    print("  - Will create real Azure resources (costs apply)")


def main():
    """Run examples."""
    print("\n🚀 Agent Infrastructure Spike - Examples\n")

    # Example 1: Individual components (always works)
    example_manual_pipeline()

    # Example 2: Dry-run with agent (requires credentials)
    example_infrastructure_agent_dry_run()

    # Example 3: Full deployment example (informational)
    example_infrastructure_agent_full()

    print("\n" + "=" * 80)
    print("✅ Examples complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
