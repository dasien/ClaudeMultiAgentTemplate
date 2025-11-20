#!/usr/bin/env python3
"""
Unit tests for Task Manager CLI
"""

import unittest
import os
import sys
import subprocess
import tempfile
from src.task_manager import Task, TaskManager


class TestTask(unittest.TestCase):
    """Test cases for Task class."""

    def test_task_creation(self):
        """Test creating a new task."""
        task = Task("Test task", "Test description", 1)
        self.assertEqual(task.id, 1)
        self.assertEqual(task.title, "Test task")
        self.assertEqual(task.description, "Test description")
        self.assertEqual(task.status, "pending")

    def test_task_completion(self):
        """Test completing a task."""
        task = Task("Test task", "", 1)
        self.assertEqual(task.status, "pending")
        self.assertIsNone(task.completed_at)

        task.complete()
        self.assertEqual(task.status, "completed")
        self.assertIsNotNone(task.completed_at)

    def test_task_to_dict(self):
        """Test converting task to dictionary."""
        task = Task("Test task", "Description", 1)
        data = task.to_dict()

        self.assertEqual(data["id"], 1)
        self.assertEqual(data["title"], "Test task")
        self.assertEqual(data["description"], "Description")
        self.assertEqual(data["status"], "pending")

    def test_task_from_dict(self):
        """Test creating task from dictionary."""
        data = {
            "id": 1,
            "title": "Test task",
            "description": "Description",
            "status": "pending",
            "created_at": "2024-01-01T12:00:00",
            "completed_at": None
        }

        task = Task.from_dict(data)
        self.assertEqual(task.id, 1)
        self.assertEqual(task.title, "Test task")
        self.assertEqual(task.status, "pending")


class TestTaskManager(unittest.TestCase):
    """Test cases for TaskManager class."""

    def setUp(self):
        """Create a temporary file for each test."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self.temp_file.close()
        self.manager = TaskManager(self.temp_file.name)

    def tearDown(self):
        """Clean up temporary file after each test."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_add_task(self):
        """Test adding a new task."""
        task = self.manager.add_task("Test task", "Description")
        self.assertIsNotNone(task.id)
        self.assertEqual(task.title, "Test task")
        self.assertEqual(len(self.manager.tasks), 1)

    def test_list_tasks(self):
        """Test listing tasks."""
        self.manager.add_task("Task 1")
        self.manager.add_task("Task 2")

        tasks = self.manager.list_tasks()
        self.assertEqual(len(tasks), 2)

    def test_list_tasks_filter_completed(self):
        """Test that completed tasks are filtered by default."""
        task1 = self.manager.add_task("Task 1")
        task2 = self.manager.add_task("Task 2")

        self.manager.complete_task(task1.id)

        active_tasks = self.manager.list_tasks(show_completed=False)
        all_tasks = self.manager.list_tasks(show_completed=True)

        self.assertEqual(len(active_tasks), 1)
        self.assertEqual(len(all_tasks), 2)

    def test_get_task(self):
        """Test getting a specific task."""
        task = self.manager.add_task("Test task")
        found = self.manager.get_task(task.id)

        self.assertIsNotNone(found)
        self.assertEqual(found.id, task.id)

    def test_complete_task(self):
        """Test completing a task."""
        task = self.manager.add_task("Test task")
        result = self.manager.complete_task(task.id)

        self.assertTrue(result)
        self.assertEqual(task.status, "completed")

    def test_delete_task(self):
        """Test deleting a task."""
        task = self.manager.add_task("Test task")
        result = self.manager.delete_task(task.id)

        self.assertTrue(result)
        self.assertEqual(len(self.manager.tasks), 0)

    def test_persistence(self):
        """Test saving and loading tasks."""
        self.manager.add_task("Task 1", "Description 1")
        self.manager.add_task("Task 2", "Description 2")

        # Create new manager with same file
        manager2 = TaskManager(self.temp_file.name)

        self.assertEqual(len(manager2.tasks), 2)
        self.assertEqual(manager2.tasks[0].title, "Task 1")
        self.assertEqual(manager2.tasks[1].title, "Task 2")

class TestHelloCommand(unittest.TestCase):
    """Test cases for hello command (demo-test enhancement)."""

    def test_hello_command_output(self):
        """Test that hello command outputs 'Hello, World!'"""
        result = subprocess.run(
            [sys.executable, "src/task_manager.py", "hello"],
            capture_output=True,
            text=True
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Hello, World!")
        self.assertEqual(result.stderr, "")

    def test_hello_command_exit_code(self):
        """Test that hello command exits with code 0."""
        result = subprocess.run(
            [sys.executable, "src/task_manager.py", "hello"],
            capture_output=True
        )

        self.assertEqual(result.returncode, 0)

    def test_hello_command_in_help(self):
        """Test that hello command appears in help output."""
        result = subprocess.run(
            [sys.executable, "src/task_manager.py", "--help"],
            capture_output=True,
            text=True
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("hello", result.stdout)
        self.assertIn("Display a simple greeting", result.stdout)

    def test_hello_command_no_side_effects(self):
        """Test that hello command doesn't create or modify files."""
        # Get initial directory state
        temp_dir = tempfile.gettempdir()
        before_files = set(os.listdir(temp_dir))

        # Run hello command
        subprocess.run(
            [sys.executable, "src/task_manager.py", "hello"],
            capture_output=True
        )

        # Check directory state after
        after_files = set(os.listdir(temp_dir))

        # No new files should be created
        self.assertEqual(before_files, after_files)


class TestRegressionExistingCommands(unittest.TestCase):
    """Regression tests to ensure existing commands still work after hello command addition."""

    def setUp(self):
        """Create a temporary file for each test."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self.temp_file.close()

    def tearDown(self):
        """Clean up temporary file after each test."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_list_command_still_works(self):
        """Test that list command works after hello command added."""
        result = subprocess.run(
            [sys.executable, "src/task_manager.py", "list"],
            capture_output=True,
            text=True,
            env={**os.environ, "TASK_FILE": self.temp_file.name}
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("No tasks found", result.stdout)

    def test_help_shows_all_commands(self):
        """Test that help output includes all commands including hello."""
        result = subprocess.run(
            [sys.executable, "src/task_manager.py", "--help"],
            capture_output=True,
            text=True
        )

        self.assertEqual(result.returncode, 0)
        # Check all commands are present
        self.assertIn("add", result.stdout)
        self.assertIn("list", result.stdout)
        self.assertIn("complete", result.stdout)
        self.assertIn("delete", result.stdout)
        self.assertIn("show", result.stdout)
        self.assertIn("hello", result.stdout)


if __name__ == "__main__":
    unittest.main()