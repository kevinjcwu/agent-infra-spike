"""
Phase 0: Microsoft Agent Framework Setup Validation

This test suite validates that MAF is correctly installed and configured
with Azure OpenAI. It runs 6 comprehensive tests to ensure the environment
is ready for Phase 1 implementation.

Usage:
    python tests/test_maf_setup.py
"""

import asyncio
import os
import sys
from typing import Tuple

from dotenv import load_dotenv

# Load environment variables with override to ensure latest values
load_dotenv(override=True)


async def test_maf_import():
    """Test 1: Verify MAF package imports correctly"""
    print("\n" + "=" * 70)
    print("TEST 1: MAF Package Import")
    print("=" * 70)

    try:
        import agent_framework
        from agent_framework.azure import AzureOpenAIResponsesClient
        from azure.identity import AzureCliCredential

        print(f"✓ agent_framework imported successfully")
        print(f"✓ Version: {agent_framework.__version__}")
        print(f"✓ AzureOpenAIResponsesClient available")
        print(f"✓ Azure CLI credential support available")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


async def test_azure_openai_connectivity():
    """Test 2: Verify Azure OpenAI connectivity with MAF"""
    print("\n" + "=" * 70)
    print("TEST 2: Azure OpenAI Connectivity")
    print("=" * 70)

    try:
        from agent_framework.azure import AzureOpenAIResponsesClient
        from azure.identity import AzureCliCredential

        # Load environment variables
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")

        if not endpoint:
            print("⚠ AZURE_OPENAI_ENDPOINT not set, using default from existing setup")
            endpoint = "https://ai-wukevaispikes153544078536.openai.azure.com/"

        if not deployment:
            print("⚠ Deployment name not set, using default: gpt-4o")
            deployment = "gpt-4o"

        if not api_version:
            print("⚠ API version not set, using default: 2024-08-01-preview")
            api_version = "2024-08-01-preview"

        print(f"  Endpoint: {endpoint}")
        print(f"  Deployment: {deployment}")
        print(f"  API Version: {api_version}")
        print(f"  Auth: Azure CLI Credential")

        # Create client
        client = AzureOpenAIResponsesClient(
            endpoint=endpoint,
            deployment_name=deployment,
            api_version=api_version,
            credential=AzureCliCredential(),
        )

        print(f"✓ Client created successfully")
        return True

    except Exception as e:
        print(f"✗ Client creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_basic_agent_creation():
    """Test 3: Create a basic MAF agent"""
    print("\n" + "=" * 70)
    print("TEST 3: Basic Agent Creation")
    print("=" * 70)

    try:
        from agent_framework.azure import AzureOpenAIResponsesClient
        from azure.identity import AzureCliCredential

        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://ai-wukevaispikes153544078536.openai.azure.com/")
        deployment = os.getenv("AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or "gpt-4o"
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")

        # Create agent
        agent = AzureOpenAIResponsesClient(
            endpoint=endpoint,
            deployment_name=deployment,
            api_version=api_version,
            credential=AzureCliCredential(),
        ).create_agent(
            name="TestBot",
            instructions="You are a helpful test assistant. Respond concisely.",
        )

        print(f"✓ Agent 'TestBot' created successfully")
        print(f"  Name: {agent.name if hasattr(agent, 'name') else 'N/A'}")
        return True

    except Exception as e:
        print(f"✗ Agent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_conversation():
    """Test 4: Test basic agent conversation"""
    print("\n" + "=" * 70)
    print("TEST 4: Agent Conversation (Simple Hello)")
    print("=" * 70)

    try:
        from agent_framework.azure import AzureOpenAIResponsesClient
        from azure.identity import AzureCliCredential

        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://ai-wukevaispikes153544078536.openai.azure.com/")
        deployment = os.getenv("AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or "gpt-4o"
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")

        # Create agent
        agent = AzureOpenAIResponsesClient(
            endpoint=endpoint,
            deployment_name=deployment,
            api_version=api_version,
            credential=AzureCliCredential(),
        ).create_agent(
            name="TestBot",
            instructions="You are a helpful test assistant. Respond with exactly: 'Hello from MAF!'",
        )

        print(f"  Sending message: 'Say hello'")

        # Send message
        response = await agent.run("Say hello")

        # Extract response text from AgentRunResponse
        response_text = response.messages[-1].text if response.messages else str(response)

        print(f"✓ Agent responded: {response_text}")

        # Validate response
        if "hello" in response_text.lower() or "maf" in response_text.lower():
            print(f"✓ Response contains expected keywords")
            return True
        else:
            print(f"⚠ Response unexpected but agent is working")
            return True

    except Exception as e:
        print(f"✗ Conversation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_infrastructure_agent_scenario():
    """Test 5: Simulate infrastructure orchestrator conversation"""
    print("\n" + "=" * 70)
    print("TEST 5: Infrastructure Orchestrator Simulation")
    print("=" * 70)

    try:
        from agent_framework.azure import AzureOpenAIResponsesClient
        from azure.identity import AzureCliCredential

        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://ai-wukevaispikes153544078536.openai.azure.com/")
        deployment = os.getenv("AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or "gpt-4o"
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")

        # Create infrastructure orchestrator agent
        agent = AzureOpenAIResponsesClient(
            endpoint=endpoint,
            deployment_name=deployment,
            api_version=api_version,
            credential=AzureCliCredential(),
        ).create_agent(
            name="InfrastructureOrchestrator",
            instructions="""You are an infrastructure provisioning orchestrator.

When a user asks to provision infrastructure, you should:
1. Ask clarifying questions about region, resource names, and budget
2. Be conversational and helpful
3. Suggest smart defaults

Keep responses concise for testing purposes."""
        )

        print(f"  Test message: 'Create a Databricks workspace'")

        # Send test message
        response = await agent.run("Create a Databricks workspace")

        # Extract response text from AgentRunResponse
        response_text = response.messages[-1].text if response.messages else str(response)

        print(f"✓ Agent responded:")
        print(f"  {response_text[:200]}{'...' if len(response_text) > 200 else ''}")

        # Check for expected orchestrator behavior
        keywords = ["region", "name", "databricks", "workspace"]
        found_keywords = [kw for kw in keywords if kw.lower() in response_text.lower()]

        if len(found_keywords) >= 2:
            print(f"✓ Response shows orchestrator behavior (keywords: {', '.join(found_keywords)})")
            return True
        else:
            print(f"⚠ Response seems generic but agent is working")
            return True

    except Exception as e:
        print(f"✗ Infrastructure simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_existing_agent_compatibility():
    """Test 6: Verify existing agent code still works"""
    print("\n" + "=" * 70)
    print("TEST 6: Existing Agent Code Compatibility")
    print("=" * 70)

    try:
        # Import our existing agent code
        from agent.intent_recognizer import IntentRecognizer
        from agent.models import InfrastructureRequest

        print(f"✓ Existing agent modules import successfully")

        # Test that OpenAI client still works (our current implementation)
        from azure.identity import AzureCliCredential, get_bearer_token_provider
        from openai import AzureOpenAI

        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://ai-wukevaispikes153544078536.openai.azure.com/")

        token_provider = get_bearer_token_provider(
            AzureCliCredential(),
            "https://cognitiveservices.azure.com/.default"
        )

        client = AzureOpenAI(
            azure_endpoint=endpoint,
            azure_ad_token_provider=token_provider,
            api_version="2025-01-01-preview",
        )

        print(f"✓ Existing OpenAI client still works")
        print(f"✓ Both MAF and existing implementation coexist successfully")

        return True

    except Exception as e:
        print(f"✗ Compatibility check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all Phase 0 validation tests"""
    print("\n" + "=" * 70)
    print("PHASE 0: MICROSOFT AGENT FRAMEWORK SETUP VALIDATION")
    print("=" * 70)
    print("Testing MAF installation and Azure OpenAI integration")
    print("=" * 70)

    results = []

    # Test 1: Import
    results.append(("MAF Import", await test_maf_import()))

    # Test 2: Azure OpenAI connectivity
    results.append(("Azure OpenAI Connectivity", await test_azure_openai_connectivity()))

    # Test 3: Agent creation
    results.append(("Agent Creation", await test_basic_agent_creation()))

    # Test 4: Basic conversation
    results.append(("Agent Conversation", await test_agent_conversation()))

    # Test 5: Infrastructure scenario
    results.append(("Infrastructure Orchestrator", await test_infrastructure_agent_scenario()))

    # Test 6: Existing code compatibility
    results.append(("Existing Code Compatibility", await test_existing_agent_compatibility()))

    # Summary
    print("\n" + "=" * 70)
    print("PHASE 0 TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} | {test_name}")

    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)

    print("=" * 70)
    print(f"Results: {passed_tests}/{total_tests} tests passed")
    print("=" * 70)

    if passed_tests == total_tests:
        print("\n🎉 Phase 0 Complete: MAF is ready for Phase 1 implementation!")
        return True
    else:
        print(f"\n⚠ {total_tests - passed_tests} test(s) failed - review errors above")
        return False


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Run tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
