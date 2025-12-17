# Cost Tracking Guide

Complete guide to token usage and cost tracking in CMAT.

**Version**: 8.2.0

## Overview

CMAT tracks token usage and calculates costs for all agent tasks. This helps you:

- **Monitor spending**: Track costs per task and enhancement
- **Optimize usage**: Identify expensive operations
- **Budget planning**: Estimate costs for future work
- **Audit trail**: Maintain cost records for projects

---

## How It Works

### Cost Tracking Flow

```
┌─────────────────┐
│  Agent Task     │
│   Executes      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Session Ends   │
│  Hook Fires     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ on-session-end  │
│   -cost.sh      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  cmat costs     │
│    extract      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ModelService    │
│ Parse & Calculate│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Task Metadata   │
│   Updated       │
└─────────────────┘
```

### Components

1. **SessionEnd Hook**: Triggers cost extraction after each session
2. **ModelService**: Parses transcripts and calculates costs
3. **QueueService**: Stores costs in task metadata
4. **CLI Commands**: View and analyze costs

---

## Model Configuration

### models.json

Model definitions and pricing are stored in `.claude/data/models.json`:

```json
{
  "models": [
    {
      "id": "claude-sonnet-4-20250514",
      "name": "Claude Sonnet 4",
      "description": "Fast and intelligent model",
      "pattern": "claude-sonnet-4-.*",
      "max_tokens": 8192,
      "is_default": true,
      "pricing": {
        "input": 3.00,
        "output": 15.00,
        "cache_write": 3.75,
        "cache_read": 0.30
      }
    },
    {
      "id": "claude-opus-4-5-20251101",
      "name": "Claude Opus 4.5",
      "description": "Most capable model",
      "pattern": "claude-opus-4-.*",
      "max_tokens": 8192,
      "is_default": false,
      "pricing": {
        "input": 15.00,
        "output": 75.00,
        "cache_write": 18.75,
        "cache_read": 1.50
      }
    }
  ],
  "version": "1.0"
}
```

### Pricing Structure

Prices are per **million tokens**:

| Model | Input | Output | Cache Write | Cache Read |
|-------|-------|--------|-------------|------------|
| Sonnet 4 | $3.00 | $15.00 | $3.75 | $0.30 |
| Opus 4.5 | $15.00 | $75.00 | $18.75 | $1.50 |
| Haiku | $0.25 | $1.25 | $0.30 | $0.03 |

### Model Matching

Models are matched by pattern regex against the model ID in transcripts:

```json
{
  "pattern": "claude-sonnet-4-.*"
}
```

This allows matching versioned model IDs like `claude-sonnet-4-20250514`.

---

## CLI Commands

### models list

List all configured models.

```bash
python -m cmat models list
```

**Output**:
```
Available models (4):

  claude-sonnet-4-20250514 (default)
    Name: Claude Sonnet 4
    Input:  $3.00/M tokens
    Output: $15.00/M tokens

  claude-opus-4-5-20251101
    Name: Claude Opus 4.5
    Input:  $15.00/M tokens
    Output: $75.00/M tokens
```

### models show

Show detailed model information.

```bash
python -m cmat models show <id>
```

**Output**:
```
Model: claude-sonnet-4-20250514 (default)
  Name: Claude Sonnet 4
  Description: Fast and intelligent model
  Pattern: claude-sonnet-4-.*
  Max Tokens: 8,192

  Pricing (per million tokens):
    Input:       $3.00
    Output:      $15.00
    Cache Write: $3.75
    Cache Read:  $0.30
```

### models set-default

Set the default model for cost calculations.

```bash
python -m cmat models set-default <id>
```

### costs extract

Extract costs from a transcript and store in task metadata.

```bash
python -m cmat costs extract <task_id> <transcript_path> [session_id]
```

**Arguments**:
- `task_id`: Task to associate costs with
- `transcript_path`: Path to Claude transcript JSON
- `session_id`: Optional session ID filter

**Example**:
```bash
python -m cmat costs extract task_1702345678_12345 ~/.claude/sessions/abc123.json
```

### costs show

Show cost breakdown for a task.

```bash
python -m cmat costs show <task_id>
```

**Output**:
```
Cost for task task_1702345678_12345:
  Model: claude-sonnet-4-20250514
  Input Tokens:         12,345
  Output Tokens:         3,456
  Cache Creation:            0
  Cache Read:            8,901
  Total Cost:          $0.0789
```

### costs enhancement

Show total costs for all tasks in an enhancement.

```bash
python -m cmat costs enhancement <name>
```

**Output**:
```
Cost for enhancement 'my-feature':
  Tasks:              5
  Input Tokens:    45,678
  Output Tokens:   12,345
  Total Cost:     $0.2345
```

---

## Hook Configuration

### settings.json

The cost tracking hook must be configured in `.claude/settings.json`:

```json
{
  "hooks": {
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/on-session-end-cost.sh"
          }
        ]
      }
    ]
  }
}
```

### Hook Script

The `on-session-end-cost.sh` script receives session information and calls the Python cost extractor:

