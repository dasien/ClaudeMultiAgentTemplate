"""
CMAT CLI entry point.

Usage:
    python -m cmat <command> [options]

Commands:
    workflow start <name> <enhancement>   Start a workflow
    workflow list                         List all workflows
    workflow show <name>                  Show workflow details
    workflow validate <name>              Validate a workflow template
    workflow add <id> <name> <desc>       Create a new workflow
    workflow remove <id>                  Delete a workflow
    workflow update <id> [--name] [--description]
    workflow add-step <wf> <agent> <in> <out> [--model] [--index]
    workflow remove-step <wf> <index>     Remove a step
    workflow update-step <wf> <index> [--agent] [--input] [--output] [--model]
    workflow add-transition <wf> <step> <status> [--next-step] [--no-auto-chain]
    workflow remove-transition <wf> <step> <status>

    queue status                          Show queue status
    queue list [pending|active|completed|failed|all]
    queue add <agent> <title> <source> [--auto-chain]
    queue start <task_id>                 Start a pending task
    queue complete <task_id> <result>     Mark task as completed
    queue fail <task_id> <reason>         Mark task as failed
    queue cancel <task_id> [reason]       Cancel a task
    queue rerun <task_id>                 Re-queue a completed/failed task

    skills list                           List all skills
    skills show <name>                    Show skill details
    skills get <agent>                    Get skills for an agent

    learnings list                        List all learnings
    learnings add "<content>"             Add a manual learning
    learnings delete <id>                 Delete a learning
    learnings show <id>                   Show learning details
    learnings search "<query>"            Search learnings (uses Claude)

    agents list                           List all agents
    agents generate                       Regenerate agents.json from markdown

    models list                           List all Claude models
    models show <id>                      Show model details
    models set-default <id>               Set default model

    costs extract <task_id> <transcript_path> [session_id]
                                          Extract costs from transcript
    costs show <task_id>                  Show task cost
    costs enhancement <name>              Show enhancement total cost

    version                               Show CMAT version
"""

import sys
import json
from typing import Optional

from cmat import CMAT, __version__
from cmat.models import Learning
from cmat.models.workflow_template import WorkflowTemplate
from cmat.models.workflow_step import WorkflowStep
from cmat.models.step_transition import StepTransition


def print_error(msg: str) -> None:
    print(f"Error: {msg}", file=sys.stderr)


def print_learning(learning: Learning, verbose: bool = False) -> None:
    """Print a learning in a readable format."""
    print(f"  ID: {learning.id}")
    print(f"  Summary: {learning.summary}")
    print(f"  Tags: {', '.join(learning.tags) if learning.tags else '(none)'}")
    print(f"  Applies to: {', '.join(learning.applies_to) if learning.applies_to else '(any)'}")
    print(f"  Source: {learning.source_type}")
    print(f"  Confidence: {learning.confidence:.0%}")
    print(f"  Created: {learning.created}")
    if verbose:
        print(f"  Content:\n    {learning.content}")
    print()


