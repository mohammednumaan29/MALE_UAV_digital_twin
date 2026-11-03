import unittest
import json
from unittest.mock import patch, MagicMock

from xai.providers.groq_provider import GroqLLMProvider


VALID_RESPONSE = {
    "overall_condition": "Engine condition is degraded.",
    "summary": "Engine parameters deviate from expected physics-model behaviour.",
    "why_degraded": "Multiple supplied anomaly indicators are active.",
    "key_evidence": [
        "EGT residual is 25 C.",
        "CHT residual is 14 C."
    ],
    "affected_regions_explanation": "Fuel combustion and cooling regions are affected.",
    "severity_explanation": "The supplied physics model classifies the severity as MEDIUM.",
    "technical_interpretation": "Measured parameters deviate from expected values.",
    "limitations": "Explanation is limited to supplied physics-model evidence."
}


class TestGroqLLMProvider(unittest.TestCase):

    @patch.dict(
        "os.environ",
        {
            "GROQ_API_KEY": "test-groq-key",
            "GROQ_MODEL": "test-groq-model"
        },
        clear=True
    )
    @patch("xai.providers.groq_provider.Groq")
    def test_initialization(self, GroqMock):
        provider = GroqLLMProvider()

        self.assertEqual(provider.model, "test-groq-model")
        GroqMock.assert_called_once_with(api_key="test-groq-key")

    @patch.dict(
        "os.environ",
        {
            "GROQ_API_KEY": "your_groq_api_key_here"
        },
        clear=True
    )
    def test_placeholder_api_key_rejected(self):
        with self.assertRaises(ValueError):
            GroqLLMProvider()

    @patch.dict(
        "os.environ",
        {},
        clear=True
    )
    def test_missing_api_key_rejected(self):
        with self.assertRaises(ValueError):
            GroqLLMProvider()

    @patch.dict(
        "os.environ",
        {
            "GROQ_API_KEY": "test-groq-key",
            "GROQ_MODEL": "test-groq-model"
        },
        clear=True
    )
    @patch("xai.providers.groq_provider.Groq")
    def test_valid_response(self, GroqMock):

        provider = GroqLLMProvider()

        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(VALID_RESPONSE)

        provider.client.chat.completions.create.return_value = mock_response

        result = provider.generate_explanation("Test prompt")

        self.assertEqual(result, VALID_RESPONSE)

        provider.client.chat.completions.create.assert_called_once()

    @patch.dict(
        "os.environ",
        {
            "GROQ_API_KEY": "test-groq-key",
            "GROQ_MODEL": "test-groq-model"
        },
        clear=True
    )
    @patch("xai.providers.groq_provider.Groq")
    def test_invalid_json_response(self, GroqMock):

        provider = GroqLLMProvider()

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "INVALID JSON"

        provider.client.chat.completions.create.return_value = mock_response

        with self.assertRaises(ValueError):
            provider.generate_explanation("Test prompt")

    @patch.dict(
        "os.environ",
        {
            "GROQ_API_KEY": "test-groq-key",
            "GROQ_MODEL": "test-groq-model"
        },
        clear=True
    )
    @patch("xai.providers.groq_provider.Groq")
    def test_api_failure(self, GroqMock):

        provider = GroqLLMProvider()

        provider.client.chat.completions.create.side_effect = Exception(
            "Groq quota exceeded"
        )

        with self.assertRaises(RuntimeError):
            provider.generate_explanation("Test prompt")


if __name__ == "__main__":
    unittest.main()