import os
import sys
import json
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

load_dotenv(os.path.join(current_dir, ".env"))

from xai.loader import load_engine_output
from xai.evidence import extract_xai_evidence
from xai.prompt import build_xai_prompt
from xai.provider_manager import XAIProviderManager

def main():
    json_path = os.path.join(current_dir, "data", "sample_engine_output.json")
    
    try:
        print("=== XAI PROVIDER MANAGER TEST ===\n")
        
        print("Loading engine output...")
        data = load_engine_output(json_path)
        
        print("Extracting evidence...")
        evidence = extract_xai_evidence(data)
        
        print("Building prompt...")
        prompt = build_xai_prompt(evidence)
        
        print("\nProvider order:")
        print("1. Groq")
        print("2. Cerebras")
        print("3. Gemini\n")
        
        print("Initializing XAIProviderManager...")
        manager = XAIProviderManager()
        
        print("Requesting explanation (Fallback chain activated)...")
        result = manager.generate_explanation(prompt)
        
        print("\nFinal result:")
        print(json.dumps(result, indent=2))
            
    except Exception as e:
        print(f"\nGeneral Error: {e}")

if __name__ == "__main__":
    main()
