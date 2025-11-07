"""
Interactive CLI for Infrastructure Orchestrator using MAF.

This provides a conversational interface for infrastructure provisioning,
replacing the single-command approach of the original cli.py.

Usage:
    python cli_maf.py
"""

import asyncio
import sys

from orchestrator.orchestrator_agent import InfrastructureOrchestrator


async def main():
    """Run the interactive orchestrator CLI."""
    print("=" * 70)
    print("Infrastructure Orchestrator - Conversational Interface")
    print("=" * 70)
    print()
    print("I'll help you provision cloud infrastructure through natural conversation.")
    print("Tell me what you need, and I'll guide you through the process.")
    print()
    print("Commands: 'exit' or 'quit' to end, 'reset' to start over")
    print("=" * 70)
    print()

    # Initialize orchestrator
    orchestrator = InfrastructureOrchestrator()

    # Start conversation loop
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ["exit", "quit"]:
                print("\n👋 Goodbye!")
                break

            if user_input.lower() == "reset":
                orchestrator.reset()
                print("\n🔄 Conversation reset. Let's start fresh!\n")
                continue

            # Process message with orchestrator
            print()  # Blank line for readability
            response = await orchestrator.process_message(user_input)

            # Display response
            print(f"Orchestrator: {response}")
            print()  # Blank line for readability

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Let's try again...\n")


if __name__ == "__main__":
    asyncio.run(main())
