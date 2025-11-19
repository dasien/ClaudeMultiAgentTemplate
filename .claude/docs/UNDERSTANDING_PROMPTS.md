# Prompt Construction Guide

The purpose of this document is to aid in understanding how the Claude Multi-Agent Template builds prompts for agents.

## Overview

When you start a task, the system automatically constructs a comprehensive prompt that includes:
1. Base task template (from TASK_PROMPT_DEFAULTS.md)
2. Workflow context (expected statuses, input/output specs)
3. Skills (domain expertise for the agent)
4. Variable substitutions (task-specific details)
5. User input (enhancement spec file and task description)

This guide explains each component and how they combine.

---

## The Prompt Construction Pipeline

### Step-by-Step Process

```
1. User starts workflow
   ↓
2. System creates task with workflow metadata
   ↓
3. invoke_agent() function called
   ↓
4. Load base template (by task_type)
   ↓
5. Inject skills section
   ↓
6. Get workflow context (expected statuses, required output)
   ↓
7. Substitute all variables 
   ↓
8. Send final prompt to Claude
```

---

## Component 1: Base Template

**Source**: `.claude/docs/TASK_PROMPT_DEFAULTS.md`

Based on task type, one of these templates is loaded:
- `ANALYSIS_TEMPLATE` - For requirements-analyst tasks
- `TECHNICAL_ANALYSIS_TEMPLATE` - For architect tasks
- `IMPLEMENTATION_TEMPLATE` - For implementer tasks
- `TESTING_TEMPLATE` - For tester tasks
- `DOCUMENTATION_TEMPLATE` - For documenter tasks
- `INTEGRATION_TEMPLATE` - For integration coordinator tasks


**Key Variables:** In each template, the following variables are substituted:
- `${agent}` - Agent name (e.g., "requirements-analyst")
- `${agent_config}` - Path to agent .md file
- `${task_description}` - Task description
- `${enhancement_name}` - Enhancement name
- `${input_instruction}` - "Read file: ..." or "Read directory: ..."
- `${enhancement_dir}` - Enhancement directory path
- `${required_output_filename}` - Filename from workflow
- `${expected_statuses}` - List of statuses from workflow
- `${task_id}` - Unique task ID

---

### Example: ANALYSIS_TEMPLATE

```markdown
You are the **${agent}** agent. Your configuration and instructions are in: `${agent_config}`

## Task: ${task_description}

You are working on enhancement: **${enhancement_name}**

## Input

${input_instruction}

## Output Requirements

Create the following directory structure:

${enhancement_dir}/${agent}/
├── required_output/
│   └── ${required_output_filename}  (REQUIRED)
└── optional_output/                  (OPTIONAL)

### Required Output File

You **must** create: `${enhancement_dir}/${agent}/required_output/${required_output_filename}`

This file must include a metadata header:
---
enhancement: ${enhancement_name}
agent: ${agent}
task_id: ${task_id}
timestamp: <ISO-8601-timestamp>
status: <your-completion-status>
---

## Status Output

At the end of your response, output your completion status.

**Expected Statuses for This Workflow:**
${expected_statuses}

**Other Acceptable Statuses:**
- `BLOCKED: <specific reason>` - Cannot proceed without intervention
- `NEEDS_CLARIFICATION: <what you need>` - Need more information

**Important:** Only the expected statuses listed above will trigger automatic workflow progression.

## Your Task

Read the agent configuration at `${agent_config}` for detailed instructions on your role and responsibilities, then complete the task described above.
```

---
## Component 2: Skills Section

Using skills is an important part of the agent's overall effectiveness. 
Agents can use specialized skills to enhance their capabilities. 

**Source**: `.claude/skills/{skill-directory}/SKILL.md`

The skills system automatically injects domain expertise based on agent configuration.

### How Skills Are Selected

**From agent frontmatter** (`.claude/agents/requirements-analyst.md`):
```yaml
---
skills: ["requirements-elicitation", "user-story-writing", "bug-triage"]
---
```

**System loads these skills**:
1. `.claude/skills/requirements-elicitation/SKILL.md`
2. `.claude/skills/user-story-writing/SKILL.md`
3. `.claude/skills/bug-triage/SKILL.md`

**Built by**: `skills-commands.sh` → `build_skills_prompt()` function.

