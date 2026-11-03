import os
import json
from xai.providers.base import BaseLLMProvider

class GeminiLLMProvider(BaseLLMProvider):
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise ValueError("Gemini API key is not configured. Placeholder key detected.")
            
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=(
                    "You are an Explainable AI layer for a UAV engine Digital Twin. "
                    "Interpret only the supplied Physics Model evidence. "
                    "Do not calculate or invent engineering values. "
                    "You must output exactly valid JSON matching the requested schema."
                )
            )
        except ImportError:
            raise RuntimeError("Gemini SDK (google-generativeai) is not installed.")

    def generate_explanation(self, prompt: str) -> dict:
        try:
            import google.generativeai as genai
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            
            content = response.text
            parsed_json = json.loads(content)
            
            required_keys = [
                "overall_condition", "summary", "why_degraded", 
                "key_evidence", "affected_regions_explanation", 
                "severity_explanation", "technical_interpretation", "limitations"
            ]
            
            for key in required_keys:
                if key not in parsed_json:
                    raise ValueError(f"Missing required key in structured response: {key}")
                    
            return parsed_json
            
        except Exception as e:
            if isinstance(e, json.JSONDecodeError):
                raise ValueError(f"Invalid JSON response from Gemini: {e}")
            elif type(e).__name__ == "ValueError" and "Missing required key in structured response" in str(e):
                raise e
            else:
                raise RuntimeError(f"Unexpected error calling Gemini: {e}")
