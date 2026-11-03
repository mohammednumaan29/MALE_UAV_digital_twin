import json
import os

def load_engine_output(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in {file_path}: {e}")
        
    required_fields = [
        "engine_id",
        "timestamp",
        "operating_conditions",
        "actual_parameters",
        "physics_model_expected",
        "residuals",
        "physics_health_assessment",
        "physics_anomaly_indicators",
        "probable_affected_regions",
        "physics_model_summary"
    ]
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
            
    return data