### Skills Section Structure

```markdown
################################################################################
## SPECIALIZED SKILLS AVAILABLE
################################################################################

You have access to the following specialized skills that enhance your capabilities.
Use these skills when they are relevant to your task:

---

# Requirements Elicitation

## Purpose
Extract complete, unambiguous requirements from user specifications...

## When to Use
- Analyzing new feature requests
- Processing enhancement specifications
...

## Key Capabilities
1. **Extract Requirements** - Identify functional and non-functional requirements
2. **Clarify Ambiguities** - Flag unclear specifications
...

## Approach
1. Read entire specification thoroughly
2. Extract explicit requirements
3. Identify implicit requirements
...

## Example
**Context**: Feature request to "add export functionality"
...

## Best Practices
- ✅ Ask "what" questions, not "how"
- ✅ Document assumptions explicitly
...

---

# User Story Writing

[Similar structure for next skill...]

---

**Using Skills**: Apply the above skills as appropriate to accomplish your objectives.

################################################################################
```

---

## Component 3: Workflow Context

**Source**: Workflow template + task metadata

### Workflow Context Extraction

**From task metadata**:
```json
{
  "workflow_name": "new_feature_development",
  "workflow_step": 0
}
```

**System looks up** in `workflow_templates.json`:
```json
{
  "workflows": {
    "new_feature_development": {
      "steps": [
        {
          "agent": "requirements-analyst",
          "input": "enhancements/{enhancement_name}/{enhancement_name}.md",
          "required_output": "analysis_summary.md",
          "on_status": {
            "READY_FOR_DEVELOPMENT": {
              "next_step": "architect",
              "auto_chain": true
            }
          }
        }
      ]
    }
  }
}
```

### Extracted Information

**1. Required Output Filename**:
```
From workflow step: "analysis_summary.md"
```

**2. Expected Statuses**:
```
From workflow on_status keys: ["READY_FOR_DEVELOPMENT"]
```

**3. Input Instruction**:
```
From workflow input + file type detection:
"Read and process this file: enhancements/my-feature/my-feature.md"
```

---

## Component 4: Variable Substitution

**Function**: `invoke_agent()` in `agent-commands.sh`

### Variables Substituted

```bash
# Basic task info
prompt="${prompt//\$\{agent\}/$agent}"
# Example: "requirements-analyst"

prompt="${prompt//\$\{agent_config\}/$agent_config}"
# Example: ".claude/agents/requirements-analyst.md"

prompt="${prompt//\$\{task_description\}/$task_description}"
# Example: "Analyze requirements for user authentication"

prompt="${prompt//\$\{task_id\}/$task_id}"
# Example: "task_1732123456_12345"

# Enhancement context
prompt="${prompt//\$\{enhancement_name\}/$enhancement_name}"
# Example: "user-auth"

prompt="${prompt//\$\{enhancement_dir\}/$enhancement_dir}"
# Example: "enhancements/user-auth"

# Workflow-driven values
prompt="${prompt//\$\{input_instruction\}/$input_instruction}"
# Example: "Read and process this file: enhancements/user-auth/user-auth.md"

prompt="${prompt//\$\{required_output_filename\}/$required_output_filename}"
# Example: "analysis_summary.md"

prompt="${prompt//\$\{expected_statuses\}/$expected_statuses}"
# Example: "- `READY_FOR_DEVELOPMENT`"
```

---

## Where User Input Goes

The user controls the prompt in **two main ways**:

### 1. Enhancement Specification File (Primary User Input)

**File**: `enhancements/{enhancement_name}/{enhancement_name}.md`

This is the **main user input** that agents process. The user writes their requirements, feature description, and acceptance criteria here.

**Example**:
```markdown
# User Authentication Feature

## Description
Add user login and registration functionality with email verification.

## Acceptance Criteria
- Users can register with email/password
- Email verification required before login
- Password must meet strength requirements (8+ chars, number, special char)
- Login generates JWT token
- Logout invalidates token

## Technical Notes
- Use bcrypt for password hashing
- JWT tokens expire after 24 hours
- Email sent via SendGrid API

## Security Considerations
- Rate limit login attempts
- Log failed authentication attempts
- Implement account lockout after 5 failed attempts
```