def cmd_workflow(cmat: CMAT, args: list[str]) -> int:
    """Handle workflow subcommands."""
    if not args:
        print("Usage: cmat workflow <command> [options]")
        print("Commands: start, list, show, validate, add, remove, update,")
        print("          add-step, remove-step, update-step, add-transition, remove-transition")
        return 1

    subcmd = args[0]

    if subcmd == "start":
        if len(args) < 3:
            print_error("Usage: cmat workflow start <workflow_name> <enhancement_name> [--model <model_id>]")
            return 1

        workflow_name = args[1]
        enhancement_name = args[2]

        # Parse --model option
        model = None
        if "--model" in args:
            idx = args.index("--model")
            if idx + 1 < len(args):
                model = args[idx + 1]

        task_id = cmat.workflow.start_workflow(workflow_name, enhancement_name, model=model)

        if task_id:
            task = cmat.queue.get(task_id)
            print(f"Workflow started: {workflow_name}")
            print(f"Enhancement: {enhancement_name}")
            print(f"Task: {task_id}")
            if task:
                print(f"Agent: {task.assigned_agent}")
                print(f"Status: {task.status.value}")
                if model:
                    print(f"Model: {model}")
            return 0
        else:
            print_error(f"Failed to start workflow: {workflow_name}")
            return 1

    elif subcmd == "list":
        workflows = cmat.workflow.list_all()

        if not workflows:
            print("No workflows found.")
            return 0

        print(f"Available workflows ({len(workflows)}):\n")
        for wf in workflows:
            print(f"  {wf.id}")
            print(f"    Name: {wf.name}")
            print(f"    Description: {wf.description}")
            print(f"    Steps: {len(wf.steps)}")
            print()
        return 0

    elif subcmd == "show":
        if len(args) < 2:
            print_error("Usage: cmat workflow show <name>")
            return 1

        workflow_name = args[1]
        wf = cmat.workflow.get(workflow_name)

        if not wf:
            print_error(f"Workflow not found: {workflow_name}")
            return 1

        print(f"Workflow: {wf.id}")
        print(f"  Name: {wf.name}")
        print(f"  Description: {wf.description}")
        print(f"\n  Steps ({len(wf.steps)}):")

        for i, step in enumerate(wf.steps):
            print(f"\n    [{i}] {step.agent}")
            print(f"        Input: {step.input}")
            print(f"        Required Output: {step.required_output}")
            if step.on_status:
                print(f"        Status Transitions:")
                for status, transition in step.on_status.items():
                    next_step = transition.next_step or "(end)"
                    auto = "auto" if transition.auto_chain else "manual"
                    print(f"          {status} -> {next_step} ({auto})")
        return 0

    elif subcmd == "validate":
        if len(args) < 2:
            print_error("Usage: cmat workflow validate <name>")
            return 1

        workflow_name = args[1]
        wf = cmat.workflow.get(workflow_name)

        if not wf:
            print_error(f"Workflow not found: {workflow_name}")
            return 1

        errors = cmat.workflow.validate_template(wf)

        if errors:
            print(f"Validation errors for '{workflow_name}':")
            for error in errors:
                print(f"  - {error}")
            return 1
        else:
            print(f"Workflow '{workflow_name}' is valid.")
            return 0

    # === Workflow CRUD ===
    elif subcmd == "add":
        if len(args) < 4:
            print_error("Usage: cmat workflow add <id> <name> <description>")
            return 1

        workflow_id = args[1]
        name = args[2]
        description = args[3]

        # Check if workflow already exists
        if cmat.workflow.get(workflow_id):
            print_error(f"Workflow already exists: {workflow_id}")
            return 1

        template = WorkflowTemplate(
            id=workflow_id,
            name=name,
            description=description,
            steps=[],
        )

        result = cmat.workflow.add(template)
        print(f"Workflow created: {result.id}")
        print(f"  Name: {result.name}")
        print(f"  Description: {result.description}")
        print(f"  Steps: 0 (use 'workflow add-step' to add steps)")
        return 0

    elif subcmd == "remove":
        if len(args) < 2:
            print_error("Usage: cmat workflow remove <id>")
            return 1

        workflow_id = args[1]

        if cmat.workflow.delete(workflow_id):
            print(f"Workflow removed: {workflow_id}")
            return 0
        else:
            print_error(f"Workflow not found: {workflow_id}")
            return 1

    elif subcmd == "update":
        if len(args) < 2:
            print_error("Usage: cmat workflow update <id> [--name <name>] [--description <desc>]")
            return 1

        workflow_id = args[1]
        wf = cmat.workflow.get(workflow_id)

        if not wf:
            print_error(f"Workflow not found: {workflow_id}")
            return 1

        # Parse optional arguments
        if "--name" in args:
            idx = args.index("--name")
            if idx + 1 < len(args):
                wf.name = args[idx + 1]

        if "--description" in args:
            idx = args.index("--description")
            if idx + 1 < len(args):
                wf.description = args[idx + 1]

        result = cmat.workflow.update(wf)
        if result:
            print(f"Workflow updated: {result.id}")
            print(f"  Name: {result.name}")
            print(f"  Description: {result.description}")
            return 0
        else:
            print_error(f"Failed to update workflow: {workflow_id}")
            return 1

    # === Step CRUD ===
    elif subcmd == "add-step":
        if len(args) < 5:
            print_error("Usage: cmat workflow add-step <workflow_id> <agent> <input> <output> [--model <model>] [--index <n>]")
            return 1

        workflow_id = args[1]
        agent = args[2]
        input_path = args[3]
        required_output = args[4]

        # Parse optional arguments
        model = None
        if "--model" in args:
            idx = args.index("--model")
            if idx + 1 < len(args):
                model = args[idx + 1]

        index = None
        if "--index" in args:
            idx = args.index("--index")
            if idx + 1 < len(args):
                try:
                    index = int(args[idx + 1])
                except ValueError:
                    print_error("Index must be an integer")
                    return 1

        step = WorkflowStep(
            agent=agent,
            input=input_path,
            required_output=required_output,
            on_status={},
            model=model,
        )

        result = cmat.workflow.add_step(workflow_id, step, index)
        if result:
            step_idx = index if index is not None else len(result.steps) - 1
            print(f"Step added to workflow '{workflow_id}' at index {step_idx}")
            print(f"  Agent: {agent}")
            print(f"  Input: {input_path}")
            print(f"  Output: {required_output}")
            if model:
                print(f"  Model: {model}")
            return 0
        else:
            print_error(f"Failed to add step. Workflow not found: {workflow_id}")
            return 1

    elif subcmd == "remove-step":
        if len(args) < 3:
            print_error("Usage: cmat workflow remove-step <workflow_id> <step_index>")
            return 1

        workflow_id = args[1]
        try:
            step_index = int(args[2])
        except ValueError:
            print_error("Step index must be an integer")
            return 1

        result = cmat.workflow.remove_step(workflow_id, step_index)
        if result:
            print(f"Step {step_index} removed from workflow '{workflow_id}'")
            print(f"  Remaining steps: {len(result.steps)}")
            return 0
        else:
            print_error(f"Failed to remove step. Workflow or step not found.")
            return 1

    elif subcmd == "update-step":
        if len(args) < 3:
            print_error("Usage: cmat workflow update-step <workflow_id> <step_index> [--agent <a>] [--input <i>] [--output <o>] [--model <m>]")
            return 1

        workflow_id = args[1]
        try:
            step_index = int(args[2])
        except ValueError:
            print_error("Step index must be an integer")
            return 1

        wf = cmat.workflow.get(workflow_id)
        if not wf:
            print_error(f"Workflow not found: {workflow_id}")
            return 1

        if step_index < 0 or step_index >= len(wf.steps):
            print_error(f"Step index out of range: {step_index} (workflow has {len(wf.steps)} steps)")
            return 1

        step = wf.steps[step_index]

        # Parse optional arguments
        if "--agent" in args:
            idx = args.index("--agent")
            if idx + 1 < len(args):
                step.agent = args[idx + 1]

        if "--input" in args:
            idx = args.index("--input")
            if idx + 1 < len(args):
                step.input = args[idx + 1]

        if "--output" in args:
            idx = args.index("--output")
            if idx + 1 < len(args):
                step.required_output = args[idx + 1]

        if "--model" in args:
            idx = args.index("--model")
            if idx + 1 < len(args):
                step.model = args[idx + 1]

        result = cmat.workflow.update(wf)
        if result:
            print(f"Step {step_index} updated in workflow '{workflow_id}'")
            print(f"  Agent: {step.agent}")
            print(f"  Input: {step.input}")
            print(f"  Output: {step.required_output}")
            if step.model:
                print(f"  Model: {step.model}")
            return 0
        else:
            print_error(f"Failed to update step")
            return 1

    # === Transition CRUD ===
    elif subcmd == "add-transition":
        if len(args) < 4:
            print_error("Usage: cmat workflow add-transition <workflow_id> <step_index> <status> [--next-step <agent>] [--no-auto-chain] [--description <desc>]")
            return 1

        workflow_id = args[1]
        try:
            step_index = int(args[2])
        except ValueError:
            print_error("Step index must be an integer")
            return 1
        status = args[3]

        # Parse optional arguments
        next_step = None
        if "--next-step" in args:
            idx = args.index("--next-step")
            if idx + 1 < len(args):
                next_step = args[idx + 1]

        auto_chain = "--no-auto-chain" not in args

        description = None
        if "--description" in args:
            idx = args.index("--description")
            if idx + 1 < len(args):
                description = args[idx + 1]

        transition = StepTransition(
            name=status,
            next_step=next_step,
            auto_chain=auto_chain,
            description=description,
        )

        result = cmat.workflow.add_transition(workflow_id, step_index, status, transition)
        if result:
            print(f"Transition added to step {step_index} in workflow '{workflow_id}'")
            print(f"  Status: {status}")
            print(f"  Next Step: {next_step or '(end)'}")
            print(f"  Auto Chain: {auto_chain}")
            if description:
                print(f"  Description: {description}")
            return 0
        else:
            print_error(f"Failed to add transition. Workflow or step not found.")
            return 1

    elif subcmd == "remove-transition":
        if len(args) < 4:
            print_error("Usage: cmat workflow remove-transition <workflow_id> <step_index> <status>")
            return 1

        workflow_id = args[1]
        try:
            step_index = int(args[2])
        except ValueError:
            print_error("Step index must be an integer")
            return 1
        status = args[3]

        result = cmat.workflow.remove_transition(workflow_id, step_index, status)
        if result:
            print(f"Transition '{status}' removed from step {step_index} in workflow '{workflow_id}'")
            return 0
        else:
            print_error(f"Failed to remove transition. Workflow, step, or status not found.")
            return 1

    else:
        print_error(f"Unknown workflow command: {subcmd}")
        return 1


