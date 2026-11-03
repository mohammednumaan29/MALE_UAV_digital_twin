from xai.providers.base import BaseLLMProvider

class MockLLMProvider(BaseLLMProvider):
    def generate_explanation(self, prompt: str) -> str:
        return "Mock provider received the XAI prompt successfully."