**This content is read by the agent** via the input instruction:
```markdown
## Input

Read and process this file: enhancements/user-auth/user-auth.md
```

The agent then analyzes this user-provided content to complete its task.

### 2. Task Description (Secondary means of adding context to the main input)

**When using workflows** (recommended):
```bash
cmat workflow start new_feature_development user-auth
```

**Task description is auto-generated**:
```
"Workflow: new_feature_development, Step 0"
```

**When creating manual tasks** (advanced):
```bash
cmat queue add \
  "Custom Task Title" \
  "requirements-analyst" \
  "high" \
  "analysis" \
  "enhancements/user-auth/user-auth.md" \
  "YOUR CUSTOM DESCRIPTION HERE"  # ← User can customize this
  true \
  true
```

**Task description appears in prompt**:
```markdown
## Task: YOUR CUSTOM DESCRIPTION HERE
```

### User Input Flow - Workflow based on Enhancement Specification

```
User writes:
  enhancements/user-auth/user-auth.md
    ↓
User starts workflow:
  cmat workflow start new_feature_development user-auth
    ↓
System builds prompt including:
  - Base template
  - Skills
  - Workflow context
  - Points to user's spec file
    ↓
Agent receives prompt with:
  "Read and process this file: enhancements/user-auth/user-auth.md"
    ↓
Agent reads user's spec file and processes it
```

**Key Point**: The **enhancement specification file** is the primary way users communicate what they want built. The prompt tells the agent to read and process that user-provided file.

### User Input Flow - Manual Task Creation (Maximum Control)

```
User creates task manually with custom description:
  cmat queue add \
    "Analyze authentication security" \
    "requirements-analyst" \
    "high" \
    "analysis" \
    "enhancements/user-auth/user-auth.md" \
    "Focus on OAuth2 integration and JWT token security. Identify potential vulnerabilities and recommend best practices for secure authentication flow."
    ↓
System builds prompt including:
  - Base template
  - Skills
  - User's custom task description
  - Points to source file
    ↓
Agent receives prompt with:
  ## Task: Focus on OAuth2 integration and JWT token security. Identify potential vulnerabilities and recommend best practices for secure authentication flow.
  
  ## Input
  Read and process this file: enhancements/user-auth/user-auth.md
    ↓
Agent reads source file AND follows user's specific instructions in task description
```

**Best for**: 
- Custom focus or specific instructions for the agent
- Non-standard analysis or processing
- Directing agent attention to specific concerns
- Ad-hoc tasks without workflow automation

**User Control**:
- ✅ Choose which agent to use
- ✅ Write custom task description (specific instructions)
- ✅ Point to any file or directory as input
- ✅ Control automation (auto_complete, auto_chain)
- ✅ Set priority
- ❌ No workflow metadata (unless manually added)
- ❌ No automatic expected statuses (generic message shown instead)

**Example with no auto-completion**:
```bash
TASK_ID=$(cmat queue add \
  "Security-focused requirements analysis" \
  "requirements-analyst" \
  "critical" \
  "analysis" \
  "enhancements/user-auth/user-auth.md" \
  "Analyze authentication requirements with emphasis on security vulnerabilities, OWASP compliance, and secure credential storage. Identify any potential attack vectors." \
  false \
  false)

cmat queue start $TASK_ID
# User will be prompted to confirm completion
# User will be prompted to decide on next step
# Maximum control over workflow
```

**Key Point**: The `task_description` parameter is **freeform text** that appears in the prompt as specific instructions to the agent. Users can write whatever guidance they want the agent to follow.

### Input Parameters

When user runs:
```bash
cmat workflow start new_feature_development user-auth
```

The system creates a task with these parameters:
```bash
agent="requirements-analyst"                    # From workflow step 0
task_id="task_1732123456_12345"                # Generated by system
source_file="enhancements/user-auth/user-auth.md"  # From workflow input
task_type="analysis"                           # From agent role
task_description="Workflow: new_feature_development, Step 0"  # System-generated
workflow_name="new_feature_development"        # User-specified workflow
workflow_step=0                                # First step
```

**User Input**:
- ✅ Workflow name (which template to use)
- ✅ Enhancement name (which spec file to process)
- ✅ Enhancement spec file content (the actual requirements/description)

