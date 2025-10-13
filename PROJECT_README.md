# Task Manager CLI

A simple command-line task management application written in Python.

## Features

- Add tasks with titles and descriptions
- List all tasks (with optional filter for completed)
- Mark tasks as completed
- Delete tasks
- Persistent storage using text file format
- Full test coverage

## Usage

```bash
# Add a new task
python src/task_manager.py add "Buy groceries" -d "Milk, eggs, bread"

# List all tasks
python src/task_manager.py list

# List all tasks including completed
python src/task_manager.py list --all

# Show task details
python src/task_manager.py show 1

# Complete a task
python src/task_manager.py complete 1

# Delete a task
python src/task_manager.py delete 1
```

## Running Tests

```bash
python -m unittest discover tests
```

## Requirements

- Python 3.7 or higher
- No external dependencies (uses Python standard library only)

## Storage

Tasks are stored in `tasks.txt` in the current directory using a simple pipe-delimited format.
