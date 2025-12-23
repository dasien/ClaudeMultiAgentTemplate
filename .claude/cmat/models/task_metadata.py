"""
TaskMetadata model for CMAT task tracking.

Stores integration links, workflow context, execution details, and cost information
associated with a task.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TaskMetadata:
    """
    Metadata associated with a task, including integration links and cost tracking.
    """
    # Integration links
    github_issue: Optional[str] = None
    github_pr: Optional[str] = None
    jira_ticket: Optional[str] = None
    confluence_page: Optional[str] = None

    # Workflow context
    parent_task_id: Optional[str] = None
    workflow_status: Optional[str] = None
    enhancement_title: Optional[str] = None
    workflow_name: Optional[str] = None
    workflow_step: Optional[str] = None

    # Execution context
    process_pid: Optional[str] = None
    session_id: Optional[str] = None

    # Model selection
    requested_model: Optional[str] = None  # Model requested for this task execution

    # Cost tracking
    cost_input_tokens: Optional[str] = None
    cost_output_tokens: Optional[str] = None
    cost_cache_creation_tokens: Optional[str] = None
    cost_cache_read_tokens: Optional[str] = None
    cost_usd: Optional[str] = None
    cost_model: Optional[str] = None

    # Learnings tracking (RAG system)
    learnings_retrieved: list[str] = field(default_factory=list)  # IDs of learnings used in prompt
    learnings_created: list[str] = field(default_factory=list)    # IDs of learnings extracted from output

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "github_issue": self.github_issue,
            "github_pr": self.github_pr,
            "jira_ticket": self.jira_ticket,
            "confluence_page": self.confluence_page,
            "parent_task_id": self.parent_task_id,
            "workflow_status": self.workflow_status,
            "enhancement_title": self.enhancement_title,
            "workflow_name": self.workflow_name,
            "workflow_step": self.workflow_step,
            "process_pid": self.process_pid,
            "session_id": self.session_id,
            "requested_model": self.requested_model,
            "cost_input_tokens": self.cost_input_tokens,
            "cost_output_tokens": self.cost_output_tokens,
            "cost_cache_creation_tokens": self.cost_cache_creation_tokens,
            "cost_cache_read_tokens": self.cost_cache_read_tokens,
            "cost_usd": self.cost_usd,
            "cost_model": self.cost_model,
            "learnings_retrieved": self.learnings_retrieved,
            "learnings_created": self.learnings_created,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TaskMetadata":
        """Create TaskMetadata from dictionary."""
        return cls(
            github_issue=data.get("github_issue"),
            github_pr=data.get("github_pr"),
            jira_ticket=data.get("jira_ticket"),
            confluence_page=data.get("confluence_page"),
            parent_task_id=data.get("parent_task_id"),
            workflow_status=data.get("workflow_status"),
            enhancement_title=data.get("enhancement_title"),
            workflow_name=data.get("workflow_name"),
            workflow_step=data.get("workflow_step"),
            process_pid=data.get("process_pid"),
            session_id=data.get("session_id"),
            requested_model=data.get("requested_model"),
            cost_input_tokens=data.get("cost_input_tokens"),
            cost_output_tokens=data.get("cost_output_tokens"),
            cost_cache_creation_tokens=data.get("cost_cache_creation_tokens"),
            cost_cache_read_tokens=data.get("cost_cache_read_tokens"),
            cost_usd=data.get("cost_usd"),
            cost_model=data.get("cost_model"),
            learnings_retrieved=data.get("learnings_retrieved", []),
            learnings_created=data.get("learnings_created", []),
        )