**System-Generated**:
- Task ID, task type, task description, step number

### Step 1: Load Base Template

```markdown
You are the **${agent}** agent...
## Task: ${task_description}
...
```

### Step 2: Inject Skills

```markdown
[Base template content...]

################################################################################
## SPECIALIZED SKILLS AVAILABLE
################################################################################

---

# Requirements Elicitation
[Complete skill content...]

---

# User Story Writing
[Complete skill content...]

---

# Bug Triage
[Complete skill content...]

---
```

### Step 3: Get Workflow Context

From `workflow_templates.json` step 0:
```json
{
  "agent": "requirements-analyst",
  "input": "enhancements/{enhancement_name}/{enhancement_name}.md",
  "required_output": "analysis_summary.md",
  "on_status": {
    "READY_FOR_DEVELOPMENT": {"next_step": "architect", "auto_chain": true}
  }
}
```

**Extracts**:
- `required_output_filename` = "analysis_summary.md"
- `expected_statuses` = "- `READY_FOR_DEVELOPMENT`"
- `input_instruction` = "Read and process this file: enhancements/user-auth/user-auth.md"

### Step 4: Substitute Variables

**Before substitution**:
```markdown
You are the **${agent}** agent...
## Task: ${task_description}
You are working on enhancement: **${enhancement_name}**
...
**Expected Statuses for This Workflow:**
${expected_statuses}
```

**After substitution**:
```markdown
You are the **requirements-analyst** agent...
## Task: Analyze user authentication requirements
You are working on enhancement: **user-auth**
...
**Expected Statuses for This Workflow:**
- `READY_FOR_DEVELOPMENT`
```

### Final Assembled Prompt

```markdown
You are the **requirements-analyst** agent. Your configuration and instructions are in: `.claude/agents/requirements-analyst.md`

## Task: Analyze user authentication requirements

You are working on enhancement: **user-auth**

## Input

Read and process this file: enhancements/user-auth/user-auth.md

## Output Requirements

Create the following directory structure:

enhancements/user-auth/requirements-analyst/
├── required_output/
│   └── analysis_summary.md  (REQUIRED)
└── optional_output/                  (OPTIONAL)

### Required Output File

You **must** create: `enhancements/user-auth/requirements-analyst/required_output/analysis_summary.md`

This file must include a metadata header:
---
enhancement: user-auth
agent: requirements-analyst
task_id: task_1732123456_12345
timestamp: <ISO-8601-timestamp>
status: <your-completion-status>
---

### Optional Outputs

Place any additional supporting documents in: `enhancements/user-auth/requirements-analyst/optional_output/`

## Status Output

At the end of your response, output your completion status.

**Expected Statuses for This Workflow:**
- `READY_FOR_DEVELOPMENT`

**Other Acceptable Statuses:**
- `BLOCKED: <specific reason>` - Cannot proceed without intervention
- `NEEDS_CLARIFICATION: <what you need>` - Need more information

**Important:** Only the expected statuses listed above will trigger automatic workflow progression. Any other status will stop the workflow and require manual intervention.

## Your Task

Read the agent configuration at `.claude/agents/requirements-analyst.md` for detailed instructions on your role and responsibilities, then complete the task described above.

################################################################################
## SPECIALIZED SKILLS AVAILABLE
################################################################################

You have access to the following specialized skills that enhance your capabilities.
Use these skills when they are relevant to your task:

---

# Requirements Elicitation

## Purpose
Extract complete, unambiguous requirements from user specifications, identifying what needs to be built while clarifying unclear or missing information.

## When to Use
- Analyzing new feature requests
- Processing enhancement specifications
- Breaking down large features into components
- Identifying missing information in requirements

## Key Capabilities
1. **Extract Requirements** - Identify functional and non-functional requirements
2. **Clarify Ambiguities** - Flag unclear specifications and ask targeted questions
3. **Identify Constraints** - Find technical, business, and resource limitations

## Approach
1. Read entire specification thoroughly
2. Extract explicit requirements (stated clearly)
3. Identify implicit requirements (assumed but not stated)
4. Flag ambiguities and inconsistencies
5. Document acceptance criteria for each requirement

## Example
**Context**: Feature request to "add export functionality"

**Approach**:
- What formats? (CSV, JSON, PDF?)
- What data to export? (All fields or subset?)
- Who can export? (All users or admins only?)
- Size limits? (Max rows, file size?)
- Output: Clear requirements with acceptance criteria

## Best Practices
- ✅ Ask "what" questions, not "how"
- ✅ Document assumptions explicitly
- ✅ Create testable acceptance criteria
- ❌ Avoid: Making technical implementation decisions

---

# User Story Writing

[Similar detailed structure...]

---

# Bug Triage

[Similar detailed structure...]

---

**Using Skills**: Apply the above skills as appropriate to accomplish your objectives.
Reference specific skills in your work when they guide your approach or decisions.

################################################################################
```

