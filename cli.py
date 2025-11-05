#!/usr/bin/env python3
"""
Command-line interface for the Infrastructure Agent.

This CLI provides a user-friendly way to provision and manage Databricks
workspaces using natural language requests.
"""

import logging
import sys
from pathlib import Path

import click

from agent import InfrastructureAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@click.group()
@click.version_option(version="0.1.0", prog_name="agent-infra")
def cli():
    """
    AI-powered Databricks Infrastructure Agent.

    Automates Databricks workspace provisioning from natural language requests.

    Examples:

        # Dry-run (plan only, no deployment)
        $ agent-infra provision --request "Create prod workspace for ML team" --dry-run

        # Interactive approval
        $ agent-infra provision --request "Create dev workspace for data team"

        # Fully automated
        $ agent-infra provision --request "Create workspace" --auto-approve

        # Destroy a workspace
        $ agent-infra destroy --working-dir ./terraform-state
    """
    pass


@cli.command()
@click.option(
    "--request",
    "-r",
    required=True,
    help="Natural language request describing the workspace to create.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Run terraform plan only, do not deploy.",
)
@click.option(
    "--auto-approve",
    "-y",
    is_flag=True,
    default=False,
    help="Skip approval prompt and deploy automatically.",
)
@click.option(
    "--working-dir",
    "-w",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory to store Terraform files. If not specified, uses temporary directory.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Enable verbose logging output.",
)
def provision(request, dry_run, auto_approve, working_dir, verbose):
    """
    Provision a new Databricks workspace from natural language.

    This command uses AI to parse your request, make intelligent configuration
    decisions, generate Terraform code, and deploy infrastructure to Azure.

    Examples:

        \b
        # Basic request with interactive approval
        $ agent-infra provision -r "Create workspace for ML team"

        \b
        # Production workspace with specific requirements
        $ agent-infra provision -r "Create prod workspace for ML team in East US with GPU support"

        \b
        # Dry-run to see what would be deployed
        $ agent-infra provision -r "Create dev workspace" --dry-run

        \b
        # Automated deployment with no prompts
        $ agent-infra provision -r "Create analytics workspace" --auto-approve
    """
    # Configure logging level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("agent").setLevel(logging.DEBUG)

    # Display header
    click.echo()
    click.secho("=" * 80, fg="cyan")
    click.secho("  Databricks Infrastructure Agent", fg="cyan", bold=True)
    click.secho("=" * 80, fg="cyan")
    click.echo()

    # Display configuration
    click.secho("📋 Configuration:", fg="blue", bold=True)
    click.echo(f"  Request: {request}")
    click.echo(f"  Mode: {'DRY-RUN (plan only)' if dry_run else 'DEPLOYMENT'}")
    click.echo(
        f"  Approval: {'AUTOMATIC' if auto_approve else 'INTERACTIVE (will prompt)'}"
    )
    if working_dir:
        click.echo(f"  Working directory: {working_dir}")
    else:
        click.echo("  Working directory: <temporary>")
    click.echo()

    # Confirm if not auto-approve and not dry-run
    if not auto_approve and not dry_run:
        click.secho("⚠️  This will provision real Azure resources.", fg="yellow")
        if not click.confirm("Continue?", default=True):
            click.secho("❌ Aborted by user.", fg="red")
            sys.exit(0)
        click.echo()

    try:
        # Initialize agent
        click.secho("🚀 Initializing Infrastructure Agent...", fg="green")
        agent = InfrastructureAgent(working_dir=working_dir)

        # Provision workspace
        click.secho("📡 Processing request...", fg="green")
        click.echo()

        result = agent.provision_workspace(
            user_message=request,
            auto_approve=auto_approve,
            dry_run=dry_run,
        )

        click.echo()

        # Display results
        if result.success:
            click.secho("=" * 80, fg="green")
            click.secho("✅ SUCCESS", fg="green", bold=True)
            click.secho("=" * 80, fg="green")
            click.echo()

            if dry_run:
                click.secho("📋 Dry-run Results:", fg="blue", bold=True)
                click.echo("  Terraform plan validated successfully")
                if result.terraform_plan:
                    click.echo(f"  Plan preview: {result.terraform_plan[:200]}...")
            else:
                click.secho("🎉 Workspace Deployed!", fg="green", bold=True)
                if result.workspace_url:
                    click.echo()
                    click.secho("  🔗 Workspace URL:", fg="blue", bold=True)
                    click.secho(f"     {result.workspace_url}", fg="cyan")
                if result.resource_group_name:
                    click.echo()
                    click.secho("  📦 Resource Group:", fg="blue", bold=True)
                    click.echo(f"     {result.resource_group_name}")
                if result.workspace_id:
                    click.echo()
                    click.secho("  🆔 Workspace ID:", fg="blue", bold=True)
                    click.echo(f"     {result.workspace_id}")

            if result.deployment_time_seconds is not None:
                click.echo()
                click.secho("  ⏱️  Time:", fg="blue", bold=True)
                minutes = int(result.deployment_time_seconds // 60)
                seconds = int(result.deployment_time_seconds % 60)
                click.echo(f"     {minutes}m {seconds}s")

            if result.terraform_outputs:
                click.echo()
                click.secho("  📊 Terraform Outputs:", fg="blue", bold=True)
                for key, value in result.terraform_outputs.items():
                    if key not in ["workspace_url", "workspace_id", "resource_group_name"]:
                        click.echo(f"     {key}: {value}")

            click.echo()
            sys.exit(0)

        else:
            click.secho("=" * 80, fg="red")
            click.secho("❌ FAILED", fg="red", bold=True)
            click.secho("=" * 80, fg="red")
            click.echo()

            click.secho("Error Details:", fg="red", bold=True)
            click.echo(f"  {result.error_message}")

            if result.deployment_time_seconds is not None:
                click.echo()
                click.secho("  ⏱️  Time before failure:", fg="blue")
                click.echo(f"     {result.deployment_time_seconds:.1f}s")

            click.echo()
            sys.exit(1)

    except KeyboardInterrupt:
        click.echo()
        click.secho("❌ Interrupted by user.", fg="red")
        sys.exit(130)

    except Exception as e:
        click.echo()
        click.secho("=" * 80, fg="red")
        click.secho("❌ UNEXPECTED ERROR", fg="red", bold=True)
        click.secho("=" * 80, fg="red")
        click.echo()
        click.secho(f"Error: {str(e)}", fg="red")
        if verbose:
            click.echo()
            click.secho("Stack trace:", fg="yellow")
            import traceback

            click.echo(traceback.format_exc())
        click.echo()
        sys.exit(1)


@cli.command()
@click.option(
    "--working-dir",
    "-w",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Directory containing Terraform state for the workspace to destroy.",
)
@click.option(
    "--auto-approve",
    "-y",
    is_flag=True,
    default=False,
    help="Skip confirmation prompt and destroy automatically.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Enable verbose logging output.",
)
def destroy(working_dir, auto_approve, verbose):
    """
    Destroy a previously provisioned workspace.

    This command runs 'terraform destroy' to tear down all infrastructure
    created by the agent. This action is irreversible and will delete all
    resources including data.

    Examples:

        \b
        # Interactive destruction (prompts for confirmation)
        $ agent-infra destroy --working-dir ./terraform-state

        \b
        # Automated destruction without prompts
        $ agent-infra destroy -w ./terraform-state --auto-approve
    """
    # Configure logging level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("agent").setLevel(logging.DEBUG)

    # Display header
    click.echo()
    click.secho("=" * 80, fg="red")
    click.secho("  Workspace Destruction", fg="red", bold=True)
    click.secho("=" * 80, fg="red")
    click.echo()

    # Display warning
    click.secho("⚠️  WARNING: This will PERMANENTLY DELETE all resources!", fg="yellow", bold=True)
    click.echo(f"  Working directory: {working_dir}")
    click.echo()

    # Confirm if not auto-approve
    if not auto_approve:
        click.secho("This action is IRREVERSIBLE and will delete:", fg="red")
        click.echo("  - Databricks workspace")
        click.echo("  - All clusters and notebooks")
        click.echo("  - Virtual network and subnets")
        click.echo("  - All associated Azure resources")
        click.echo()
        if not click.confirm("Are you ABSOLUTELY SURE you want to proceed?", default=False):
            click.secho("❌ Destruction cancelled.", fg="yellow")
            sys.exit(0)
        click.echo()

    try:
        # Initialize agent
        click.secho("🚀 Initializing Infrastructure Agent...", fg="green")
        agent = InfrastructureAgent()

        # Destroy workspace
        click.secho("💥 Starting destruction...", fg="red")
        click.echo()

        result = agent.destroy_workspace(
            working_dir=working_dir,
            auto_approve=auto_approve,
        )

        click.echo()

        # Display results
        if result.success:
            click.secho("=" * 80, fg="green")
            click.secho("✅ DESTRUCTION COMPLETE", fg="green", bold=True)
            click.secho("=" * 80, fg="green")
            click.echo()
            click.secho("All resources have been destroyed.", fg="green")

            if result.deployment_time_seconds is not None:
                click.echo()
                click.secho("  ⏱️  Time:", fg="blue", bold=True)
                click.echo(f"     {result.deployment_time_seconds:.1f}s")

            click.echo()
            sys.exit(0)

        else:
            click.secho("=" * 80, fg="red")
            click.secho("❌ DESTRUCTION FAILED", fg="red", bold=True)
            click.secho("=" * 80, fg="red")
            click.echo()

            click.secho("Error Details:", fg="red", bold=True)
            click.echo(f"  {result.error_message}")
            click.echo()
            click.secho("⚠️  Resources may still exist. Please check Azure Portal.", fg="yellow")
            click.echo()
            sys.exit(1)

    except KeyboardInterrupt:
        click.echo()
        click.secho("❌ Interrupted by user.", fg="red")
        click.echo()
        click.secho("⚠️  Destruction may be incomplete. Check Terraform state.", fg="yellow")
        sys.exit(130)

    except Exception as e:
        click.echo()
        click.secho("=" * 80, fg="red")
        click.secho("❌ UNEXPECTED ERROR", fg="red", bold=True)
        click.secho("=" * 80, fg="red")
        click.echo()
        click.secho(f"Error: {str(e)}", fg="red")
        if verbose:
            click.echo()
            click.secho("Stack trace:", fg="yellow")
            import traceback

            click.echo(traceback.format_exc())
        click.echo()
        sys.exit(1)


if __name__ == "__main__":
    cli()
