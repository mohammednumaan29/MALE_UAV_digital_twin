import unittest
import json
from unittest.mock import patch, MagicMock

from xai.providers.cerebras_provider import CerebrasLLMProvider


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


class TestCerebrasLLMProvider(unittest.TestCase):

    @patch.dict(
        "os.environ",
        {
            "CEREBRAS_API_KEY": "test-cerebras-key",
            "CEREBRAS_MODEL": "test-cerebras-model"
        },
        clear=True
    )
    @patch("cerebras.cloud.sdk.Cerebras")
    def test_initialization(self, CerebrasMock):
        provider = CerebrasLLMProvider()

        self.assertEqual(provider.model, "test-cerebras-model")
        CerebrasMock.assert_called_once_with(
            api_key="test-cerebras-key"
        )

    @patch.dict(
        "os.environ",
        {
            "CEREBRAS_API_KEY": "your_cerebras_api_key_here"
        },
        clear=True
    )
    def test_placeholder_api_key_rejected(self):
        with self.assertRaises(ValueError):
            CerebrasLLMProvider()

    @patch.dict(
        "os.environ",
        {},
        clear=True
    )
    def test_missing_api_key_rejected(self):
        with self.assertRaises(ValueError):
            CerebrasLLMProvider()

    @patch.dict(
        "os.environ",
        {
            "CEREBRAS_API_KEY": "test-cerebras-key",
            "CEREBRAS_MODEL": "test-cerebras-model"
        },
        clear=True
    )
    @patch("cerebras.cloud.sdk.Cerebras")
    def test_valid_response(self, CerebrasMock):

        provider = CerebrasLLMProvider()

        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(
            VALID_RESPONSE
        )

        provider.client.chat.completions.create.return_value = mock_response

        result = provider.generate_explanation("Test prompt")

        self.assertEqual(result, VALID_RESPONSE)

        provider.client.chat.completions.create.assert_called_once()

    @patch.dict(
        "os.environ",
        {
            "CEREBRAS_API_KEY": "test-cerebras-key",
            "CEREBRAS_MODEL": "test-cerebras-model"
        },
        clear=True
    )
    @patch("cerebras.cloud.sdk.Cerebras")
    def test_invalid_json_response(self, CerebrasMock):

        provider = CerebrasLLMProvider()

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "INVALID JSON"

        provider.client.chat.completions.create.return_value = mock_response

        with self.assertRaises(ValueError):
            provider.generate_explanation("Test prompt")

    @patch.dict(
        "os.environ",
        {
            "CEREBRAS_API_KEY": "test-cerebras-key",
            "CEREBRAS_MODEL": "test-cerebras-model"
        },
        clear=True
    )
    @patch("cerebras.cloud.sdk.Cerebras")
    def test_api_failure(self, CerebrasMock):

        provider = CerebrasLLMProvider()

        provider.client.chat.completions.create.side_effect = Exception(
            "Cerebras quota exceeded"
        )

        with self.assertRaises(RuntimeError):
            provider.generate_explanation("Test prompt")


if __name__ == "__main__":
    unittest.main()