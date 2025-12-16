# Cost Extraction Migration Plan

## Overview

Migrate cost extraction from bash (`on-session-end-cost.sh`) to Python, with the hook acting as a thin passthrough.

**Current State:**
- `on-session-end-cost.sh` is broken (references deleted `.claude/scripts/cmat.sh` and old paths)
- `on-subagent-stop.sh` has been deleted (was also broken)
- Python has cost data models but doesn't populate them

**Goal:** Hook intercepts session end, passes transcript path to Python which handles all logic.

---

## Phase 1: Create Python Cost Extraction

### 1.1 Create CostService
**New File:** `.claude/cmat/services/cost_service.py`

```python
class CostService:
    def __init__(self, models_file: Optional[str] = None):
        # Load models.json for pricing data

    def extract_from_transcript(self, transcript_path: str) -> dict:
        """
        Parse transcript JSONL file and extract usage data.

        Returns:
            {
                "input_tokens": int,
                "output_tokens": int,
                "cache_creation_tokens": int,
                "cache_read_tokens": int,
                "model": str,
            }
        """

    def calculate_cost(self, usage: dict) -> float:
        """Calculate USD cost from usage data using models.json pricing."""

    def extract_and_store(
        self,
        task_id: str,
        transcript_path: str,
        session_id: str,
        queue_service: QueueService
    ) -> Optional[float]:
        """
        Extract cost from transcript and store in task metadata.

        1. Parse transcript
        2. Calculate cost
        3. Update task metadata via queue_service
        4. Return cost_usd
        """
```

### 1.2 Wire into CMAT
**File:** `.claude/cmat/cmat.py`

```python
from .services.cost_service import CostService

class CMAT:
    def __init__(self, ...):
        # ... existing services ...
        self.costs = CostService(
            models_file=str(base / ".claude/data/models.json")
        )
```

---

## Phase 2: Add CLI Command

### 2.1 Add costs command to CLI
**File:** `.claude/cmat/__main__.py`

Add:
```
Commands:
    costs extract <task_id> <transcript_path> [session_id]
    costs show <task_id>
    costs enhancement <enhancement_name>
```

Implementation:
```python
def cmd_costs_extract(task_id: str, transcript_path: str, session_id: str = ""):
    cmat = CMAT()
    cost = cmat.costs.extract_and_store(
        task_id=task_id,
        transcript_path=transcript_path,
        session_id=session_id,
        queue_service=cmat.queue
    )
    if cost:
        print(f"Cost: ${cost:.4f}")
    else:
        print("No cost data extracted")
```

---

## Phase 3: Simplify Hook

### 3.1 Rewrite on-session-end-cost.sh
**File:** `.claude/hooks/on-session-end-cost.sh`

Replace entire file with:
```bash
#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Read hook input from stdin
HOOK_INPUT=$(cat)

# Check if we're in a task execution context
TASK_ID="${CMAT_CURRENT_TASK_ID:-}"

if [ -z "$TASK_ID" ]; then
    exit 0
fi

# Extract session info from hook input
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path // ""')
SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // ""')

if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
    exit 0
fi

# Call Python to handle cost extraction
cd "$PROJECT_ROOT"
python -m cmat costs extract "$TASK_ID" "$TRANSCRIPT_PATH" "$SESSION_ID" 2>&1 || true
```

---

## Phase 4: Update Exports and Tests

### 4.1 Export CostService
**File:** `.claude/cmat/services/__init__.py`

Add:
```python
from .cost_service import CostService
```

### 4.2 Add Unit Tests
**File:** `.claude/tests/test_services.py`

Add `TestCostService` class:
- `test_extract_from_transcript()` - with mock JSONL data
- `test_calculate_cost()` - verify pricing math
- `test_extract_and_store()` - verify metadata update

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `.claude/cmat/services/cost_service.py` | **CREATE** |
| `.claude/cmat/services/__init__.py` | Add export |
| `.claude/cmat/cmat.py` | Wire CostService |
| `.claude/cmat/__main__.py` | Add `costs` command |
| `.claude/hooks/on-session-end-cost.sh` | Simplify to passthrough |
| `.claude/tests/test_services.py` | Add CostService tests |

---

## Transcript JSONL Format

The transcript file contains one JSON object per line. Assistant messages with usage look like:
```json
{"type":"assistant","message":{"usage":{"input_tokens":100,"output_tokens":50,"cache_creation_input_tokens":0,"cache_read_input_tokens":0}}}
```

The extraction logic:
1. Read file line by line
2. Filter lines containing `"type":"assistant"`
3. Parse JSON, extract `.message.usage`
4. Sum all token counts across messages
5. Get model from first message with model field

---

## Version Bump

After implementation, bump to 8.2.0 in:
- `.claude/cmat/__init__.py`
- `.claude/pyproject.toml`
- `.claude/manifest.json`