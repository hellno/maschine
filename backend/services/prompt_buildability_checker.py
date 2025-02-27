from typing import Tuple
from backend.integrations.llm import get_deepseek_client
from openai import OpenAI
from typing import Optional
import json

class PromptBuildabilityChecker:
    """
    Validates if a user prompt can be implemented within system constraints
    without database modifications or smart contract deployments.
    """

    SYSTEM_PROMPT = """Analyze if this technical request can be built given:
- No new databases/tables can be created
- No smart contract deployments possible

Return JSON with 'buildable' boolean and 'reason' string."""

    def __init__(self, client: Optional[OpenAI] = None):
        self.llm_client = client or get_deepseek_client()

    def check_prompt(self, user_prompt: str) -> Tuple[bool, str]:
        """
        Determine if a user prompt is buildable within constraints

        Args:
            user_prompt: User's natural language feature request

        Returns:
            Tuple (is_buildable: bool, reason: str)
        """
        try:
            response = self.llm_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )

            result = self._parse_response(response.choices[0].message.content)
            return result

        except Exception as e:
            # Fail closed on API errors
            return False, f"Validation failed: {str(e)}"

    def _parse_response(self, raw_response: str) -> Tuple[bool, str]:
        """Parse LLM response into validation result"""
        try:
            response = json.loads(raw_response)
            return (
                bool(response.get('buildable', False)),
                str(response.get('reason', 'No reason provided'))
            )
        except (json.JSONDecodeError, KeyError):
            return False, "invalid validation response format"
