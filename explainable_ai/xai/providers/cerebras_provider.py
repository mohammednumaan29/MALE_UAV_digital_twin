import os
import json
from xai.providers.base import BaseLLMProvider

class CerebrasLLMProvider(BaseLLMProvider):
    def __init__(self):
        self.api_key = os.getenv("CEREBRAS_API_KEY")
        if not self.api_key or self.api_key == "your_cerebras_api_key_here":
            raise ValueError("Cerebras API key is not configured. Placeholder key detected.")
            
        self.model = os.getenv("CEREBRAS_MODEL", "llama3.1-8b")
        
        try:
            from cerebras.cloud.sdk import Cerebras
            self.client = Cerebras(api_key=self.api_key)
        except ImportError:
            raise RuntimeError("Cerebras SDK is not installed.")
            
    def generate_explanation(self, prompt: str) -> dict:
        system_message = (
            "You are an Explainable AI layer for a UAV engine Digital Twin. "
            "Interpret only the supplied Physics Model evidence. "
            "Do not calculate or invent engineering values. "
            "You must output exactly valid JSON matching the requested schema."
        )
        
        try:
            from cerebras.cloud.sdk import APIError
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            
            # Additional validation to ensure not malformed
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
            if type(e).__name__ == 'APIError':
                raise RuntimeError(f"Cerebras API Error: {e}")
            elif isinstance(e, json.JSONDecodeError):
                raise ValueError(f"Invalid JSON response from Cerebras: {e}")
            else:
                raise RuntimeError(f"Unexpected error calling Cerebras: {e}")
