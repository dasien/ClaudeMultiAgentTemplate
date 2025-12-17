# Learnings Guide

Complete guide to the RAG-based learnings system in CMAT.

**Version**: 8.2.0

## Overview

The learnings system provides persistent memory for the multi-agent system. It captures insights, patterns, and knowledge from agent outputs and user feedback, then retrieves relevant learnings when building prompts for future tasks.

### Key Benefits

- **Continuous Improvement**: Agents learn from past work
- **Consistency**: Project patterns are reinforced across tasks
- **Onboarding**: New team members benefit from captured knowledge
- **Quality**: Best practices are automatically applied

---

## How It Works

### Learning Flow

```
┌─────────────────┐
│ Learning Sources │
├─────────────────┤
│ - Agent outputs │
│ - User input    │
│ - Code patterns │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Extraction    │
│  (via Claude)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Storage      │
│ learnings.json  │
└────────┬────────┘
         │
         ▼ (on new task)
┌─────────────────┐
│   Retrieval     │
│  (via Claude)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Prompt Injection│
│ (context-aware) │
└─────────────────┘
```

### Components

1. **Learning Model**: Structured data representing a learning
2. **LearningsService**: Manages storage, extraction, and retrieval
3. **TaskService Integration**: Injects learnings into prompts
4. **CLI Commands**: Manual learning management

---

## Learning Structure

Each learning has the following properties:

```json
{
  "id": "learn_1702345678_12345",
  "summary": "Use pytest fixtures for database tests",
  "content": "When writing database tests, always use pytest fixtures with scope='function' for isolated test databases. This prevents test pollution and ensures reliable test execution.",
  "tags": ["testing", "python", "database"],
  "applies_to": ["implementation", "testing"],
  "source_type": "user_input",
  "source_task_id": null,
  "confidence": 0.8,
  "created": "2024-12-12T10:30:00Z"
}
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Unique ID: `learn_<timestamp>_<random>` |
| `summary` | string | 1-2 sentence description |
| `content` | string | Full learning content |
| `tags` | array | Categories: `python`, `testing`, `architecture`, etc. |
| `applies_to` | array | Contexts: `analysis`, `implementation`, `testing`, etc. |
| `source_type` | enum | `user_input`, `agent_output`, `code_pattern` |
| `source_task_id` | string | Task ID if extracted from agent output |
| `confidence` | float | 0.0-1.0, how universal vs project-specific |
| `created` | string | ISO 8601 timestamp |

---

## CLI Commands

### learnings list

List all stored learnings.

```bash
python -m cmat learnings list
```

**Output**:
```
Found 3 learning(s):

  ID: learn_1702345678_12345
  Summary: Use pytest fixtures for database tests
  Tags: testing, python, database
  Applies to: implementation, testing
  Source: user_input
  Confidence: 80%
  Created: 2024-12-12T10:30:00Z

  ...
```

### learnings add

Add a new learning manually.

```bash
python -m cmat learnings add "<content>" [--tags tag1,tag2]
```

**Examples**:
```bash
# Simple learning
python -m cmat learnings add "Always use snake_case for Python function names"

# With tags
python -m cmat learnings add "API responses should return ISO 8601 timestamps" --tags api,python

# Complex learning
python -m cmat learnings add "When implementing authentication, use JWT tokens with short expiration (15 min) and refresh tokens for longer sessions. Store refresh tokens in httpOnly cookies for security." --tags security,authentication
```

### learnings show

Show full details including content.

```bash
python -m cmat learnings show <id>
```

**Output**:
```
  ID: learn_1702345678_12345
  Summary: Use pytest fixtures for database tests
  Tags: testing, python, database
  Applies to: implementation, testing
  Source: user_input
  Confidence: 80%
  Created: 2024-12-12T10:30:00Z
  Content:
    When writing database tests, always use pytest fixtures...
```

### learnings delete

Remove a learning by ID.

```bash
python -m cmat learnings delete <id>
```

### learnings search

Search for relevant learnings.

```bash
python -m cmat learnings search "<query>"
```

**Example**:
```bash
python -m cmat learnings search "database testing patterns"
```

This uses Claude to find the most relevant learnings for the query.

### learnings count

Show total count.

```bash
python -m cmat learnings count
```

---

## Learning Sources

### 1. User Input (Manual)

Add learnings directly via CLI:

```bash
python -m cmat learnings add "Description of the learning" --tags tag1,tag2
```

**Best practices for manual learnings**:
- Be specific and actionable
- Include context and reasoning
- Use relevant tags for discoverability
- Keep summary concise, detail in content

### 2. Agent Outputs (Automatic)

When agents complete tasks, the system can extract learnings from their output. This captures:

- Architectural decisions
- Coding patterns discovered
- Gotchas and workarounds
- Best practices applied

**Extraction prompt example**:
```
Analyze this agent output and extract any learnings that would help future tasks.
Look for: coding patterns, architectural decisions, gotchas, preferences, best practices.
```

### 3. Code Patterns (Future)

Planned feature to analyze project code and detect recurring patterns:

- Function naming conventions
- Error handling patterns
- Testing approaches
- Documentation styles

---

## Retrieval Context

When retrieving learnings for a task, the system considers:

```python
@dataclass
class RetrievalContext:
    agent_name: str        # Which agent is running
    task_type: str         # Type of task (analysis, implementation, etc.)
    task_description: str  # What the task is about
    source_file: str       # Input file being processed (optional)
