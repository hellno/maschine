import os
from typing import Tuple

from openai import OpenAI


def get_deepseek_client() -> OpenAI:
    """Get a Deepseek client."""
    return OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com/v1"
    )


def get_openai_client() -> OpenAI:
    """Get an OpenAI client."""
    return OpenAI(
        api_key=os.environ["REAL_OPENAI_API_KEY"], base_url="https://api.openai.com/v1"
    )


def get_venice_ai_client() -> OpenAI:
    """Get a Venice AI client."""
    return OpenAI(
        api_key=os.environ["VENICE_AI_API_KEY"], base_url="https://api.venice.ai/api/v1"
    )


def send_prompt_to_reasoning_model(prompt: str) -> Tuple[str, str]:
    client = get_venice_ai_client()
    response = client.chat.completions.create(
        model="deepseek-r1-671b",
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    content = response.choices[0].message.content.strip()
    reasoning = content.split("</think>")[0].split("<think>")[1].strip()
    response = reasoning.split("</think>")[1].strip()
    return response, reasoning


def generate_project_name(prompt: str) -> str:
    """Generate a project name from the user's prompt using LLM."""
    deepseek = get_deepseek_client()

    try:
        response = deepseek.chat.completions.create(
            model="deepseek-chat",
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
        print(f'generate_project_name: response "{llm_content}"')
        project_name = llm_content.split("\n")[0].replace('"', "").strip()
        print(f'generate_project_name: project_name "{project_name}"')
        return project_name[:50]  # Limit length
    except Exception as e:
        print(f"Warning: Could not generate project name: {e}")
        return "new-frame-project"


QUERY_GEN_STR = """\
You are a technical query refinement assistant. Transform the following user project description into up to {num_queries} concise, highly technical search queries — one per line—that will help retrieve relevant API documentation. 
Your queries should:
• Identify specific API endpoints, function or method names, or SDK operations implied by the description.
• Use precise, domain-specific terminology.

If no clear API-related details are present, do not generate any queries.
"""

# ai! add simple timing measurment to this function
def generate_search_queries_from_user_input(
    user_input: str, num_queries: int = 2
) -> list[str]:
    """Generate expanded technical queries for documentation search."""
    print(f"Generating queries from prompt: {user_input}")

    try:
        client = get_venice_ai_client()
        system_prompt = QUERY_GEN_STR.format(num_queries=num_queries)

        response = client.chat.completions.create(
            model="llama-3.1-405b",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Original user input: {user_input} Refined search queries:",
                },
            ],
        )

        llm_content = response.choices[0].message.content.strip()
        print("Raw model response:", llm_content)

        queries = [q.strip() for q in llm_content.split("\n") if q.strip()]
        print(f"Generated queries: {queries}")
        return queries

    except Exception as e:
        print(f"Query generation failed: {e}")
        return []
