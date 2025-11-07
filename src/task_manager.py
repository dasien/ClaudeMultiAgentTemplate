#!/usr/bin/env python3
"""
Simple Task Manager CLI Application
A demonstration project for the Claude Multi-Agent Template
"""

import argparse
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional


class Task:
    """Represents a single task with title, description, and status."""

    def __init__(self, title: str, description: str = "", task_id: Optional[int] = None):
        self.id = task_id
        self.title = title
        self.description = description
        self.status = "pending"
        self.created_at = datetime.now().isoformat()
        self.completed_at = None

    def complete(self):
        """Mark task as completed."""
        self.status = "completed"
        self.completed_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """Convert task to dictionary format."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        """Create task from dictionary format."""
        task = cls(data["title"], data["description"], data["id"])
        task.status = data["status"]
        task.created_at = data["created_at"]
        task.completed_at = data["completed_at"]
        return task

    def __str__(self) -> str:
        """String representation of task."""
        status_icon = "✓" if self.status == "completed" else "○"
        return f"[{self.id}] {status_icon} {self.title}"


class TaskManager:
    """Manages a collection of tasks with persistence."""

    def __init__(self, storage_file: str = "tasks.txt"):
        self.storage_file = storage_file
        self.tasks: List[Task] = []
        self.next_id = 1
        self.load_tasks()

    def add_task(self, title: str, description: str = "") -> Task:
        """Add a new task."""
        task = Task(title, description, self.next_id)
        self.tasks.append(task)
        self.next_id += 1
        self.save_tasks()
        return task

    def list_tasks(self, show_completed: bool = False) -> List[Task]:
        """List all tasks, optionally including completed ones."""
        if show_completed:
            return self.tasks
        return [t for t in self.tasks if t.status != "completed"]

    def get_task(self, task_id: int) -> Optional[Task]:
        """Get a specific task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def complete_task(self, task_id: int) -> bool:
        """Mark a task as completed."""
        task = self.get_task(task_id)
        if task:
            task.complete()
            self.save_tasks()
            return True
        return False

    def delete_task(self, task_id: int) -> bool:
        """Delete a task."""
        task = self.get_task(task_id)
        if task:
            self.tasks.remove(task)
            self.save_tasks()
            return True
        return False

    def save_tasks(self):
        """Save tasks to storage file (simple text format)."""
        with open(self.storage_file, 'w') as f:
            for task in self.tasks:
                # Simple pipe-delimited format
                line = f"{task.id}|{task.title}|{task.description}|{task.status}|{task.created_at}|{task.completed_at or ''}\n"
                f.write(line)

    def load_tasks(self):
        """Load tasks from storage file."""
        if not os.path.exists(self.storage_file):
            return

        with open(self.storage_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                parts = line.split('|')
                if len(parts) >= 6:
                    task_id = int(parts[0])
                    title = parts[1]
                    description = parts[2]
                    status = parts[3]
                    created_at = parts[4]
                    completed_at = parts[5] if parts[5] else None

                    task = Task(title, description, task_id)
                    task.status = status
                    task.created_at = created_at
                    task.completed_at = completed_at

                    self.tasks.append(task)
                    if task_id >= self.next_id:
                        self.next_id = task_id + 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Simple Task Manager CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("title", help="Task title")
    add_parser.add_argument("-d", "--description", default="", help="Task description")

    # List command
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("-a", "--all", action="store_true", help="Show completed tasks")

    # Complete command
    complete_parser = subparsers.add_parser("complete", help="Complete a task")
    complete_parser.add_argument("task_id", type=int, help="Task ID to complete")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("task_id", type=int, help="Task ID to delete")

    # Show command
    show_parser = subparsers.add_parser("show", help="Show task details")
    show_parser.add_argument("task_id", type=int, help="Task ID to show")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize task manager for stateful commands
    manager = TaskManager()

    # Execute stateful commands
    if args.command == "add":
        task = manager.add_task(args.title, args.description)
        print(f"✓ Task added: {task}")

    elif args.command == "list":
        tasks = manager.list_tasks(show_completed=args.all)
        if not tasks:
            print("No tasks found.")
        else:
            for task in tasks:
                print(task)

    elif args.command == "complete":
        if manager.complete_task(args.task_id):
            print(f"✓ Task {args.task_id} marked as completed")
        else:
            print(f"✗ Task {args.task_id} not found")
            sys.exit(1)

    elif args.command == "delete":
        if manager.delete_task(args.task_id):
            print(f"✓ Task {args.task_id} deleted")
        else:
            print(f"✗ Task {args.task_id} not found")
            sys.exit(1)

    elif args.command == "show":
        task = manager.get_task(args.task_id)
        if task:
            print(f"Task ID: {task.id}")
            print(f"Title: {task.title}")
            print(f"Description: {task.description}")
            print(f"Status: {task.status}")
            print(f"Created: {task.created_at}")
            if task.completed_at:
                print(f"Completed: {task.completed_at}")
        else:
            print(f"✗ Task {args.task_id} not found")
            sys.exit(1)


if __name__ == "__main__":
    main()