---

## Viewing Prompts

### Preview Before Execution

```bash
# Preview what would be sent to agent
cmat queue preview-prompt <task_id>
```

This shows the **complete assembled prompt** before the agent runs.

### View After Execution

```bash
# Check agent logs
cat enhancements/feature/logs/requirements-analyst_task_*.log
```

Logs include:
```
===================================================================
PROMPT SENT TO AGENT
===================================================================

[Complete prompt as sent to Claude]

===================================================================
END OF PROMPT
===================================================================
```

---

## Customizing Prompts

There are several ways to customize prompts, depending on your needs and how permanent you want the change to be.

### Method 1: Edit Base Templates

**File**: `.claude/docs/TASK_PROMPT_DEFAULTS.md`

Modify the base template for a task type:
```markdown
# ANALYSIS_TEMPLATE

[Your custom instructions here...]

You are the **${agent}** agent...
[Rest of template...]

===END_TEMPLATE===
```

**Affects**: All tasks of that type

### Method 2: Customize Agent Configuration

**File**: `.claude/agents/{agent}.md`

The prompt instructs agents to read their config file:
```markdown
## Your Task

Read the agent configuration at `${agent_config}` for detailed instructions...
```

So agents see:
```markdown
Read the agent configuration at `.claude/agents/requirements-analyst.md` for detailed instructions...
```

Update the agent .md file to change:
- Role description
- Core responsibilities
- Scope boundaries
- Best practices

**Affects**: All tasks for that agent

### Method 3: Add/Modify Skills

**Files**: `.claude/skills/{skill}/SKILL.md`

Skills are automatically injected. To customize:

1. Edit existing skill content
2. Create new skills
3. Assign different skills to agents

**Affects**: All agents with that skill assigned.  If this is a new skill, you must also add it to the agent's frontmatter and `skills.json`.

### Method 4: Workflow-Level Customization

**File**: `.claude/queues/workflow_templates.json`

Workflows inject:
- Expected statuses (from `on_status` keys)
- Required output filename
- Input paths

Change these in workflow definition to customize behavior.

**Affects**: Only workflows using that template

## Method 5: Task-Level Customization

**Task Description**: You can add custom instructions to the task description to supplement or override the base template.

Workflows injects the Task description (from `task_description` parameter)

---

## Prompt Flow Example

### User Action
```bash
cmat workflow start new_feature_development user-auth
```

### System Actions

**1. Creates Task**:
```json
{
  "id": "task_1732123456_12345",
  "assigned_agent": "requirements-analyst",
  "task_type": "analysis",
  "source_file": "enhancements/user-auth/user-auth.md",
  "description": "Workflow: new_feature_development, Step 0",
  "metadata": {
    "workflow_name": "new_feature_development",
    "workflow_step": 0
  }
}
```

**2. invoke_agent() Called**:
```bash
invoke_agent \
  "requirements-analyst" \
  "task_1732123456_12345" \
  "enhancements/user-auth/user-auth.md" \
  "enhancements/user-auth" \
  "analysis" \
  "Workflow: new_feature_development, Step 0" \
  "true" \
  "true"
```

**3. Loads ANALYSIS_TEMPLATE**:
```bash
template=$(awk '/^# ANALYSIS_TEMPLATE$/{flag=1; next} /^===END_TEMPLATE===$/{flag=0} flag' \
    .claude/docs/TASK_PROMPT_DEFAULTS.md)
```

**4. Builds Skills Section**:
```bash
skills_section=$(cmat skills prompt requirements-analyst)
template="${template}${skills_section}"
```

