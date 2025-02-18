import os

from openai import OpenAI


MODEL_NAME = "deepseek-chat"
# MODEL_NAME = "qwen32b" # venice ai model


def get_deepseek_client() -> OpenAI:
    """Get a Deepseek client."""
    # testing venice ai while deepseek is down
    # VENICE_AI_BASE_URL = "https://api.venice.ai/api/v1"
    # return OpenAI(api_key=os.environ["VENICE_AI_API_KEY"], base_url=VENICE_AI_BASE_URL)
    return OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com/v1"
    )


def generate_project_name(prompt: str) -> str:
    """Generate a project name from the user's prompt using LLM."""
    deepseek = get_deepseek_client()

    try:
        response = deepseek.chat.completions.create(
            model=MODEL_NAME,
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


def generate_search_queries_from_user_input(
    user_input: str, num_queries: int = 3
) -> list[str]:
    """Generate expanded technical queries for documentation search."""
    print(f"Generating queries from prompt: {user_input}")

    try:
        deepseek = get_deepseek_client()
        system_prompt = QUERY_GEN_STR.format(num_queries=num_queries)

        response = deepseek.chat.completions.create(
            model=MODEL_NAME,
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
