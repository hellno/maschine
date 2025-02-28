CLARIFY_INTENT_PROMPT = """
## Extract User Intent
Distill the core functionality request into clear technical requirements.

### Instructions
1. Identify the main crypto/web3 feature requested
2. Extract essential Frame UI requirements
3. Define the core user flow in 3-5 steps

### Output
- Primary Function: [One sentence]
- Key Requirements: [3-5 bullet points]
- User Flow: [Step-by-step journey]
- Technical Constraints: [Frame-specific limitations]

### User Request
{prompt}
"""

FEASIBILITY_CHECK_PROMPT = """
## Rapid Feasibility Check
Determine if this can be built within Frame limitations.

### Frame Constraints
- Limited to 4 button actions
- No persistent state between frames
- Limited UI components
- Image-based UI rendering

### Requirements
{requirements}

### Output
- Feasibility: [Yes/No/Partial]
- Critical Challenges: [1-2 bullet points]
- Suggested Approach: [1-2 sentences]
"""

CREATE_SPEC_PROMPT = """
## Minimal Implementation Spec
Create a focused spec addressing the core user need.
We have an existing Farcaster miniapp (Frame v2) template based on Next.js using typescript.
We need to customize this template in form and function to meet the user requirements.

### Output Format
1. Core Functionality
   - Main user flow
   - Required API endpoints
   - Key data structures

2. Implementation Approach
   - Frame structure (screens/actions)
   - External API integration points
   - State management approach

3. Technical Considerations
   - API authentication needs
   - Critical error scenarios

### API Context
{context}

### User Prompt
{prompt}
"""

CREATE_TASK_PLAN_PROMPT = """
## Implementation Tasks
Break down the spec into ordered coding tasks.

### Instructions
Create a stepped implementation plan where:
1. Each step builds on previous work
2. Core functionality comes first
3. Tasks are small enough to implement in 30-45 mins
4. Focus on making each step functional, not perfect

### Output Format
### Step 1: [Action-focused title]
```text
- Build: [What to implement]
- Outcome: [How to verify it works]
```

### Step 2: [Action-focused title]
```text
- Build: [What to implement]
- Outcome: [How to verify it works]

### Specification
{spec}
"""


CREATE_TODO_LIST_PROMPT = """## Make a Coding Task List
 Generate an executable task list focusing on immediate implementation steps based on the implementation plan.

 ### Instructions
 Create tasks that:
 1. Specify exact files to create/modify
 2. Include code snippets or function signatures needed
 3. List explicit API endpoints and their methods
 4. Order tasks by implementation sequence
 5. Contain verifiable completion criteria, but no specific tests needed
 6. Reference specific UI components to implement

 ### Output Format
 - [ ] Task 1: Create [description]
   File: path/to/file.ext
   Action: Create x/Add y/Change from z to y
   Description: xyz
 - [ ] Task 2: ...

### Implementation Plan
{plan}
"""

IMPLEMENT_TODO_LIST_PROMPT = """Code the next highest priority task from the todo list.

### Instructions
1. Find the highest priority uncompleted task
2. Implement focused, working code (not perfect)
3. Add brief comments on complex logic
4. Verify the implementation meets the task requirement
5. Update the todo list to reflect completed work
"""

RETRY_IMPLEMENT_TODO_LIST_PROMPT = f"""{IMPLEMENT_TODO_LIST_PROMPT}

If there are no todo items left, skip this step and move on without changing anything.
"""

FIX_PROBLEMS_PROMPT = """## Fix Implementation Issues
Address specific problems with the current implementation and get it working.

### Instructions
1. Focus on critical problems first - get something working
2. Prioritize fixing:
   - Broken user flows
   - Rendering issues
   - API integration failures
   - State management problems
3. Make minimal changes needed to fix the issue
4. Update the todo list to related todos if their status is changed

"""
