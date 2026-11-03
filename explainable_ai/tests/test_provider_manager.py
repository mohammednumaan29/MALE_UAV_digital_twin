import unittest
from unittest.mock import patch

from xai.provider_manager import XAIProviderManager


VALID_RESPONSE = {
    "overall_condition": "Engine condition is degraded.",
    "summary": "Engine parameters deviate from expected physics-model behaviour.",
    "why_degraded": "Multiple supplied anomaly indicators are active.",
    "key_evidence": [
        "EGT residual is 25 C.",
        "CHT residual is 14 C.",
        "Fuel flow residual is 0.7 LPH.",
        "Vibration residual is 0.10 g."
    ],
    "affected_regions_explanation": (
        "The supplied physics assessment identifies the fuel combustion system, "
        "cylinder region, and cooling system."
    ),
    "severity_explanation": (
        "The supplied physics model classifies the severity as MEDIUM."
    ),
    "technical_interpretation": (
        "The measured parameters show deviation from the supplied expected values."
    ),
    "limitations": (
        "This explanation is limited to the evidence supplied by the physics model."
    )
}


INVALID_RESPONSE = {
    "overall_condition": "Engine condition is degraded."
}


class TestXAIProviderManagerFallback(unittest.TestCase):

    def test_groq_success(self):
        with patch("xai.provider_manager.GroqLLMProvider") as GroqMock, \
             patch("xai.provider_manager.CerebrasLLMProvider") as CerebrasMock, \
             patch("xai.provider_manager.GeminiLLMProvider") as GeminiMock:

            groq = GroqMock.return_value
            groq.model_name = "test-groq-model"
            groq.generate_explanation.return_value = VALID_RESPONSE

            result = XAIProviderManager().generate_explanation("Test prompt")

            self.assertTrue(result["success"])
            self.assertEqual(result["provider"], "groq")
            self.assertEqual(result["model"], "test-groq-model")
            self.assertEqual(result["response"], VALID_RESPONSE)

            groq.generate_explanation.assert_called_once()
            CerebrasMock.return_value.generate_explanation.assert_not_called()
            GeminiMock.return_value.generate_explanation.assert_not_called()

    def test_groq_failure_cerebras_success(self):
        with patch("xai.provider_manager.GroqLLMProvider") as GroqMock, \
             patch("xai.provider_manager.CerebrasLLMProvider") as CerebrasMock, \
             patch("xai.provider_manager.GeminiLLMProvider") as GeminiMock:

            groq = GroqMock.return_value
            groq.model_name = "test-groq-model"
            groq.generate_explanation.side_effect = RuntimeError(
                "Groq failed"
            )

            cerebras = CerebrasMock.return_value
            cerebras.model_name = "test-cerebras-model"
            cerebras.generate_explanation.return_value = VALID_RESPONSE

            result = XAIProviderManager().generate_explanation("Test prompt")

            self.assertTrue(result["success"])
            self.assertEqual(result["provider"], "cerebras")
            self.assertEqual(result["model"], "test-cerebras-model")
            self.assertEqual(result["response"], VALID_RESPONSE)

            groq.generate_explanation.assert_called_once()
            cerebras.generate_explanation.assert_called_once()
            GeminiMock.return_value.generate_explanation.assert_not_called()
    
    
    def test_groq_failure_cerebras_failure_gemini_success(self):
      with patch("xai.provider_manager.GroqLLMProvider") as GroqMock, \
         patch("xai.provider_manager.CerebrasLLMProvider") as CerebrasMock, \
         patch("xai.provider_manager.GeminiLLMProvider") as GeminiMock:

        GroqMock.return_value.model_name = "test-groq-model"
        CerebrasMock.return_value.model_name = "test-cerebras-model"
        GeminiMock.return_value.model_name = "test-gemini-model"

        GroqMock.return_value.generate_explanation.side_effect = RuntimeError(
            "Groq failed"
        )

        CerebrasMock.return_value.generate_explanation.side_effect = RuntimeError(
            "Cerebras failed"
        )

        GeminiMock.return_value.generate_explanation.return_value = VALID_RESPONSE

        result = XAIProviderManager().generate_explanation("Test prompt")

        self.assertTrue(result["success"])
        self.assertEqual(result["provider"], "gemini")
        self.assertEqual(result["model"], "test-gemini-model")
        self.assertEqual(result["response"], VALID_RESPONSE)

        GroqMock.return_value.generate_explanation.assert_called_once()
        CerebrasMock.return_value.generate_explanation.assert_called_once()
        GeminiMock.return_value.generate_explanation.assert_called_once()

        self.assertEqual(len(result["provider_errors"]), 2)

    def test_all_providers_fail(self):
        with patch("xai.provider_manager.GroqLLMProvider") as GroqMock, \
             patch("xai.provider_manager.CerebrasLLMProvider") as CerebrasMock, \
             patch("xai.provider_manager.GeminiLLMProvider") as GeminiMock:

            GroqMock.return_value.model_name = "test-groq-model"
            CerebrasMock.return_value.model_name = "test-cerebras-model"
            GeminiMock.return_value.model_name = "test-gemini-model"

            GroqMock.return_value.generate_explanation.side_effect = RuntimeError(
                "Groq failed"
            )

            CerebrasMock.return_value.generate_explanation.side_effect = RuntimeError(
                "Cerebras failed"
            )

            GeminiMock.return_value.generate_explanation.side_effect = RuntimeError(
                "Gemini failed"
            )

            result = XAIProviderManager().generate_explanation("Test prompt")

            self.assertFalse(result["success"])
            self.assertIsNone(result["provider"])
            self.assertIsNone(result["model"])
            self.assertIsNone(result["response"])

            self.assertEqual(
                result["error"],
                "All XAI providers are unavailable."
            )

            self.assertEqual(len(result["provider_errors"]), 3)

            GroqMock.return_value.generate_explanation.assert_called_once()
            CerebrasMock.return_value.generate_explanation.assert_called_once()
            GeminiMock.return_value.generate_explanation.assert_called_once()

    def test_invalid_response_triggers_fallback(self):
        with patch("xai.provider_manager.GroqLLMProvider") as GroqMock, \
             patch("xai.provider_manager.CerebrasLLMProvider") as CerebrasMock, \
             patch("xai.provider_manager.GeminiLLMProvider") as GeminiMock:

            groq = GroqMock.return_value
            groq.model_name = "test-groq-model"
            groq.generate_explanation.return_value = INVALID_RESPONSE

            cerebras = CerebrasMock.return_value
            cerebras.model_name = "test-cerebras-model"
            cerebras.generate_explanation.return_value = VALID_RESPONSE

            result = XAIProviderManager().generate_explanation("Test prompt")

            self.assertTrue(result["success"])
            self.assertEqual(result["provider"], "cerebras")
            self.assertEqual(result["model"], "test-cerebras-model")
            self.assertEqual(result["response"], VALID_RESPONSE)

            groq.generate_explanation.assert_called_once()
            cerebras.generate_explanation.assert_called_once()
            GeminiMock.return_value.generate_explanation.assert_not_called()

            self.assertTrue(
                any(
                    error["provider"] == "groq"
                    for error in result["provider_errors"]
                )
            )


if __name__ == "__main__":
    unittest.main()