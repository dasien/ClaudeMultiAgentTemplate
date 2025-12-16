"""
CMAT CLI entry point.

Usage:
    python -m cmat <command> [options]

Commands:
    learnings list                    List all learnings
    learnings add "<content>"         Add a manual learning
    learnings delete <id>             Delete a learning
    learnings show <id>               Show learning details
    learnings search "<query>"        Search learnings (uses Claude)

    queue status                      Show queue status
    queue list [pending|active|completed|failed|all]

    agents list                       List all agents
    agents generate                   Regenerate agents.json from markdown

    models list                       List all Claude models
    models show <id>                  Show model details
    models set-default <id>           Set default model

    costs extract <task_id> <transcript_path> [session_id]
                                      Extract costs from transcript
    costs show <task_id>              Show task cost
    costs enhancement <name>          Show enhancement total cost

    version                           Show CMAT version
"""

import sys
import json
from typing import Optional

from cmat import CMAT, __version__
from cmat.models import Learning


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

        print(f"✓ Learning added: {learning.id}")
        print(f"  Summary: {learning.summary}")
        return 0

    elif subcmd == "delete":
        if len(args) < 2:
            print_error("Usage: cmat learnings delete <id>")
            return 1

        learning_id = args[1]
        if cmat.learnings.delete(learning_id):
            print(f"✓ Learning deleted: {learning_id}")
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


def cmd_queue(cmat: CMAT, args: list[str]) -> int:
    """Handle queue subcommands."""
    if not args:
        print("Usage: cmat queue <status|list> [options]")
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
            print()
        return 0

    else:
        print_error(f"Unknown queue command: {subcmd}")
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
        print(f"✓ Generated {result['generated']} agents")
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

    if command == "learnings":
        return cmd_learnings(cmat, cmd_args)
    elif command == "queue":
        return cmd_queue(cmat, cmd_args)
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