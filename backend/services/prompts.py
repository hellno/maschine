FARCASTER_DESCRIPTION = ""

CREATE_SPEC_PROMPT = """Compile our findings into a comprehensive, developer-ready specification. 
Include all relevant requirements, architecture choices, data handling details, error handling strategies, so a developer can immediately begin implementation.
API context:
{context}

User prompt:
{prompt}
"""

CREATE_SPEC_FROM_PLAN_PROMPT = """Draft a detailed, step-by-step blueprint for building this project. Then, once you have a solid plan, break it down into small, iterative chunks that build on each other. Look at these chunks and then go another round to break it into small steps. review the results and make sure that the steps are small enough to be implemented safely, but big enough to move the project forward. Iterate until you feel that the steps are right sized for this project.
From here you should have the foundation to provide a series of prompts for a code-generation LLM that will implement each step. Prioritize best practices, and incremental progress, ensuring no big jumps in complexity at any stage. Make sure that each prompt builds on the previous prompts, and ends with wiring things together. There should be no hanging or orphaned code that isn't integrated into a previous step.
Make sure and separate each prompt section. Use markdown. Each prompt should be tagged as text using code tags. The goal is to output prompts, but context, etc is important as well.

{spec}
"""

CREATE_TODO_LIST_PROMPT = """
Make a `todo.md` that I can use as a checklist for building this project.

{plan}
"""

IMPLEMENT_TODO_LIST_PROMPT = "Implement the todos described in `todo.md`. When you're done, you should have a working project. When you complete a task, mark it as done in the todo list."

RETRY_IMPLEMENT_TODO_LIST_PROMPT = "Validate that the todos in `todo.md` are implemented correctly. If you find any issues, fix them and mark the task as done in the todo list."