def cmd_queue(cmat: CMAT, args: list[str]) -> int:
    """Handle queue subcommands."""
    if not args:
        print("Usage: cmat queue <status|list|add|start|complete|fail|cancel|rerun> [options]")
        return 1

    subcmd = args[0]

    if subcmd == "status":
        status = cmat.queue.status()
        print("Queue Status:")
        print(f"  Pending:   {status['pending']}")
        print(f"  Active:    {status['active']}")
        print(f"  Completed: {status['completed']}")
        print(f"  Failed:    {status['failed']}")
        print(f"  Total:     {status['total']}")
        return 0

    elif subcmd == "list":
        queue_type = args[1] if len(args) > 1 else "all"
        if queue_type == "pending":
            tasks = cmat.queue.list_pending()
        elif queue_type == "active":
            tasks = cmat.queue.list_active()
        elif queue_type == "completed":
            tasks = cmat.queue.list_completed()
        elif queue_type == "failed":
            tasks = cmat.queue.list_failed()
        elif queue_type == "all":
            tasks = cmat.queue.list_all()
        else:
            print_error(f"Unknown queue type: {queue_type}")
            return 1

        if not tasks:
            print(f"No {queue_type} tasks.")
            return 0

        print(f"{queue_type.capitalize()} tasks ({len(tasks)}):\n")
        for task in tasks:
            print(f"  {task.id}")
            print(f"    Title: {task.title}")
            print(f"    Agent: {task.assigned_agent}")
            print(f"    Status: {task.status.value}")
            if task.result:
                print(f"    Result: {task.result}")
            print()
        return 0

    elif subcmd == "add":
        if len(args) < 4:
            print_error("Usage: cmat queue add <agent> <title> <source_file> [--auto-chain] [--model <model_id>]")
            return 1

        agent = args[1]
        title = args[2]
        source_file = args[3]
        auto_chain = "--auto-chain" in args

        # Parse --model option
        model = None
        if "--model" in args:
            idx = args.index("--model")
            if idx + 1 < len(args):
                model = args[idx + 1]

        # Determine task type from agent
        task_type = cmat.workflow.get_task_type_for_agent(agent)

        task = cmat.queue.add(
            title=title,
            assigned_agent=agent,
            priority="normal",
            task_type=task_type,
            source_file=source_file,
            description=title,
            auto_complete=True,
            auto_chain=auto_chain,
            model=model,
        )

        print(f"Task added: {task.id}")
        print(f"  Agent: {agent}")
        print(f"  Title: {title}")
        print(f"  Auto-chain: {auto_chain}")
        if model:
            print(f"  Model: {model}")
        return 0

    elif subcmd == "start":
        if len(args) < 2:
            print_error("Usage: cmat queue start <task_id>")
            return 1

        task_id = args[1]
        task = cmat.queue.start(task_id)

        if task:
            print(f"Task started: {task_id}")
            print(f"  Agent: {task.assigned_agent}")
            return 0
        else:
            print_error(f"Failed to start task: {task_id}")
            print("  (Task may not exist or may not be in pending status)")
            return 1

    elif subcmd == "complete":
        if len(args) < 3:
            print_error("Usage: cmat queue complete <task_id> <result>")
            return 1

        task_id = args[1]
        result = args[2]
        task = cmat.queue.complete(task_id, result)

        if task:
            print(f"Task completed: {task_id}")
            print(f"  Result: {result}")
            return 0
        else:
            print_error(f"Failed to complete task: {task_id}")
            print("  (Task may not exist or may not be in active status)")
            return 1

    elif subcmd == "fail":
        if len(args) < 3:
            print_error("Usage: cmat queue fail <task_id> <reason>")
            return 1

        task_id = args[1]
        reason = args[2]
        task = cmat.queue.fail(task_id, reason)

        if task:
            print(f"Task failed: {task_id}")
            print(f"  Reason: {reason}")
            return 0
        else:
            print_error(f"Failed to fail task: {task_id}")
            print("  (Task may not exist or may not be in active status)")
            return 1

    elif subcmd == "cancel":
        if len(args) < 2:
            print_error("Usage: cmat queue cancel <task_id> [reason]")
            return 1

        task_id = args[1]
        reason = args[2] if len(args) > 2 else None
        task = cmat.queue.cancel(task_id, reason)

        if task:
            print(f"Task cancelled: {task_id}")
            if reason:
                print(f"  Reason: {reason}")
            return 0
        else:
            print_error(f"Failed to cancel task: {task_id}")
            print("  (Task may not exist or may not be pending/active)")
            return 1

    elif subcmd == "rerun":
        if len(args) < 2:
            print_error("Usage: cmat queue rerun <task_id>")
            return 1

        task_id = args[1]
        task = cmat.queue.rerun(task_id)

        if task:
            print(f"Task re-queued: {task_id}")
            print(f"  Status: pending")
            return 0
        else:
            print_error(f"Failed to rerun task: {task_id}")
            print("  (Task may not exist or may not be completed/failed)")
            return 1

    else:
        print_error(f"Unknown queue command: {subcmd}")
        return 1


