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

    SYSTEM_PROMPT = """Analyze if this technical request can be built given constraints.
Output must be valid JSON with 'buildable' boolean and 'reason' string.

CONSTRAINTS:
1. No new databases/tables can be created
2. No smart contract deployments possible
3. Max 4 frame buttons per screen
4. Stateless interactions between frames
5. Only existing API endpoints can be used

EXAMPLE FORMAT:
{
  "buildable": true|false,
  "reason": "Detailed technical justification"
}"""

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
                    {"role": "user", "content": f"ANALYZE THIS REQUEST:\n{user_prompt}\n\nJSON RESPONSE:"}
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=300,  # Increased to prevent truncation
                top_p=0.3  # Added for more deterministic output
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
