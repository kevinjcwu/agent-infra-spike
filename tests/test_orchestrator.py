"""
Tests for Phase 1: Conversational Orchestrator

Validates that the MAF-based orchestrator correctly:
- Engages in multi-turn conversations
- Asks clarifying questions
- Maintains conversation context
- Calls tools when appropriate
"""

import asyncio
import json

import pytest

from orchestrator.orchestrator_agent import InfrastructureOrchestrator
from orchestrator.tools import (
    estimate_cost,
    select_capabilities,
    suggest_naming,
)


def test_tools_capability_selection():
    """Test capability selection tool validates against registry."""
    # Valid capability selection
    result = json.loads(select_capabilities(
        capabilities=["provision_databricks"],
        rationale="ML training requires compute platform"
    ))
    assert result["status"] == "success"
    assert result["count"] == 1
    assert result["capabilities"][0]["name"] == "provision_databricks"

    # Test single valid capability (spike only has Databricks)
    result = json.loads(select_capabilities(
        capabilities=["provision_databricks"],
        rationale="Need compute for data engineering"
    ))
    assert result["status"] == "success"
    assert result["count"] == 1

    # Invalid capability (hallucination prevention)
    result = json.loads(select_capabilities(
        capabilities=["provision_azure_ml"],  # Not in registry!
        rationale="Want ML platform"
    ))
    assert result["status"] == "error"
    assert "provision_azure_ml" in result["errors"][0]
    assert "valid_capabilities" in result


def test_tools_naming_suggestions():
    """Test naming suggestion tool generates Azure-compliant names."""
    result = json.loads(suggest_naming("ml-team", "prod", "resource_group"))

    assert result["primary"] == "rg-ml-team-prod"
    assert len(result["alternatives"]) > 0
    assert result["pattern_info"]["follows_azure_conventions"] is True


def test_tools_cost_estimation():
    """Test cost estimation tool calculates reasonable costs."""
    # Databricks without GPU
    result = json.loads(
        estimate_cost(
            capability="provision_databricks",
            enable_gpu=False,
            workload_type="data_engineering"
        )
    )

    assert result["monthly_estimate"] > 0
    assert result["currency"] == "USD"
    assert len(result["breakdown"]) >= 2

    # Databricks with GPU (should be more expensive)
    result_gpu = json.loads(
        estimate_cost(
            capability="provision_databricks",
            enable_gpu=True,
            workload_type="ml"
        )
    )

    assert result_gpu["monthly_estimate"] > result["monthly_estimate"]


@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test orchestrator initializes correctly."""
    orchestrator = InfrastructureOrchestrator()

    assert orchestrator.agent is not None
    assert orchestrator.state.messages_count == 0
    assert orchestrator.current_plan is None


@pytest.mark.asyncio
async def test_orchestrator_basic_conversation():
    """Test orchestrator can handle a basic conversation."""
    orchestrator = InfrastructureOrchestrator()

    # Initial request
    response = await orchestrator.process_message("I need a Databricks workspace")

    assert isinstance(response, str)
    assert len(response) > 0
    assert orchestrator.state.messages_count == 1


@pytest.mark.asyncio
async def test_orchestrator_multi_turn_conversation():
    """Test orchestrator maintains context across multiple turns."""
    orchestrator = InfrastructureOrchestrator()

    # Simulate a full conversation
    messages = [
        "I need a Databricks workspace for ML team",
        "The team is ml-research",
        "This is for production",
        "East US region please",
    ]

    responses = []
    for msg in messages:
        response = await orchestrator.process_message(msg)
        responses.append(response)

    # Verify conversation progressed
    assert orchestrator.state.messages_count == len(messages)
    assert all(len(r) > 0 for r in responses)

    # Verify agent asks follow-up questions (characteristic of good conversation)
    # At least one response should contain a question mark
    assert any("?" in r for r in responses)


@pytest.mark.asyncio
async def test_orchestrator_reset():
    """Test orchestrator can reset conversation state."""
    orchestrator = InfrastructureOrchestrator()

    # Have a conversation
    await orchestrator.process_message("I need a Databricks workspace")
    await orchestrator.process_message("ML team")

    assert orchestrator.state.messages_count == 2

    # Reset
    orchestrator.reset()

    assert orchestrator.state.messages_count == 0
    assert orchestrator.current_plan is None


@pytest.mark.asyncio
async def test_orchestrator_handles_different_requests():
    """Test orchestrator recognizes different infrastructure types."""
    orchestrator = InfrastructureOrchestrator()

    # Databricks
    response1 = await orchestrator.process_message("I need Databricks")
    assert "databricks" in response1.lower() or "workspace" in response1.lower()

    # New orchestrator for clean state
    orchestrator = InfrastructureOrchestrator()

    # OpenAI (future capability)
    response2 = await orchestrator.process_message("I need Azure OpenAI")
    assert len(response2) > 0  # Should still respond even if not implemented


def test_orchestrator_tools_available():
    """Test that all expected tools are available."""
    from orchestrator import tools

    assert hasattr(tools, "select_capabilities")
    assert hasattr(tools, "suggest_naming")
    assert hasattr(tools, "estimate_cost")


# Manual test runner for quick validation
async def run_manual_test():
    """
    Manual test for interactive validation.

    Run this directly to see conversation flow:
        python -m pytest tests/test_orchestrator.py::run_manual_test -v -s
    """
    print("\n" + "=" * 70)
    print("MANUAL TEST: Multi-Turn Conversation")
    print("=" * 70 + "\n")

    orchestrator = InfrastructureOrchestrator()

    conversation = [
        ("I need a Databricks workspace for machine learning", "Initial request"),
        ("The team is ml-research", "Team name"),
        ("This is for production environment", "Environment"),
        ("East US region", "Region selection"),
        ("Yes, that name looks good", "Confirm naming"),
    ]

    for i, (message, description) in enumerate(conversation, 1):
        print(f"Turn {i}: {description}")
        print(f"User: {message}")
        response = await orchestrator.process_message(message)
        print(f"Orchestrator: {response[:200]}..." if len(response) > 200 else f"Orchestrator: {response}")
        print("-" * 70 + "\n")

    print(f"Total messages: {orchestrator.state.messages_count}")
    print("\n✅ Manual test complete!\n")


if __name__ == "__main__":
    # Run manual test
    asyncio.run(run_manual_test())