def cmd_skills(cmat: CMAT, args: list[str]) -> int:
    """Handle skills subcommands."""
    if not args:
        print("Usage: cmat skills <list|show|get> [options]")
        return 1

    subcmd = args[0]

    if subcmd == "list":
        skills = cmat.skills.list_all()

        if not skills:
            print("No skills found.")
            return 0

        print(f"Available skills ({len(skills)}):\n")

        # Group by category
        categories: dict[str, list] = {}
        for skill in skills:
            cat = skill.category or "uncategorized"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(skill)

        for category in sorted(categories.keys()):
            print(f"  [{category}]")
            for skill in categories[category]:
                print(f"    {skill.skill_directory}")
                print(f"      Name: {skill.name}")
                print(f"      Description: {skill.description[:60]}..." if len(skill.description) > 60 else f"      Description: {skill.description}")
            print()
        return 0

    elif subcmd == "show":
        if len(args) < 2:
            print_error("Usage: cmat skills show <skill_directory>")
            return 1

        skill_dir = args[1]
        skill = cmat.skills.get(skill_dir)

        if not skill:
            print_error(f"Skill not found: {skill_dir}")
            return 1

        print(f"Skill: {skill.skill_directory}")
        print(f"  Name: {skill.name}")
        print(f"  Description: {skill.description}")
        print(f"  Category: {skill.category}")
        print(f"  Required Tools: {', '.join(skill.required_tools) if skill.required_tools else '(none)'}")

        # Show content preview
        content = cmat.skills.get_skill_content(skill_dir)
        if content:
            lines = content.split('\n')[:10]
            print(f"\n  Content Preview:")
            for line in lines:
                print(f"    {line}")
            if len(content.split('\n')) > 10:
                print("    ...")
        return 0

    elif subcmd == "get":
        if len(args) < 2:
            print_error("Usage: cmat skills get <agent_name>")
            return 1

        agent_name = args[1]
        agent = cmat.agents.get(agent_name)

        if not agent:
            print_error(f"Agent not found: {agent_name}")
            return 1

        if not agent.skills:
            print(f"Agent '{agent_name}' has no skills assigned.")
            return 0

        print(f"Skills for agent '{agent_name}':\n")
        for skill_name in agent.skills:
            skill = cmat.skills.get(skill_name)
            if skill:
                print(f"  {skill_name}")
                print(f"    Name: {skill.name}")
                print(f"    Category: {skill.category}")
            else:
                print(f"  {skill_name} (not found in registry)")
            print()
        return 0

    else:
        print_error(f"Unknown skills command: {subcmd}")
        return 1