```bash
#!/bin/bash
# Simplified passthrough to Python cost extraction

TASK_ID="${CMAT_CURRENT_TASK_ID:-}"
TRANSCRIPT_PATH="$1"
SESSION_ID="${CMAT_SESSION_ID:-}"

if [ -n "$TASK_ID" ] && [ -n "$TRANSCRIPT_PATH" ]; then
    cd "$(dirname "$0")/.."
    python -m cmat costs extract "$TASK_ID" "$TRANSCRIPT_PATH" "$SESSION_ID"
fi
```

### Environment Variables

The hook expects these environment variables:

| Variable | Description |
|----------|-------------|
| `CMAT_CURRENT_TASK_ID` | Task ID for cost association |
| `CMAT_SESSION_ID` | Claude session identifier |

---

## Cost Metadata

### Task Metadata Fields

Costs are stored in task metadata:

```json
{
  "metadata": {
    "cost_input_tokens": "12345",
    "cost_output_tokens": "3456",
    "cost_cache_creation_tokens": "0",
    "cost_cache_read_tokens": "8901",
    "cost_usd": "0.0789",
    "cost_model": "claude-sonnet-4-20250514",
    "session_id": "abc123"
  }
}
```

### Token Types

| Field | Description |
|-------|-------------|
| `cost_input_tokens` | Tokens in prompts sent to Claude |
| `cost_output_tokens` | Tokens in Claude's responses |
| `cost_cache_creation_tokens` | Tokens written to prompt cache |
| `cost_cache_read_tokens` | Tokens read from prompt cache |

### Cost Calculation

```
Total Cost = (input_tokens × input_price / 1M)
           + (output_tokens × output_price / 1M)
           + (cache_creation_tokens × cache_write_price / 1M)
           + (cache_read_tokens × cache_read_price / 1M)
```

---

## ModelService API

### Core Methods

```python
# List all models
models = model_service.list_all()

# Get model by ID
model = model_service.get("claude-sonnet-4-20250514")

# Get default model
default = model_service.get_default()

# Set default model
model_service.set_default("claude-opus-4-5-20251101")
```

### Cost Methods

```python
# Extract and store costs
cost = model_service.extract_and_store(
    task_id="task_123",
    transcript_path="/path/to/transcript.json",
    session_id="abc123",
    queue_service=queue_service
)

# Calculate cost from token counts
cost = model_service.calculate_cost(
    model_id="claude-sonnet-4-20250514",
    input_tokens=12345,
    output_tokens=3456,
    cache_creation_tokens=0,
    cache_read_tokens=8901
)

# Get model by pattern matching
model = model_service.get_by_pattern("claude-sonnet-4-20250514")
```

---

## Best Practices

### Cost Optimization

1. **Use appropriate models**: Sonnet for most tasks, Opus for complex reasoning
2. **Monitor enhancement costs**: Track spending per feature
3. **Review high-cost tasks**: Investigate unusually expensive operations
4. **Leverage caching**: Cache reads are much cheaper than input tokens

### Model Selection

| Use Case | Recommended Model |
|----------|-------------------|
| Analysis tasks | Sonnet |
| Implementation | Sonnet |
| Complex architecture | Opus |
| Documentation | Sonnet or Haiku |
| Quick operations | Haiku |

### Monitoring

1. **Regular checks**: Review costs weekly
2. **Set alerts**: Monitor for unexpected spikes
3. **Enhancement budgets**: Estimate costs before starting
4. **Historical analysis**: Compare costs over time

---

## Troubleshooting

### Missing Cost Data

**Symptoms**: Task metadata shows null/empty cost fields

**Causes**:
- Hook not configured
- Environment variables not set
- Transcript not found
- Model not in models.json

**Resolution**:
1. Verify hook in settings.json
2. Check environment variables are set
3. Verify transcript path exists
4. Add model to models.json if missing

### Incorrect Cost Calculation

**Symptoms**: Costs seem too high or too low

**Causes**:
- Wrong model matched
- Pricing out of date
- Token counts wrong

**Resolution**:
1. Verify model pattern matching
2. Update pricing in models.json
3. Check transcript for correct usage data

### Model Not Recognized

**Symptoms**: "Model not found" errors

**Causes**:
- New model not in models.json
- Pattern doesn't match

**Resolution**:
1. Add model definition to models.json
2. Adjust pattern regex to match model ID

---

## Adding New Models

When Anthropic releases new models:

1. **Add to models.json**:
```json
{
  "id": "claude-new-model-20250601",
  "name": "Claude New Model",
  "description": "Description",
  "pattern": "claude-new-model-.*",
  "max_tokens": 8192,
  "is_default": false,
  "pricing": {
    "input": 5.00,
    "output": 25.00,
    "cache_write": 6.25,
    "cache_read": 0.50
  }
}
```

2. **Verify pattern matches** model IDs in transcripts

3. **Update default** if needed:
```bash
python -m cmat models set-default claude-new-model-20250601
```

---

## See Also

- [CLI_REFERENCE.md](CLI_REFERENCE.md) - Complete CLI commands
- [QUEUE_SYSTEM_GUIDE.md](QUEUE_SYSTEM_GUIDE.md) - Task metadata
- [INSTALLATION.md](../../INSTALLATION.md) - Hook setup
