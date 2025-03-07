from idlelib import undo
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

CREATE_SPEC_PROMPT = """You are a technical expert designing a Farcaster Frame v2 application.
We have an existing nextjs typescript template with common UI components.
It has scaffolding to make the project a complete Frame v2 application (meta tags to indicate the webapp is a Frame v2).
We need to fill in the content based on the user request.
CRITICAL: Frames v2 provides full HTML/CSS/Typescript capabilities with no button limits.

USER REQUEST: {prompt}

TECHNICAL CONTEXT: {context}

Create a detailed specification document with these sections:

1. OVERVIEW
   - Core functionality
   - UX flow

2. TECHNICAL REQUIREMENTS
    - use full responsive design, most users will be on mobile devices
    - don't hallucinate APIs, see context for relevant external sources

3. FRAMES v2 IMPLEMENTATION
    - Interactive canvas elements
    - User input handling (not limited to buttons)
    - Saving/sharing capabilities via Frames v2 SDK

5. MOBILE CONSIDERATIONS
    - Responsive layout techniques
    - Touch interaction patterns

4. CONSTRAINTS COMPLIANCE
    - Miniapp context: localstorage is available on each device without sync across devices
    - No database requirements, no migrations, no custom DB
    - No smart contract deployments
    - No third-party integrations beyond those mentioned in context
    - No unnecessary complexity or enterprise-level features
    - No need for QA or testing, this is a prototype. 90/10 impact to effort.

respond with markdown format with a focus on the spec, no code snippets needed here.
"""

CREATE_PROMPT_PLAN_PROMPT = """
You are a technical expert designing a Farcaster Frame v2 application.

Draft a detailed, step-by-step blueprint for building this project.
Then, once you have a solid plan, break it down into small, iterative chunks that build on each other.
Look at these chunks and then go another round to break it into small steps.
Review the results and make sure that the steps are small enough to be implemented safely, but big enough to move the project forward.
Iterate until you feel that the steps are right sized for this project.

From here you should have the foundation to provide a series of prompts for a code-generation LLM that will implement each step.
Prioritize best practices, and incremental progress, ensuring no big jumps in complexity at any stage.
Make sure that each prompt builds on the previous prompts, and ends with wiring things together.
There should be no hanging or orphaned code that isn't integrated into a previous step.

Make sure and separate each prompt section. Use markdown. Each prompt should be tagged as text using code tags. The goal is to output prompts, but context, etc is important as well.

Based on this specification:

{spec}

- Describe what will be built
- List technical components/APIs needed
- Consider mobile-specific behaviors
- We have an existing nextjs typescript template with common UI components. Remember to customize title and components of the template
- Constraints: No database or custom smart contracts to deploy
- no need for QA or testing, this is a prototype. 90/10 impact to effort.
- CRITICAL: Frames v2 provides full HTML/CSS/Typescript capabilities with no button limits

Create a list of prompts that will be used to generate code for the application.
"""


CREATE_TODO_LIST_PROMPT = """
You are a technical expert designing a Farcaster Frame v2 application.

Based on this prompt plan:

{plan}

Create an actionable todo list that I can use as a checklist.

1. Each task is concrete and implementable
2. Tasks are ordered by dependency (foundation first)
3. Try to aim for up to 20 tasks. Make sure that the whole application will be built when all tasks are completed
4. Don't repeat yourself and don't add new tasks or unnecessary complexity

Format each task as:
- [ ] Task description with component affected and user outcome
"""

IMPLEMENT_TODO_LIST_PROMPT = """You are an expert Farcaster Frame v2 developer implementing a project based on your todo list.
CRITICAL: Frames v2 offers full html canvas capabilities with NO button limitations.

Code the next highest priority task from the todo list.

### Instructions
1. Find the highest priority uncompleted todos
2. Use relevant prompt and context that was prepared for you in the prompt_plan.md
3. Implement focused, working code (no unnecessary complexity or enterprise-level features)
4. Verify the implementation meets the task requirement
5. Update the todo list to reflect completed work

For each task you complete:
- Create/modify the necessary files with proper TypeScript
- Mark completed tasks with [x]
"""

RETRY_IMPLEMENT_TODO_LIST_PROMPT = f"""{IMPLEMENT_TODO_LIST_PROMPT}

If there are no todo items left, skip this step and move on without changing anything.
"""

FIX_PROBLEMS_PROMPT = """Address specific problems with the current implementation and get it working.
# Instructions
1. Focus on critical problems first - get something working
2. Prioritize fixing:
   - Broken user flows
   - Rendering issues
   - API integration failures
   - State management problems
3. Make minimal changes needed to fix the issue
4. Update the todo list to related todos if their status is changed
"""