def cmd_learnings(cmat: CMAT, args: list[str]) -> int:
    """Handle learnings subcommands."""
    if not args:
        print("Usage: cmat learnings <list|add|delete|show|search> [options]")
        return 1

    subcmd = args[0]

    if subcmd == "list":
        learnings = cmat.learnings.list_all()
        if not learnings:
            print("No learnings stored yet.")
            return 0

        print(f"Found {len(learnings)} learning(s):\n")
        for learning in sorted(learnings, key=lambda l: l.created, reverse=True):
            print_learning(learning)
        return 0

    elif subcmd == "add":
        if len(args) < 2:
            print_error("Usage: cmat learnings add \"<content>\" [--tags tag1,tag2]")
            return 1

        content = args[1]
        tags = []

        # Parse --tags option
        if "--tags" in args:
            idx = args.index("--tags")
            if idx + 1 < len(args):
                tags = [t.strip() for t in args[idx + 1].split(",")]

        learning = Learning.from_user_input(content, tags)
        cmat.learnings.store(learning)

        print(f"Learning added: {learning.id}")
        print(f"  Summary: {learning.summary}")
        return 0

    elif subcmd == "delete":
        if len(args) < 2:
            print_error("Usage: cmat learnings delete <id>")
            return 1

        learning_id = args[1]
        if cmat.learnings.delete(learning_id):
            print(f"Learning deleted: {learning_id}")
            return 0
        else:
            print_error(f"Learning not found: {learning_id}")
            return 1

    elif subcmd == "show":
        if len(args) < 2:
            print_error("Usage: cmat learnings show <id>")
            return 1

        learning_id = args[1]
        learning = cmat.learnings.get(learning_id)
        if learning:
            print_learning(learning, verbose=True)
            return 0
        else:
            print_error(f"Learning not found: {learning_id}")
            return 1

    elif subcmd == "search":
        if len(args) < 2:
            print_error("Usage: cmat learnings search \"<query>\"")
            return 1

        query = args[1]
        from cmat.services.learnings_service import RetrievalContext

        context = RetrievalContext(
            agent_name="search",
            task_type="search",
            task_description=query,
        )
        learnings = cmat.learnings.retrieve(context, limit=10)

        if not learnings:
            print("No relevant learnings found.")
            return 0

        print(f"Found {len(learnings)} relevant learning(s):\n")
        for learning in learnings:
            print_learning(learning)
        return 0

    elif subcmd == "count":
        count = cmat.learnings.count()
        print(f"Total learnings: {count}")
        return 0

    else:
        print_error(f"Unknown learnings command: {subcmd}")
        return 1


