def extract_xai_evidence(engine_data):
    # 1. engine_context
    engine_context = {
        "engine_id": engine_data.get("engine_id"),
        "timestamp": engine_data.get("timestamp"),
        "operating_conditions": engine_data.get("operating_conditions", {})
    }
    
    # 2. health_assessment
    health_raw = engine_data.get("physics_health_assessment", {})
    health_assessment = {
        "health_index": health_raw.get("health_index"),
        "status": health_raw.get("health_status", health_raw.get("status")), # handle both in case of variance
        "degradation_trend": health_raw.get("degradation_trend")
    }
    
    # 3. parameter_evidence
    parameter_evidence = {}
    params = [
        "egt_c", 
        "cht_c", 
        "oil_pressure_bar", 
        "oil_temperature_c", 
        "fuel_flow_lph", 
        "vibration_g"
    ]
    
    actuals = engine_data.get("actual_parameters", {})
    expecteds = engine_data.get("physics_model_expected", {})
    residuals = engine_data.get("residuals", {})
    
    for p in params:
        parameter_evidence[p] = {
            "actual": actuals.get(p),
            "expected": expecteds.get(p),
            "residual": residuals.get(p)
        }
        
    # 4. anomaly_indicators
    anomaly_indicators = engine_data.get("physics_anomaly_indicators", {})
    
    # 5. affected_regions
    affected_regions = engine_data.get("probable_affected_regions", [])
    
    # 6. model_summary
    summary_raw = engine_data.get("physics_model_summary", {})
    model_summary = {
        "overall_condition": summary_raw.get("overall_condition"),
        "primary_concern": summary_raw.get("primary_concern"),
        "severity": summary_raw.get("severity")
    }
    
    evidence = {
        "engine_context": engine_context,
        "health_assessment": health_assessment,
        "parameter_evidence": parameter_evidence,
        "anomaly_indicators": anomaly_indicators,
        "affected_regions": affected_regions,
        "model_summary": model_summary
    }
    
    return evidence
