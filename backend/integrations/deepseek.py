import os

from openai import OpenAI


MODEL_NAME = "qwen32b"


def get_deepseek_client() -> OpenAI:
    """Get a Deepseek client."""
    # testing venice ai while deepseek is down
    VENICE_AI_BASE_URL = "https://api.venice.ai/api/v1"
    return OpenAI(api_key=os.environ["VENICE_AI_API_KEY"], base_url=VENICE_AI_BASE_URL)
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
You are a technical query refinement assistant. Transform the following user project description into up to {num_queries} concise, highly technical search queries—one per line—that will help retrieve relevant API documentation. Your queries should:
• Identify specific API endpoints, function or method names, or SDK operations implied by the description.
• Use precise, domain-specific terminology.

If no clear API-related details are present, do not generate any queries.
 
Original prompt: {user_prompt}
Refined queries:
"""
# ai! transform the function below to use the get_deepseek_client above
def _generate_queries(self, user_prompt: str, num_queries: int = 3) -> list[str]:
    """Generate expanded technical queries for documentation search."""
    print(f"Generating queries from prompt: {user_prompt}")
    response = model.predict(
        prompt=PromptTemplate(QUERY_GEN_STR),
        user_prompt=user_prompt,
        num_queries=num_queries,
    )
    print("Raw model response:", response)
    queries = [q.strip() for q in response.split("\n") if q.strip()]
    print(f"Generated queries: {queries}")
    return queries
