import os
from typing import Tuple, Optional
from openai import OpenAI
from backend.utils.timing import measure_time
import re


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
def send_prompt_to_reasoning_model(prompt: str, system_prompt: Optional[str] = None) -> Tuple[str, str]:
    # client = get_together_ai_client()
    client = get_deepseek_client()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model="deepseek-reasoner",
        temperature=0.2,
        messages=messages,
    )
    content = response.choices[0].message.content.strip()
    print(f'reasoning model response: {content}')
    if "<think>" not in content or "</think>" not in content:
        return content, ""

    try:
        parts = content.split("</think>", 1)  # Only split on first occurrence
        if len(parts) < 2:
            return content, ""

        think_section = parts[0].split("<think>")[-1].strip()
        response_text = parts[1].strip()

        # Fallback if response is empty but think exists
        if not response_text:
            return content.replace("<think>", "").replace("</think>", "").strip(), think_section

        print(f'reasoning response: think length {len(think_section)}, response length {len(response_text)}')
        return response_text, think_section

    except Exception as e:
        print(f"Error parsing reasoning model response: {str(e)}")
        return content, ""


def generate_project_name(prompt: str) -> str:
    """Generate a project name from the user's prompt using LLM."""
    deepseek = get_deepseek_client()

    try:
        response = deepseek.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that generates short, memorable project names for a crypto miniapp. Only respond with one project name. 2-3 words max for this one name. no 'or' or &*/ chars. If the user suggests a title or project name, return it without modification.",
                },
                {
                    "role": "user",
                    "content": f"Generate one short, memorable project name based on this description: {prompt}",
                },
            ],
            max_tokens=25,
            temperature=1.5,
        )
        llm_content = response.choices[0].message.content.strip()
        print(f'generate_project_name: response "{llm_content}"')
        project_name = llm_content.split("\n")[0].replace('"', "").strip()
        print(f'generate_project_name: project_name "{project_name}"')
        return project_name[:50]  # hard cut length
    except Exception as e:
        print(f"Warning: Could not generate project name: {e}")
        return "new-frame-project"


QUERY_GEN_STR = """\
You are a technical query refinement assistant.
You are analyzing a request to build a Farcaster Frames v2 application.
You generate technical search queries — one per line — that will help retrieve relevant documentation.
If no technical details are present, do not generate any queries.
Don't give an explanation if you generate no queries, just return an empty list.

IMPORTANT: Frames v2 offers a full HTML/CSS/JS canvas.

Your queries should:
• Use precise, domain-specific terminology.
• Don't hallucinate or generate false information.
• be clear and concise for humans, no API calls or code snippets.

First, identify which technical components this request requires:
1. External API integrations
2. Farcaster-specific features (notifications, native actions)
3. Blockchain interactions with smart contracts

Second, generate queries for each of them. Return a list of queries, one per line.
"""


@measure_time
def generate_search_queries_from_user_input(
    user_input: str
) -> list[str]:
    """Generate expanded technical queries for documentation search."""
    print(f"Generating queries from user input: {user_input}")

    try:
        prompt = f"""Original user input: {user_input}
        Generate technical search queries — one per line — that will help retrieve relevant documentation.
        Up to 3 queries should be generated.
        If you generate no queries because no technical details are provided, just return an empty list.
        Refined search queries:
        """
        llm_content, _ = send_prompt_to_reasoning_model(prompt, system_prompt=QUERY_GEN_STR)
        # client = get_deepseek_client()

        # response = client.chat.completions.create(
        #     model="deepseek-ai/DeepSeek-R1",
        #     messages=[
        #         {"role": "system", "content": QUERY_GEN_STR},
        #         {
        #             "role": "user",
        #             "content": f"Original user input: {user_input} Generate technical search queries — one per line — that will help retrieve relevant documentation. Refined search queries:",
        #         },
        #     ],
        #     temperature=0.0,
        # )

        # llm_content = response.choices[0].message.content.strip()
        print("Model response for search queries prompt:", llm_content)

        llm_content = llm_content.replace("`", "").strip()
        llm_content = llm_content.replace("Refined search queries:", "").replace('[]', '').strip()
        queries = [q.lstrip("-").strip() for q in llm_content.split("\n") if q]
        queries = [q for q in queries if q]
        queries = [re.sub(r'^\d+\.\s+', '', q) for q in queries]
        print(f"Generated queries: {queries}")
        return queries

    except Exception as e:
        print(f"Failed to generate search queries from user input. Error: {e}")
        return []
