CREATE_SPEC_PROMPT = """Convert raw user description and requirements into an implementation-ready specification.

## API Context
{context}

## User Requirements
{prompt}

## Output Format
1. Markdown document with these sections:
   - Functional User Requirements
   - Architecture Diagram
   - Data Flow Specification
   - Error Handling Strategies
2. Technical terms clearly defined"""

CREATE_SPEC_FROM_PLAN_PROMPT = """Implementation Plan Breakdown
1. Analyze provided specification
2. Break into sequential implementation steps
3. Validate step sizing (2-4 file changes per step)

## Prompt Generation Rules
- One discrete task per prompt
- Reference previous implementations
- Specify exact files to modify
- Include integration checks

## Step Format
### Step [N]: [Action-oriented Title]
```text
1. Primary objective
2. Required files
3. Implementation details
``` 

{spec}"""

CREATE_TODO_LIST_PROMPT = """## Checklist Requirements
Generate prioritized implementation tasks in markdown format

### Format Rules
- Categories: ### Core, ### API, ### UI
- Tasks start with [ ] 
- Ordered by dependencies
- Max 1hr per task
- Includes validation criteria

{plan}"""

IMPLEMENT_TODO_LIST_PROMPT = """## Current Todo State
{todo}

## Implementation Rules
1. Complete highest priority unchecked task
2. Verify against validation criteria
3. Mark [x] when done
4. Write production-grade code
5. Maintain existing functionality

## Required Outputs
- Updated todo.md
- Implement changes
"""

RETRY_IMPLEMENT_TODO_LIST_PROMPT = """## Validation Checks
1. Verify todo.md completion
2. Confirm requirement matching
3. Test error handling
4. Validate integrations

## Correction Protocol
1. Fix implementation gaps
2. Mark completed tasks

## Output Requirements
- Revised todo.md
- Implement changes
"""
