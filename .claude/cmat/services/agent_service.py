"""
Agent service for CMAT agent management.

Handles loading, listing, and managing agent configurations.
"""

import json
from pathlib import Path
from typing import Optional

from cmat.models.agent import Agent


class AgentService:
    """
    Manages agent configurations for CMAT workflows.

    Provides operations for loading agents, listing available agents,
    and accessing agent definitions.
    """

    def __init__(self, agents_dir: str = ".claude/agents"):
        self.agents_dir = Path(agents_dir)
        self.agents_file = self.agents_dir / "agents.json"
        self._agents_cache: Optional[dict[str, Agent]] = None

    def _load_agents(self) -> dict[str, Agent]:
        """Load all agents from agents.json."""
        if self._agents_cache is not None:
            return self._agents_cache

        if not self.agents_file.exists():
            return {}

        with open(self.agents_file, 'r') as f:
            data = json.load(f)

        agents = {}
        for agent_data in data.get("agents", []):
            agent = Agent.from_dict(agent_data)
            agents[agent.agent_file] = agent

        self._agents_cache = agents
        return agents

    def _save_agents(self, agents: dict[str, Agent]) -> None:
        """Save all agents to agents.json."""
        data = {
            "agents": [agent.to_dict() for agent in agents.values()]
        }

        self.agents_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.agents_file, 'w') as f:
            json.dump(data, f, indent=2)

        self._agents_cache = agents

    def invalidate_cache(self) -> None:
        """Invalidate the agents cache to force reload."""
        self._agents_cache = None

    def list_all(self) -> list[Agent]:
        """List all available agents."""
        return list(self._load_agents().values())

    def get(self, agent_file: str) -> Optional[Agent]:
        """Get an agent by its file name (without .md extension)."""
        return self._load_agents().get(agent_file)

    def get_by_name(self, name: str) -> Optional[Agent]:
        """Get an agent by its display name."""
        for agent in self._load_agents().values():
            if agent.name == name:
                return agent
        return None

    def get_by_role(self, role: str) -> list[Agent]:
        """Get all agents with a specific role."""
        return [a for a in self._load_agents().values() if a.role == role]

    def add(self, agent: Agent) -> Agent:
        """Add a new agent to the registry."""
        agents = self._load_agents()
        agents[agent.agent_file] = agent
        self._save_agents(agents)
        return agent

    def update(self, agent: Agent) -> Optional[Agent]:
        """Update an existing agent."""
        agents = self._load_agents()
        if agent.agent_file not in agents:
            return None

        agents[agent.agent_file] = agent
        self._save_agents(agents)
        return agent

    def delete(self, agent_file: str) -> bool:
        """Delete an agent from the registry."""
        agents = self._load_agents()
        if agent_file not in agents:
            return False

        del agents[agent_file]
        self._save_agents(agents)
        return True

    def get_agent_prompt(self, agent_file: str) -> Optional[str]:
        """Load the full agent prompt from its markdown file."""
        agent = self.get(agent_file)
        if not agent:
            return None

        prompt_file = self.agents_dir / f"{agent_file}.md"
        if not prompt_file.exists():
            return None

        return prompt_file.read_text()

    def get_agents_with_skill(self, skill_name: str) -> list[Agent]:
        """Get all agents that have a specific skill."""
        return [a for a in self._load_agents().values() if a.has_skill(skill_name)]

    def get_agents_with_tool(self, tool_name: str) -> list[Agent]:
        """Get all agents that have access to a specific tool."""
        return [a for a in self._load_agents().values() if a.has_tool(tool_name)]

    def validate_agent(self, agent: Agent) -> list[str]:
        """
        Validate an agent configuration.

        Returns a list of validation errors (empty if valid).
        """
        errors = []

        if not agent.name:
            errors.append("Agent name is required")

        if not agent.agent_file:
            errors.append("Agent file name is required")

        if not agent.role:
            errors.append("Agent role is required")

        if not agent.description:
            errors.append("Agent description is required")

        # Check if markdown file exists
        prompt_file = self.agents_dir / f"{agent.agent_file}.md"
        if not prompt_file.exists():
            errors.append(f"Agent prompt file not found: {prompt_file}")

        return errors