"""
Dialog windows for the Task Queue Manager v3.0.
Enhanced with Skills, Workflows, and Integration features.
"""

# Dialogs
from .connect import ConnectDialog
from .log_viewer import LogViewerDialog
from .about import AboutDialog
from .agent_list import AgentListDialog
from .skills_list import SkillsViewerDialog
from .task_details import TaskDetailsDialog
from .task_create import CreateTaskDialog
from .agent_details import AgentDetailsDialog
from .integration_dashboard import IntegrationDashboardDialog
from .enhancement_create import CreateEnhancementDialog
from .working import WorkingDialog
from .claude_settings import ClaudeSettingsDialog
from .workflow_template_manager import WorkflowTemplateManagerDialog
from .workflow_template_editor import WorkflowTemplateEditorDialog
from .workflow_launcher import WorkflowLauncherDialog
from .documentation_viewer import DocumentationViewerDialog

__all__ = [
    'ConnectDialog',
    'LogViewerDialog',
    'AboutDialog',
    'AgentListDialog',
    'SkillsViewerDialog',
    'TaskDetailsDialog',
    'CreateTaskDialog',
    'AgentDetailsDialog',
    'IntegrationDashboardDialog',
    'CreateEnhancementDialog',
    'WorkingDialog',
    'ClaudeSettingsDialog',
    'WorkflowTemplateManagerDialog',
    'WorkflowTemplateEditorDialog',
    'WorkflowLauncherDialog',
    'DocumentationViewerDialog',
]