```

### Relevance Scoring

Claude evaluates each learning's relevance based on:

1. **Tag matching**: Learning tags vs task context
2. **applies_to matching**: Learning contexts vs task type
3. **Semantic relevance**: Content relevance to task description
4. **Confidence**: Higher confidence learnings preferred

---

## Storage

### File Location

Learnings are stored in `.claude/data/learnings.json`:

```json
{
  "learnings": [
    {
      "id": "learn_1702345678_12345",
      "summary": "...",
      "content": "...",
      "tags": [...],
      "applies_to": [...],
      "source_type": "user_input",
      "source_task_id": null,
      "confidence": 0.8,
      "created": "2024-12-12T10:30:00Z"
    }
  ],
  "version": "1.0",
  "last_updated": "2024-12-12T10:30:00Z"
}
```

### Backup

The learnings file is automatically backed up before major operations. You can also manually backup:

```bash
cp .claude/data/learnings.json .claude/data/learnings.backup.json
```

---

## Integration with Tasks

### Prompt Injection

When building prompts, `TaskService` retrieves relevant learnings and injects them:

```python
def build_prompt(self, agent, task_type, task_id, task_description, source_file):
    # ... build base prompt ...

    # Retrieve relevant learnings
    context = RetrievalContext(
        agent_name=agent.name,
        task_type=task_type,
        task_description=task_description,
        source_file=source_file
    )
    learnings = self.learnings_service.retrieve(context, limit=5)

    if learnings:
        learnings_section = self.learnings_service.build_learnings_prompt(learnings)
        prompt += f"\n\n{learnings_section}"

    return prompt
```

### Learnings Prompt Section

Injected learnings appear as:

```markdown
## Relevant Learnings

The following learnings from previous work may be helpful:

### Use pytest fixtures for database tests
When writing database tests, always use pytest fixtures with scope='function'...

### API responses should use ISO 8601 timestamps
All datetime fields in API responses should be formatted as ISO 8601 strings...

Apply these learnings where relevant to your current task.
```

### Task Metadata

Tasks track which learnings were used:

```json
{
  "metadata": {
    "learnings_retrieved": ["learn_123", "learn_456"],
    "learnings_created": ["learn_789"]
  }
}
```

---

## Best Practices

### Adding Effective Learnings

1. **Be specific**: "Use retry with exponential backoff for API calls" not "Handle errors properly"

2. **Include reasoning**: Explain why, not just what

3. **Use appropriate tags**: Help retrieval find the learning

4. **Set applies_to correctly**: Match to relevant task types

5. **Consider confidence**: Universal patterns get higher confidence

### Learning Categories

**Code Style**:
- Naming conventions
- Formatting preferences
- Comment styles

**Architecture**:
- Design patterns to use
- Architectural decisions
- Component boundaries

**Testing**:
- Test patterns
- Coverage requirements
- Test data management

**Security**:
- Authentication approaches
- Input validation
- Error handling

**Performance**:
- Optimization patterns
- Caching strategies
- Query optimization

### Maintenance

1. **Review periodically**: Remove outdated learnings
2. **Update as needed**: Modify learnings when patterns change
3. **Consolidate duplicates**: Merge similar learnings
4. **Verify relevance**: Check that retrieval returns useful results

---

## LearningsService API

### Core Methods

```python
# Store a learning
learning_id = learnings_service.store(learning)

# Get learning by ID
learning = learnings_service.get(learning_id)

# Delete a learning
success = learnings_service.delete(learning_id)

# List all learnings
all_learnings = learnings_service.list_all()

# Count learnings
count = learnings_service.count()
```

### Retrieval Methods

```python
# Retrieve relevant learnings for a context
context = RetrievalContext(
    agent_name="implementer",
    task_type="implementation",
    task_description="Add user authentication",
    source_file="enhancements/auth/auth.md"
)
relevant = learnings_service.retrieve(context, limit=5)

# Build prompt section
prompt_section = learnings_service.build_learnings_prompt(relevant)
```

### Factory Methods

```python
# Create learning from user input
learning = Learning.from_user_input(
    content="Always use snake_case for Python",
    tags=["python", "style"]
)

# Create learning from agent extraction
learning = Learning.from_claude_extraction(
    response=extraction_result,
    source_task_id="task_123"
)
```

---

## Troubleshooting

### Learnings Not Being Retrieved

**Symptoms**: Agents don't seem to use stored learnings

**Causes**:
- Tags don't match task context
- applies_to doesn't include task type
- Low relevance score

**Resolution**:
1. Check learning tags match task context
2. Verify applies_to includes relevant task types
3. Test with `learnings search` command

### Too Many Irrelevant Learnings

**Symptoms**: Prompts include unrelated learnings

**Causes**:
- Tags too broad
- Content too generic
- Confidence too high

**Resolution**:
1. Use more specific tags
2. Add clearer content
3. Adjust confidence level

### Duplicate Learnings

**Symptoms**: Same insight appears multiple times

**Resolution**:
1. List all learnings
2. Identify duplicates
3. Delete extras, keep best version

---

## See Also

- [CLI_REFERENCE.md](CLI_REFERENCE.md) - Complete CLI commands
- [QUEUE_SYSTEM_GUIDE.md](QUEUE_SYSTEM_GUIDE.md) - Task metadata
- [TASK_PROMPT_DEFAULTS.md](TASK_PROMPT_DEFAULTS.md) - Prompt templates