**5. Gets Workflow Context**:
```bash
# From task metadata → workflow_templates.json
workflow_name="new_feature_development"
workflow_step=0

# Extracts from step 0:
required_output_filename="analysis_summary.md"
expected_statuses="- \`READY_FOR_DEVELOPMENT\`"
```

**6. Determines Input Type**:
```bash
if [ -f "enhancements/user-auth/user-auth.md" ]; then
  input_instruction="Read and process this file: enhancements/user-auth/user-auth.md"
fi
```

**7. Substitutes All Variables**:
```bash
prompt="${template//\$\{agent\}/requirements-analyst}"
prompt="${prompt//\$\{task_description\}/Workflow: new_feature_development, Step 0}"
prompt="${prompt//\$\{enhancement_name\}/user-auth}"
# ... and so on for all variables
```

**8. Sends to Claude**:
```bash
claude --permission-mode bypassPermissions "$prompt"
```

---

## Variables Reference

### Always Available

| Variable | Example Value | Source |
|----------|---------------|--------|
| `${agent}` | "requirements-analyst" | Task parameter |
| `${agent_config}` | ".claude/agents/requirements-analyst.md" | Derived from agent |
| `${task_id}` | "task_1732123456_12345" | Generated |
| `${task_description}` | "Analyze requirements..." | Task parameter |
| `${task_type}` | "analysis" | Task parameter |
| `${enhancement_name}` | "user-auth" | Extracted from source path |
| `${enhancement_dir}` | "enhancements/user-auth" | Derived |

### Workflow-Driven Variables (v5.0)

| Variable | Example Value | Source |
|----------|---------------|--------|
| `${input_instruction}` | "Read and process this file: ..." | Workflow + file type detection |
| `${required_output_filename}` | "analysis_summary.md" | Workflow step definition |
| `${expected_statuses}` | "- \`READY_FOR_DEVELOPMENT\`" | Workflow on_status keys |

### Skills Variables

Skills section is built dynamically:
- Loads each skill assigned to agent
- Concatenates skill content
- Wraps in standard header/footer

---

## Troubleshooting Prompts

### View Complete Prompt

**Before execution**:
```bash
cmat queue preview-prompt <task_id>
```

**After execution**:
```bash
# Check agent log
cat enhancements/feature/logs/agent_task_*.log

# Look for section:
# ===================================================================
# PROMPT SENT TO AGENT
# ===================================================================
```

### Check Variable Substitution

```bash
# Preview prompt and check specific variable
cmat queue preview-prompt <task_id> | grep "enhancement:"
cmat queue preview-prompt <task_id> | grep "Expected Statuses"
cmat queue preview-prompt <task_id> | grep "required_output"
```

### Verify Skills Injection

```bash
# Check if skills were included
cmat queue preview-prompt <task_id> | grep "SPECIALIZED SKILLS"

# Count skills injected
cmat queue preview-prompt <task_id> | grep -c "^# " | tail -1
# Should match number of skills assigned to agent
```

---

## Prompt Size Considerations

### Approximate Sizes

**Base Template**: ~500 tokens
**Per Skill**: ~300-800 tokens each
**Agent Config Reference**: Loaded by Claude on demand

**Example Totals**:
- Requirements Analyst (3 skills): ~2000-3000 tokens
- Architect (4 skills): ~2500-3500 tokens
- Implementer (3 skills): ~2000-3000 tokens

### Managing Prompt Size

**If prompts too large**:
1. Reduce skills assigned to agents (keep 2-3 most relevant)
2. Shorten skill content (make more concise)
3. Simplify base templates

**Note**: Agent .md files are referenced, not included in prompt, so their size doesn't matter.

---
## Best Practices

### DO:
- ✅ Preview prompts before execution (use `preview-prompt`)
- ✅ Keep skills concise (300-800 tokens each)
- ✅ Assign 2-4 relevant skills per agent
- ✅ Use workflow templates to customize behavior
- ✅ Check logs to see actual prompts sent

### DON'T:
- ❌ Edit generated prompts directly (they're rebuilt each time)
- ❌ Assign too many skills (bloats prompt)
- ❌ Make base templates too verbose
- ❌ Include sensitive data in templates or skills


---

For complete command reference, see [SCRIPTS_REFERENCE.md](SCRIPTS_REFERENCE.md).