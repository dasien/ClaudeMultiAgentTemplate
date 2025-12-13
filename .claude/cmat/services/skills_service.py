"""
Skills service for CMAT skill management.

Handles loading, listing, and managing skill configurations.
"""

import json
from pathlib import Path
from typing import Optional

from cmat.models.skill import Skill


class SkillsService:
    """
    Manages skill configurations for CMAT agents.

    Provides operations for loading skills, listing available skills,
    and accessing skill definitions.
    """

    def __init__(self, skills_dir: str = ".claude/skills"):
        self.skills_dir = Path(skills_dir)
        self.skills_file = self.skills_dir / "skills.json"
        self._skills_cache: Optional[dict[str, Skill]] = None

    def _load_skills(self) -> dict[str, Skill]:
        """Load all skills from skills.json."""
        if self._skills_cache is not None:
            return self._skills_cache

        if not self.skills_file.exists():
            return {}

        with open(self.skills_file, 'r') as f:
            data = json.load(f)

        skills = {}
        for skill_data in data.get("skills", []):
            skill = Skill.from_dict(skill_data)
            skills[skill.skill_directory] = skill

        self._skills_cache = skills
        return skills

    def _save_skills(self, skills: dict[str, Skill]) -> None:
        """Save all skills to skills.json."""
        data = {
            "version": "1.0.0",
            "skills": [skill.to_dict() for skill in skills.values()]
        }

        self.skills_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.skills_file, 'w') as f:
            json.dump(data, f, indent=2)

        self._skills_cache = skills

    def invalidate_cache(self) -> None:
        """Invalidate the skills cache to force reload."""
        self._skills_cache = None

    def list_all(self) -> list[Skill]:
        """List all available skills."""
        return list(self._load_skills().values())

    def get(self, skill_directory: str) -> Optional[Skill]:
        """Get a skill by its directory name."""
        return self._load_skills().get(skill_directory)

    def get_by_name(self, name: str) -> Optional[Skill]:
        """Get a skill by its display name."""
        for skill in self._load_skills().values():
            if skill.name == name:
                return skill
        return None

    def get_by_category(self, category: str) -> list[Skill]:
        """Get all skills in a specific category."""
        return [s for s in self._load_skills().values() if s.category == category]

    def list_categories(self) -> list[str]:
        """List all unique skill categories."""
        categories = set()
        for skill in self._load_skills().values():
            categories.add(skill.category)
        return sorted(categories)

    def add(self, skill: Skill) -> Skill:
        """Add a new skill to the registry."""
        skills = self._load_skills()
        skills[skill.skill_directory] = skill
        self._save_skills(skills)
        return skill

    def update(self, skill: Skill) -> Optional[Skill]:
        """Update an existing skill."""
        skills = self._load_skills()
        if skill.skill_directory not in skills:
            return None

        skills[skill.skill_directory] = skill
        self._save_skills(skills)
        return skill

    def delete(self, skill_directory: str) -> bool:
        """Delete a skill from the registry."""
        skills = self._load_skills()
        if skill_directory not in skills:
            return False

        del skills[skill_directory]
        self._save_skills(skills)
        return True

    def get_skill_content(self, skill_directory: str) -> Optional[str]:
        """Load the full skill content from its markdown file."""
        skill = self.get(skill_directory)
        if not skill:
            return None

        skill_file = self.skills_dir / skill_directory / "SKILL.md"
        if not skill_file.exists():
            return None

        return skill_file.read_text()

    def get_skills_for_agent(self, skill_names: list[str]) -> list[Skill]:
        """Get all skills assigned to an agent by skill directory names."""
        skills = []
        for name in skill_names:
            skill = self.get(name)
            if skill:
                skills.append(skill)
        return skills

    def get_combined_skill_content(self, skill_names: list[str]) -> str:
        """Get combined content of multiple skills for prompt injection."""
        contents = []
        for name in skill_names:
            content = self.get_skill_content(name)
            if content:
                contents.append(f"## Skill: {name}\n\n{content}")
        return "\n\n---\n\n".join(contents)

    def build_skills_prompt(self, skill_names: list[str]) -> str:
        """
        Build a formatted skills prompt section for agent invocation.

        Matches the bash formatting from skills-commands.sh.
        Returns empty string if no skills found.
        """
        if not skill_names:
            return ""

        skills_content = []
        for name in skill_names:
            content = self.get_skill_content(name)
            if content:
                skills_content.append(f"---\n{content}\n---")

        if not skills_content:
            return ""

        # Build formatted section matching bash output
        header = """
################################################################################
## SPECIALIZED SKILLS AVAILABLE
################################################################################

You have access to the following specialized skills. Apply them when they are
relevant to the task at hand.

"""
        footer = """

**Using Skills**: Apply the above skills when they are relevant to your task.
Focus on the skills that directly support what you need to accomplish.

################################################################################
"""

        return header + "\n\n".join(skills_content) + footer

    def validate_skill(self, skill: Skill) -> list[str]:
        """
        Validate a skill configuration.

        Returns a list of validation errors (empty if valid).
        """
        errors = []

        if not skill.name:
            errors.append("Skill name is required")

        if not skill.skill_directory:
            errors.append("Skill directory is required")

        if not skill.category:
            errors.append("Skill category is required")

        if not skill.description:
            errors.append("Skill description is required")

        # Check if skill directory and file exist
        skill_path = self.skills_dir / skill.skill_directory
        if not skill_path.exists():
            errors.append(f"Skill directory not found: {skill_path}")
        else:
            skill_file = skill_path / "SKILL.md"
            if not skill_file.exists():
                errors.append(f"Skill file not found: {skill_file}")

        return errors