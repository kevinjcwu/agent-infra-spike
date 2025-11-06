"""
Simple Azure Responses Agent Example - Haiku Generator

This example demonstrates the Microsoft Agent Framework with Azure OpenAI
to create a poetry-writing agent.

Usage:
    python haiku_example.py
"""

import asyncio
import os

from agent_framework.azure import AzureOpenAIResponsesClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)


async def main():
    """Create a haiku-writing agent using Azure OpenAI Responses API."""

    print("=" * 70)
    print("Microsoft Agent Framework - Haiku Generator")
    print("=" * 70)
    print()

    # Initialize Azure OpenAI Responses client
    # Credentials loaded from .env file
    agent = AzureOpenAIResponsesClient(
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
    ).create_agent(
        name="HaikuBot",
        instructions="You are an upbeat assistant that writes beautifully. Write haikus with 5-7-5 syllable structure.",
    )

    print("🤖 Agent: HaikuBot")
    print("📝 Task: Write a haiku about Microsoft Agent Framework")
    print()

    # Run the agent
    response = await agent.run("Write a haiku about Microsoft Agent Framework.")

    print("🎨 Result:")
    print("-" * 70)
    print(response)
    print("-" * 70)
    print()
    print("✓ Complete!")


if __name__ == "__main__":
    asyncio.run(main())
