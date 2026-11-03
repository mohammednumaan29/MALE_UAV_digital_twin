from xai.response_validator import validate_xai_response, XAIResponseValidationError
from xai.providers.groq_provider import GroqLLMProvider
from xai.providers.cerebras_provider import CerebrasLLMProvider
from xai.providers.gemini_provider import GeminiLLMProvider

class XAIProviderManager:
    def __init__(self):
        self.providers = []
        self.init_errors = []
        
        # 1. Initialize Groq (Primary)
        try:
            self.providers.append({
                "name": "groq",
                "instance": GroqLLMProvider()
            })
        except Exception as e:
            self.init_errors.append({
                "provider": "groq",
                "error": str(e)
            })
            
        # 2. Initialize Cerebras (First Fallback)
        try:
            self.providers.append({
                "name": "cerebras",
                "instance": CerebrasLLMProvider()
            })
        except Exception as e:
            self.init_errors.append({
                "provider": "cerebras",
                "error": str(e)
            })
            
        # 3. Initialize Gemini (Second Fallback)
        try:
            self.providers.append({
                "name": "gemini",
                "instance": GeminiLLMProvider()
            })
        except Exception as e:
            self.init_errors.append({
                "provider": "gemini",
                "error": str(e)
            })
            
    def generate_explanation(self, prompt: str) -> dict:
        """
        Attempts to generate an explanation by sequentially trying 
        available providers in strict fallback order.
        """
        provider_errors = list(self.init_errors)
        
        for provider_info in self.providers:
            provider_name = provider_info["name"]
            provider_instance = provider_info["instance"]
            
            # Safely extract the configured model name across different provider implementations
            model_name = getattr(provider_instance, "model_name", getattr(provider_instance, "model", "unknown"))
            
            try:
                # Attempt generation
                response = provider_instance.generate_explanation(prompt)
                # Validate the XAI response schema
                try:
                    validate_xai_response(response)
                except XAIResponseValidationError as ve:
                    raise ValueError(f"XAI response validation failed for provider '{provider_name}': {ve}")
                
                # Success - return immediately
                return {
                    "success": True,
                    "provider": provider_name,
                    "model": model_name,
                    "response": response,
                    "error": None,
                    "provider_errors": provider_errors
                }
                
            except Exception as e:
                # Record generation error and allow fallback to continue
                provider_errors.append({
                    "provider": provider_name,
                    "error": str(e)
                })
                
        # If all available providers failed (or none were available)
        return {
            "success": False,
            "provider": None,
            "model": None,
            "response": None,
            "error": "All XAI providers are unavailable.",
            "provider_errors": provider_errors
        }
