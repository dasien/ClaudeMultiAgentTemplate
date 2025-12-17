# Task Prompt Defaults

This file contains the default prompt templates used for different task types. These templates are loaded by the queue manager and customized with task-specific information before being sent to agents.

Variables available for substitution:
- `${agent}` - Agent name
- `${agent_config}` - Path to agent configuration file
- `${source_file}` - Path to source file or directory
- `${task_description}` - Task description
- `${task_id}` - Unique task identifier
- `${task_type}` - Type of task
- `${enhancement_name}` - Enhancement name
- `${enhancement_dir}` - Enhancement directory path
- `${input_instruction}` - Instruction for reading input (file or directory)
- `${required_output_filename}` - Required output filename
- `${expected_statuses}` - List of expected status codes from workflow

# ANALYSIS_TEMPLATE

You are the **${agent}** agent. Your configuration and instructions are in: `${agent_config}`

## Task: ${task_description}

You are working on enhancement: **${enhancement_name}**

## Input

${input_instruction}

## Output Requirements

Create the following directory structure:

```
${enhancement_dir}/${agent}/
├── required_output/
│   └── ${required_output_filename}  (REQUIRED)
└── optional_output/                  (OPTIONAL)
    └── [any additional files]
```

### Required Output File

You **must** create: `${enhancement_dir}/${agent}/required_output/${required_output_filename}`

This file must include a metadata header:
```markdown
---
enhancement: ${enhancement_name}
agent: ${agent}
task_id: ${task_id}
timestamp: <ISO-8601-timestamp>
status: <your-completion-status>
---
```

### Optional Outputs

Place any additional supporting documents in: `${enhancement_dir}/${agent}/optional_output/`

These might include:
- Detailed analysis notes
- Research findings
- Alternative approaches considered
- Risk assessments

## Completion Block

At the end of your response, you **must** output a completion block in this exact format:

```yaml
---
agent: ${agent}
task_id: ${task_id}
status: <STATUS>
---
```

The `status` field must be one of the following:

${expected_statuses}

## Your Task

Read the agent configuration at `${agent_config}` for detailed instructions on your role and responsibilities, then complete the analysis task described above.

===END_TEMPLATE===

# TECHNICAL_ANALYSIS_TEMPLATE

You are the **${agent}** agent. Your configuration and instructions are in: `${agent_config}`

## Task: ${task_description}

You are working on enhancement: **${enhancement_name}**

## Input

${input_instruction}

## Output Requirements

Create the following directory structure:

```
${enhancement_dir}/${agent}/
├── required_output/
│   └── ${required_output_filename}  (REQUIRED)
└── optional_output/                  (OPTIONAL)
    └── [any additional files]
```

### Required Output File

You **must** create: `${enhancement_dir}/${agent}/required_output/${required_output_filename}`

This file must include a metadata header:
```markdown
---
enhancement: ${enhancement_name}
agent: ${agent}
task_id: ${task_id}
timestamp: <ISO-8601-timestamp>
status: <your-completion-status>
---
```

### Optional Outputs

Place any additional supporting documents in: `${enhancement_dir}/${agent}/optional_output/`

These might include:
- Architecture diagrams
- API specifications
- Data model designs
- Technology research

## Completion Block

At the end of your response, you **must** output a completion block in this exact format:

```yaml
---
agent: ${agent}
task_id: ${task_id}
status: <STATUS>
---
```

The `status` field must be one of the following:

${expected_statuses}

## Your Task

Read the agent configuration at `${agent_config}` for detailed instructions on your role and responsibilities, then complete the technical analysis task described above.

===END_TEMPLATE===

# IMPLEMENTATION_TEMPLATE

You are the **${agent}** agent. Your configuration and instructions are in: `${agent_config}`

## Task: ${task_description}

You are working on enhancement: **${enhancement_name}**

## Input

${input_instruction}

## Output Requirements

Create the following directory structure:

```
${enhancement_dir}/${agent}/
├── required_output/
│   └── ${required_output_filename}  (REQUIRED)
└── optional_output/                  (OPTIONAL)
    └── [any additional files]
```

### Required Output File

You **must** create: `${enhancement_dir}/${agent}/required_output/${required_output_filename}`

This file must include a metadata header:
```markdown
---
enhancement: ${enhancement_name}
agent: ${agent}
task_id: ${task_id}
timestamp: <ISO-8601-timestamp>
status: <your-completion-status>
---
```

### Optional Outputs

Place any additional supporting documents in: `${enhancement_dir}/${agent}/optional_output/`