def cmd_agents(cmat: CMAT, args: list[str]) -> int:
    """Handle agents subcommands."""
    if not args:
        print("Usage: cmat agents <list|generate>")
        return 1

    subcmd = args[0]

    if subcmd == "list":
        agents = cmat.agents.list_all()
        if not agents:
            print("No agents found.")
            return 0

        print(f"Found {len(agents)} agent(s):\n")
        for agent in agents:
            print(f"  {agent.agent_file}")
            print(f"    Name: {agent.name}")
            print(f"    Role: {agent.role}")
            print(f"    Skills: {', '.join(agent.skills) if agent.skills else '(none)'}")
            print()
        return 0

    elif subcmd == "generate":
        result = cmat.agents.generate_agents_json()
        print(f"Generated {result['generated']} agents")
        if result['errors']:
            print("\nWarnings:")
            for error in result['errors']:
                print(f"  - {error}")
        return 0

    else:
        print_error(f"Unknown agents command: {subcmd}")
        return 1


def cmd_models(cmat: CMAT, args: list[str]) -> int:
    """Handle models subcommands."""
    if not args:
        print("Usage: cmat models <list|show|set-default>")
        return 1

    subcmd = args[0]

    if subcmd == "list":
        models = cmat.models.list_all()
        default = cmat.models.get_default()

        if not models:
            print("No models configured.")
            return 0

        print(f"Available models ({len(models)}):\n")
        for model in models:
            is_default = " (default)" if model.id == default.id else ""
            print(f"  {model.id}{is_default}")
            print(f"    Name: {model.name}")
            print(f"    Input:  ${model.pricing.input:.2f}/M tokens")
            print(f"    Output: ${model.pricing.output:.2f}/M tokens")
            print()
        return 0

    elif subcmd == "show":
        if len(args) < 2:
            print_error("Usage: cmat models show <id>")
            return 1

        model_id = args[1]
        model = cmat.models.get(model_id)

        if not model:
            print_error(f"Model not found: {model_id}")
            return 1

        default = cmat.models.get_default()
        is_default = " (default)" if model.id == default.id else ""

        print(f"Model: {model.id}{is_default}")
        print(f"  Name: {model.name}")
        print(f"  Description: {model.description}")
        print(f"  Pattern: {model.pattern}")
        print(f"  Max Tokens: {model.max_tokens:,}")
        print(f"\n  Pricing (per million tokens):")
        print(f"    Input:       ${model.pricing.input:.2f}")
        print(f"    Output:      ${model.pricing.output:.2f}")
        print(f"    Cache Write: ${model.pricing.cache_write:.2f}")
        print(f"    Cache Read:  ${model.pricing.cache_read:.2f}")
        return 0

    elif subcmd == "set-default":
        if len(args) < 2:
            print_error("Usage: cmat models set-default <id>")
            return 1

        model_id = args[1]
        if cmat.models.set_default(model_id):
            print(f"Default model set to: {model_id}")
            return 0
        else:
            print_error(f"Model not found: {model_id}")
            return 1

    else:
        print_error(f"Unknown models command: {subcmd}")
        return 1


