import pytest
from unittest.mock import Mock, MagicMock
from backend.services.prompt_buildability_checker import PromptBuildabilityChecker

class TestPromptBuildabilityChecker:
    @pytest.fixture
    def mock_client(self):
        client = Mock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        client.chat.completions.create.return_value = mock_completion
        return client

    def test_valid_buildable_response(self, mock_client):
        valid_response = '{"buildable": true, "reason": "Feasible"}'
        mock_client.chat.completions.create.return_value.choices[0].message.content = valid_response
        checker = PromptBuildabilityChecker(mock_client)

        result, reason = checker.check_prompt("Add a counter button")

        assert result is True
        assert "Feasible" in reason

    def test_valid_unbuildable_response(self, mock_client):
        response = '{"buildable": false, "reason": "Needs DB"}'
        mock_client.chat.completions.create.return_value.choices[0].message.content = response
        checker = PromptBuildabilityChecker(mock_client)

        result, reason = checker.check_prompt("Save user profiles")

        assert result is False
        assert "DB" in reason

    def test_invalid_json_response(self, mock_client):
        mock_client.chat.completions.create.return_value.choices[0].message.content = "invalid json"
        checker = PromptBuildabilityChecker(mock_client)

        result, reason = checker.check_prompt("Bad request")

        assert result is False
        assert "invalid" in reason

    def test_api_error_handling(self):
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API down")
        checker = PromptBuildabilityChecker(mock_client)

        result, reason = checker.check_prompt("Any prompt")

        assert result is False
        assert "API down" in reason
