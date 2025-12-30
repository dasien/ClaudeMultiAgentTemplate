"""
Agent service for CMAT agent management.

Handles loading, listing, and managing agent configurations.
"""

import json
import re
from pathlib import Path
from typing import Optional

import yaml

from core.models.agent import Agent
from core.utils import log_operation, log_error, find_project_root


class AgentService:
    """
    Manages agent configurations for CMAT workflows.

    Provides operations for loading agents, listing available agents,
    and accessing agent definitions.
    """

    def __init__(self, agents_dir: Optional[str] = None):
        # Resolve path relative to project root, not cwd
        if agents_dir is None:
            project_root = find_project_root()
            if project_root:
                self.agents_dir = project_root / ".claude/agents"
            else:
                self.agents_dir = Path(".claude/agents")
        else:
            self.agents_dir = Path(agents_dir)

        self.agents_file = self.agents_dir / "agents.json"

    def _load_agents(self) -> dict[str, Agent]:
        """Load all agents from agents.json."""
        if not self.agents_file.exists():
            return {}

        with open(self.agents_file, 'r') as f:
            data = json.load(f)

        agents = {}
        for agent_data in data.get("agents", []):
            agent = Agent.from_dict(agent_data)
            agents[agent.agent_file] = agent

        return agents

    def _save_agents(self, agents: dict[str, Agent]) -> None:
        """Save all agents to agents.json."""
        data = {
            "agents": [agent.to_dict() for agent in agents.values()]
        }

        self.agents_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.agents_file, 'w') as f:
            json.dump(data, f, indent=2)

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

    def generate_agents_json(self, skip_templates: bool = True) -> dict:
        """
        Generate agents.json by parsing frontmatter from agent markdown files.

        Scans all .md files in the agents directory, extracts YAML frontmatter,
        and builds the agents.json registry.

        Args:
            skip_templates: If True, skip files named *TEMPLATE*.md (default: True)

        Returns:
            Dict with "generated": count, "errors": list of error messages
        """
        agents = {}
        errors = []

        if not self.agents_dir.exists():
            return {"generated": 0, "errors": ["Agents directory not found"]}

        # Find all markdown files
        md_files = list(self.agents_dir.glob("*.md"))

        for md_file in md_files:
            # Skip templates if configured
            if skip_templates and "TEMPLATE" in md_file.name.upper():
                continue

            agent_file = md_file.stem  # filename without .md

            try:
                content = md_file.read_text()

                # Extract frontmatter
                frontmatter = self._extract_frontmatter(content)
                if not frontmatter:
                    errors.append(f"{md_file.name}: No valid frontmatter found")
                    continue

                # Validate required fields
                required_fields = ["name", "role", "description"]
                missing = [f for f in required_fields if f not in frontmatter]
                if missing:
                    errors.append(f"{md_file.name}: Missing required fields: {missing}")
                    continue

                # Create agent from frontmatter
                agent = Agent(
                    name=frontmatter.get("name", ""),
                    agent_file=agent_file,
                    role=frontmatter.get("role", ""),
                    description=frontmatter.get("description", ""),
                    tools=frontmatter.get("tools", []),
                    skills=frontmatter.get("skills", []),
                )

                agents[agent_file] = agent

            except Exception as e:
                errors.append(f"{md_file.name}: Error parsing - {e}")

        # Save the generated agents
        self._save_agents(agents)

        log_operation(
            "AGENTS_GENERATED",
            f"Generated {len(agents)} agents from markdown files"
        )

        return {
            "generated": len(agents),
            "errors": errors,
        }

    def _extract_frontmatter(self, content: str) -> Optional[dict]:
        """
        Extract YAML frontmatter from markdown content.

        Expects format:
        ---
        key: value
        ---
        Content...

        Returns parsed dict or None if no valid frontmatter.
        """
        # Match frontmatter block
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return None

        frontmatter_text = match.group(1)

        try:
            return yaml.safe_load(frontmatter_text)
        except yaml.YAMLError:
            return None