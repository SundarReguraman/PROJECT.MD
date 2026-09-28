"""The multi-agent pre-flight swarm: five specialists plus an orchestrator."""

from project_md.agents.architecture_agent import ArchitectureAgent
from project_md.agents.base_agent import BaseAgent
from project_md.agents.contract_agent import ContractAgent
from project_md.agents.dependency_agent import DependencyAgent
from project_md.agents.impact_agent import ImpactAgent
from project_md.agents.security_agent import SecurityAgent


def default_agents():
    """One fresh instance of each specialist, in report order."""
    return [DependencyAgent(), ArchitectureAgent(), ContractAgent(), ImpactAgent(), SecurityAgent()]


__all__ = [
    "ArchitectureAgent",
    "BaseAgent",
    "ContractAgent",
    "DependencyAgent",
    "ImpactAgent",
    "SecurityAgent",
    "default_agents",
]
