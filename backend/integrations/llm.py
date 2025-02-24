import os
from typing import Tuple
from openai import OpenAI
from backend.utils.timing import measure_time


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


def get_together_ai_client() -> OpenAI:
    """Get a Together AI client."""
    return OpenAI(
        api_key=os.environ["TOGETHERAI_API_KEY"],
        base_url="https://api.together.xyz/v1",
    )


@measure_time
def send_prompt_to_reasoning_model(prompt: str) -> Tuple[str, str]:
    client = get_together_ai_client()
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-R1",
        temperature=0.6,
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    content = response.choices[0].message.content.strip()
    if "<think>" not in content and "</think>" not in content:
        return content, ""

    reasoning = content.split("</think>")[0].split("<think>")[1].strip()
    response = content.split("</think>")[1].strip()
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
You are a technical query refinement assistant. 
Transform the following user project description into up to {num_queries} concise, highly technical search queries — one per line — that will help retrieve relevant API documentation. 
Your queries should:
• Use precise, domain-specific terminology.
• Don't hallucinate or generate false information.
• be clear and concise for humans, no API calls or code snippets.

If no clear API-related details are present, do not generate any queries.
"""


@measure_time
def generate_search_queries_from_user_input(
    user_input: str, num_queries: int = 2
) -> list[str]:
    """Generate expanded technical queries for documentation search."""
    print(f"Generating queries from prompt: {user_input}")

    try:
        client = get_openai_client()
        system_prompt = QUERY_GEN_STR.format(num_queries=num_queries)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
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
        llm_content = llm_content.replace("`", "").strip()
        queries = [q.lstrip("-").strip() for q in llm_content.split("\n") if q]
        queries = [q for q in queries if q]
        print(f"Generated queries: {queries}")
        return queries

    except Exception as e:
        print(f"Query generation failed: {e}")
        return []
