import os

from openai import OpenAI


def get_deepseek_client() -> OpenAI:
    """Get a Deepseek client."""
    return OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com/v1"
    )


def improve_user_instructions(prompt: str) -> str:
    """Use LLM to improve and expand the user's instructions."""
    deepseek = get_deepseek_client()

    try:
        response = deepseek.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at improving and clarifying instructions for creating Farcaster Frames.",
                },
                {
                    "role": "user",
                    "content": f"Improve these instructions for creating a Farcaster Frame, adding specific technical details while keeping the original intent:\n\n{prompt}",
                },
            ],
            max_tokens=500,
        )
        reasoning_content = response.choices[0].message.reasoning_content
        content = response.choices[0].message.content.strip()
        print(f"Reasoning content: {reasoning_content}")
        print(f"Improved instructions: {content}")
        return content
    except Exception as e:
        print(f"Warning: Could not improve instructions: {str(e)}")
        return prompt


def generate_project_name(prompt: str) -> str:
    """Generate a project name from the user's prompt using LLM."""
    deepseek = get_deepseek_client()

    try:
        response = deepseek.chat.completions.create(
            model="deepseek-coder",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that generates short, memorable project names for a Farcaster Frame project. Only respond with one project name. 2-3 words max for this one name. no 'or' or &*/ chars.",
                },
                {
                    "role": "user",
                    "content": f"Generate one short, memorable project name based on this description: {prompt}",
                },
            ],
            max_tokens=50,
            temperature=2,
        )
        llm_content = response.choices[0].message.content.strip()
        project_name = llm_content.split("\n")[0].replace('"', "").strip()
        return project_name[:50]  # Limit length
    except Exception as e:
        print(f"Warning: Could not generate project name: {str(e)}")
        return "new-frame-project"
