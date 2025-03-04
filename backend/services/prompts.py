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
You are a technical expert designing a Farcaster Frame v2 application.
We have an existing nextjs typescript template with common UI components.
It has scaffolding to make the project a complete Frame v2 application (meta tags to indicate the webapp is a Frame v2).
We need to fill in the content based on the user request.
CRITICAL: Frames v2 provides full HTML/CSS/JS capabilities with no button limits.

USER REQUEST: {prompt}

TECHNICAL CONTEXT: {context}

Create a detailed specification document with these sections:

1. OVERVIEW
   - Core functionality
   - UX flow

2. TECHNICAL REQUIREMENTS
    - Frontend components using HTML/CSS/JS (leverage the full canvas)
    - API integrations (only use APIs mentioned in context)
    - Client-side state management approach
    - Mobile responsiveness strategy

3. FRAMES v2 IMPLEMENTATION
    - Interactive canvas elements
    - Animation and transition effects
    - User input handling (not limited to buttons)
    - Notification integration (if applicable)
    - Saving/sharing capabilities

5. MOBILE CONSIDERATIONS
    - Touch interaction patterns
    - Responsive layout techniques
    - Performance optimization

4. CONSTRAINTS COMPLIANCE
   - Confirm: No database requirements
   - Confirm: No smart contract deployments

FORMAT YOUR RESPONSE AS A DETAILED MARKDOWN DOCUMENT.
"""

CREATE_TASK_PLAN_PROMPT = """
You are a technical expert designing a Farcaster Frame v2 application.

Based on this specification:

{spec}

Create a development plan that:
1. Breaks down implementation into logical phases
2. Implements modern web interactions (not limited to basic buttons)
3. Properly handles mobile touch interfaces
4. Utilizes client-side storage when appropriate
5. Constraints: No database or custom smart contracts to deploy

For each development phase:
 - Describe what will be built
 - List technical components/APIs needed
 - Identify potential challenges
 - Consider mobile-specific behaviors

FORMAT AS A MARKDOWN DOCUMENT with clear task phases and dependencies.
"""


CREATE_TODO_LIST_PROMPT = """
You are a technical expert designing a Farcaster Frame v2 application.

Based on this development plan:

{plan}

Create an actionable todo list where:

1. Each task is concrete and implementable
2. Tasks are ordered by dependency (foundation first)
3. Tasks leverage the full HTML/CSS/JS canvas of Frames v2
4. Mobile responsiveness is explicitly addressed
5. NO tasks require creating databases or deploying smart contracts
6. Frames v2 capabilities are fully utilized
7. Leveraging the existing nextjs typescript template with shadcn UI components

Format each task as:
- [ ] Task description with component affected

Group tasks into these categories:
- Frame Structure
- UI Components & Interactions
- API Integration
- Client-Side State Management
- User Experience & Animations
- Mobile Optimization

IMPORTANT: Do NOT impose Farcaster frames v1 limitations (like 4-button limits or image-only rendering).
"""

IMPLEMENT_TODO_LIST_PROMPT = """
You are an expert Farcaster Frame v2 developer implementing a project based on your todo list.
CRITICAL: Frames v2 offers full HTML/CSS/JS canvas capabilities with NO button limitations.

Code the next highest priority task from the todo list.

### Instructions
1. Find the highest priority uncompleted task
2. Implement focused, working code (no unnecessary complexity or enterprise-level features)
3. Build using modern web standards for the interactive canvas
4. Optimize for touch interfaces on mobile
3. Verify the implementation meets the task requirement
4. Update the todo list to reflect completed work

For each task you complete:
- Create/modify the necessary files with proper HTML/CSS/TypeScript
- Mark completed tasks with [x]
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