These might include:
- Implementation notes
- Code change summaries
- Refactoring documentation
- Performance considerations

## Completion Block

At the end of your response, you **must** output a completion block in this exact format:

```yaml
---
agent: ${agent}
task_id: ${task_id}
status: <STATUS>
---
```

The `status` field must be one of the following:

${expected_statuses}

## Your Task

Read the agent configuration at `${agent_config}` for detailed instructions on your role and responsibilities, then complete the implementation task described above.

===END_TEMPLATE===

# TESTING_TEMPLATE

You are the **${agent}** agent. Your configuration and instructions are in: `${agent_config}`

## Task: ${task_description}

You are working on enhancement: **${enhancement_name}**

## Input

${input_instruction}

## Output Requirements

Create the following directory structure:

```
${enhancement_dir}/${agent}/
├── required_output/
│   └── ${required_output_filename}  (REQUIRED)
└── optional_output/                  (OPTIONAL)
    └── [any additional files]
```

### Required Output File

You **must** create: `${enhancement_dir}/${agent}/required_output/${required_output_filename}`

This file must include a metadata header:
```markdown
---
enhancement: ${enhancement_name}
agent: ${agent}
task_id: ${task_id}
timestamp: <ISO-8601-timestamp>
status: <your-completion-status>
---
```

### Optional Outputs

Place any additional supporting documents in: `${enhancement_dir}/${agent}/optional_output/`

These might include:
- Detailed test results
- Coverage reports
- Performance test data
- Bug reports

## Completion Block

At the end of your response, you **must** output a completion block in this exact format:

```yaml
---
agent: ${agent}
task_id: ${task_id}
status: <STATUS>
---
```

The `status` field must be one of the following:

${expected_statuses}

## Your Task

Read the agent configuration at `${agent_config}` for detailed instructions on your role and responsibilities, then complete the testing task described above.

===END_TEMPLATE===

# DOCUMENTATION_TEMPLATE

You are the **${agent}** agent. Your configuration and instructions are in: `${agent_config}`

## Task: ${task_description}

You are working on enhancement: **${enhancement_name}**

## Input

${input_instruction}

## Output Requirements

Create the following directory structure:

```
${enhancement_dir}/${agent}/
├── required_output/
│   └── ${required_output_filename}  (REQUIRED)
└── optional_output/                  (OPTIONAL)
    └── [any additional files]
```

### Required Output File

You **must** create: `${enhancement_dir}/${agent}/required_output/${required_output_filename}`

This file must include a metadata header:
```markdown
---
enhancement: ${enhancement_name}
agent: ${agent}
task_id: ${task_id}
timestamp: <ISO-8601-timestamp>
status: <your-completion-status>
---
```

### Optional Outputs

Place any additional supporting documents in: `${enhancement_dir}/${agent}/optional_output/`

These might include:
- User guide updates
- API documentation updates
- Additional examples
- Tutorial content

## Completion Block

At the end of your response, you **must** output a completion block in this exact format:

```yaml
---
agent: ${agent}
task_id: ${task_id}
status: <STATUS>
---
```

The `status` field must be one of the following:

${expected_statuses}

## Your Task

Read the agent configuration at `${agent_config}` for detailed instructions on your role and responsibilities, then complete the documentation task described above.

===END_TEMPLATE===

# INTEGRATION_TEMPLATE

You are the **${agent}** agent. Your configuration and instructions are in: `${agent_config}`

## Task: ${task_description}

You are working on enhancement: **${enhancement_name}**

## Input

${input_instruction}

## Output Requirements

Create the following directory structure:

```
${enhancement_dir}/${agent}/
├── required_output/
│   └── ${required_output_filename}  (REQUIRED)
└── optional_output/                  (OPTIONAL)
    └── [any additional files]
```

### Required Output File

You **must** create: `${enhancement_dir}/${agent}/required_output/${required_output_filename}`

Note: Integration agents may not require metadata headers. Check your agent configuration.

### Optional Outputs

Place any additional supporting documents in: `${enhancement_dir}/${agent}/optional_output/`

These might include:
- Integration logs
- Sync reports
- Error details

## Completion Block

At the end of your response, you **must** output a completion block in this exact format:

```yaml
---
agent: ${agent}
task_id: ${task_id}
status: <STATUS>
---
```

The `status` field must be one of the following:

${expected_statuses}

## Your Task

Read the agent configuration at `${agent_config}` for detailed instructions on your role and responsibilities, then complete the integration task described above.

===END_TEMPLATE===