def cmd_costs(cmat: CMAT, args: list[str]) -> int:
    """Handle costs subcommands."""
    if not args:
        print("Usage: cmat costs <extract|show|enhancement>")
        return 1

    subcmd = args[0]

    if subcmd == "extract":
        if len(args) < 3:
            print_error("Usage: cmat costs extract <task_id> <transcript_path> [session_id]")
            return 1

        task_id = args[1]
        transcript_path = args[2]
        session_id = args[3] if len(args) > 3 else ""

        # Verify task exists
        task = cmat.queue.get(task_id)
        if not task:
            print_error(f"Task not found: {task_id}")
            return 1

        cost = cmat.models.extract_and_store(
            task_id=task_id,
            transcript_path=transcript_path,
            session_id=session_id,
            queue_service=cmat.queue,
        )

        if cost is not None:
            print(f"Cost extracted: ${cost:.4f}")
        else:
            print("No usage data found in transcript")
        return 0

    elif subcmd == "show":
        if len(args) < 2:
            print_error("Usage: cmat costs show <task_id>")
            return 1

        task_id = args[1]
        cost_info = cmat.queue.show_task_cost(task_id)

        if not cost_info:
            print_error(f"Task not found or no cost data: {task_id}")
            return 1

        print(f"Cost for task {task_id}:")
        print(f"  Model: {cost_info.get('cost_model', 'unknown')}")
        print(f"  Input Tokens:    {cost_info.get('cost_input_tokens', '0'):>12}")
        print(f"  Output Tokens:   {cost_info.get('cost_output_tokens', '0'):>12}")
        print(f"  Cache Creation:  {cost_info.get('cost_cache_creation_tokens', '0'):>12}")
        print(f"  Cache Read:      {cost_info.get('cost_cache_read_tokens', '0'):>12}")
        print(f"  Total Cost:      ${cost_info.get('cost_usd', '0.0000'):>10}")
        return 0

    elif subcmd == "enhancement":
        if len(args) < 2:
            print_error("Usage: cmat costs enhancement <name>")
            return 1

        enhancement_name = args[1]
        cost_info = cmat.queue.show_enhancement_cost(enhancement_name)

        if not cost_info:
            print(f"No cost data found for enhancement: {enhancement_name}")
            return 0

        print(f"Cost for enhancement '{enhancement_name}':")
        print(f"  Tasks:           {cost_info.get('task_count', 0):>12}")
        print(f"  Input Tokens:    {cost_info.get('total_input_tokens', 0):>12}")
        print(f"  Output Tokens:   {cost_info.get('total_output_tokens', 0):>12}")
        print(f"  Total Cost:      ${cost_info.get('total_cost_usd', 0):.4f}")
        return 0

    else:
        print_error(f"Unknown costs command: {subcmd}")
        return 1


def main(args: Optional[list[str]] = None) -> int:
    """Main CLI entry point."""
    if args is None:
        args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0

    if args[0] in ("-v", "--version", "version"):
        print(f"CMAT version {__version__}")
        return 0

    # Initialize CMAT
    try:
        cmat = CMAT()
    except Exception as e:
        print_error(f"Failed to initialize CMAT: {e}")
        return 1

    command = args[0]
    cmd_args = args[1:]

    if command == "workflow":
        return cmd_workflow(cmat, cmd_args)
    elif command == "queue":
        return cmd_queue(cmat, cmd_args)
    elif command == "skills":
        return cmd_skills(cmat, cmd_args)
    elif command == "learnings":
        return cmd_learnings(cmat, cmd_args)
    elif command == "agents":
        return cmd_agents(cmat, cmd_args)
    elif command == "models":
        return cmd_models(cmat, cmd_args)
    elif command == "costs":
        return cmd_costs(cmat, cmd_args)
    else:
        print_error(f"Unknown command: {command}")
        print("Run 'cmat --help' for usage.")
        return 1


if __name__ == "__main__":
    sys.exit(main())