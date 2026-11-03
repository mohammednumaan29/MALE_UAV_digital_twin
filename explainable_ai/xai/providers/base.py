from abc import ABC, abstractmethod

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_explanation(self, prompt: str) -> str:
        """
        Accepts a prompt string and returns the LLM response.
        Must be implemented by all concrete providers.
        """
        pass
