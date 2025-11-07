"""
Orchestrator module for multi-capability infrastructure provisioning.

This module provides the MAF-based orchestrator that:
- Engages in multi-turn conversations with users
- Discovers required infrastructure capabilities
- Proposes smart naming defaults
- Validates plans before execution
- Routes to appropriate capability implementations
"""

from orchestrator.orchestrator_agent import InfrastructureOrchestrator

__all__ = ["InfrastructureOrchestrator"]
