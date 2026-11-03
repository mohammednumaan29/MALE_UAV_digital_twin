import os
import json
from groq import Groq, GroqError
from xai.providers.base import BaseLLMProvider

class GroqLLMProvider(BaseLLMProvider):
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            raise ValueError("GROQ_API_KEY environment variable is missing or invalid.")
            
        self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
        self.client = Groq(api_key=api_key)
        
    def generate_explanation(self, prompt: str) -> dict:
        schema = {
            "type": "object",
            "properties": {
                "overall_condition": {"type": "string"},
                "summary": {"type": "string"},
                "why_degraded": {"type": "string"},
                "key_evidence": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "affected_regions_explanation": {"type": "string"},
                "severity_explanation": {"type": "string"},
                "technical_interpretation": {"type": "string"},
                "limitations": {"type": "string"}
            },
            "required": [
                "overall_condition", 
                "summary", 
                "why_degraded", 
                "key_evidence", 
                "affected_regions_explanation", 
                "severity_explanation", 
                "technical_interpretation", 
                "limitations"
            ],
            "additionalProperties": False
        }
        
        system_message = "You are an Explainable AI layer for a UAV engine Digital Twin. Interpret only the supplied Physics Model evidence. Do not calculate or invent engineering values."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "explanation_schema",
                        "schema": schema,
                        "strict": True
                    }
                }
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except GroqError as e:
            raise RuntimeError(f"Groq API Error: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from Groq: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error calling Groq: {e}")
