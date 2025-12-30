# CMAT - Claude Multi-Agent Template

A workflow-based multi-agent development system with a graphical interface for managing AI-powered software development workflows.

## Overview

CMAT orchestrates multiple Claude-powered agents through customizable workflows. Each agent has specialized skills and responsibilities:

- **Requirements Analyst** - Analyzes and documents requirements
- **Architect** - Designs technical solutions
- **Implementer** - Writes production code
- **Tester** - Validates functionality and writes tests
- **Documenter** - Creates and updates documentation

Agents work together through **workflows** that automatically chain tasks based on completion status.

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Claude Code CLI installed and authenticated
- Claude API key (for enhancement generation features)

### Installation

```bash
# Clone the repository
git clone https://github.com/anthropics/claude-multi-agent-template.git
cd claude-multi-agent-template

# Install dependencies
pip install -e .

# Launch the UI
python run.py
```

### First Steps

## Try the Demo

The `demo/` folder contains a sample calculator project for testing CMAT:

1. Launch the UI: `python run.py`
2. Install CMAT to demo: File → Install... → select the `demo/` folder
3. Connect (auto-connects after install)
4. Launch a workflow: Workflows → Launch Workflow (`Ctrl+W`)
5. Create an enhancement (e.g., "Add modulo operation to calculator")
6. Watch the agents analyze, architect, implement, test, and document

To reset the demo to its original state:
```bash
./demo/reset_demo.sh
```

## Install CMAT to a Project

1.**Launch the UI**: `python run.py`
2. **Install CMAT to a project**: File → Install... → Select your project directory
3. **Connect to the project**: The UI auto-connects after installation
4. **Configure Claude API** (optional): Settings → Claude Settings → Enter API key
5. **Run a workflow**:
   - Create an enhancement: Enhancements → Generate... (`Ctrl+E`)
   - Start a workflow: Workflows → Launch Workflow (`Ctrl+W`)
   - Select your enhancement and click Start
   
## Project Structure

```
ClaudeMultiAgentTemplate/
├── src/
│   ├── core/              # Core services and models
│   │   ├── models/        # Data models (Task, Agent, Workflow, etc.)
│   │   └── services/      # Business logic services
│   └── ui/                # Tkinter graphical interface
│       └── dialogs/       # Dialog windows
├── templates/.claude/     # Installable template assets
│   ├── agents/            # Agent definitions
│   ├── skills/            # Skill definitions
│   ├── data/              # Configuration data
│   └── hooks/             # Claude Code hooks
├── docs/                  # Documentation
├── demo/                  # Demo project for testing
└── run.py                 # UI launcher
```

## Features

### Core Features

- **Task Management** - Create, start, cancel, and monitor tasks
- **Workflow Orchestration** - Auto-chain agents through multi-step workflows
- **Agent Management** - Configure agents with tools and skills
- **Skills System** - Specialized capabilities agents can apply
- **Enhancement Generator** - AI-assisted creation of specification files
- **Cost Tracking** - Monitor token usage and costs per task

### Workflow Features

- **Visual Template Editor** - Create and edit workflow templates
- **Pre-flight Validation** - Validates workflows before starting
- **Model Selection** - Choose different models per workflow step
- **Auto-Chain** - Automatically progress through workflow steps

## Documentation

- **[USER_GUIDE.md](USER_GUIDE.md)** - Complete guide to using CMAT
- **[SYSTEM_REFERENCE.md](SYSTEM_REFERENCE.md)** - Technical reference for internals

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Connect to project |
| `Ctrl+E` | Generate enhancement |
| `Ctrl+N` | Create task |
| `Ctrl+W` | Launch workflow |
| `Ctrl+R` | Learnings browser |
| `Ctrl+L` | View logs |
| `F5` | Refresh |
| `Escape` | Close dialog |

## Configuration

### Claude API Settings

Configure via **Settings → Claude Settings**:

- **API Key** - Your Claude API key from console.anthropic.com
- **Model** - Choose from Opus 4.5, Sonnet 4.5, Sonnet 4, or Haiku 4.5
- **Max Tokens** - Output token limit
- **Timeout** - Request timeout in seconds

Settings are persisted to `~/.claude_queue_ui/settings.json`

### Available Models

| Model | Best For |
|-------|----------|
| Claude Opus 4.5 | Complex architecture and analysis |
| Claude Sonnet 4.5 | General-purpose tasks (default) |
| Claude Sonnet 4 | Balanced performance |
| Claude Haiku 4.5 | Fast, simple tasks |

## License

MIT License - see LICENSE file for details
