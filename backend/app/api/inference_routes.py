"""Live ML inference endpoints for the digital twin."""

import json
import sys
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status

from app.schemas.inference import LiveInferenceRequest, LiveInferenceResponse
from app.services.live_inference_service import live_inference_service

router = APIRouter(prefix="/inference", tags=["Inference"])

EXPLAINABLE_AI_ROOT = Path(__file__).resolve().parents[3] / "explainable_ai"
if str(EXPLAINABLE_AI_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPLAINABLE_AI_ROOT))

try:
    from xai.evidence import extract_xai_evidence
    from xai.prompt import build_xai_prompt
    from xai.provider_manager import XAIProviderManager
except Exception:  # pragma: no cover - optional dependency layer
    extract_xai_evidence = None
    build_xai_prompt = None
    XAIProviderManager = None


def _build_local_explanation(inference_result: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a deterministic explanation summary if XAI providers are unavailable."""
    evidence = inference_result.get("evidence", {}) or {}
    fault = inference_result.get("probable_fault", "NORMAL")
    confidence = float(inference_result.get("fault_probability", 0.0))
    key_evidence = []
    for key, value in sorted(
        evidence.items(),
        key=lambda item: abs(float(item[1])) if isinstance(item[1], (int, float)) else 0.0,
        reverse=True,
    )[:5]:
        if key in {"fault_context", "ambient_condition", "affected_region", "confidence_pct"}:
            continue
        if isinstance(value, (int, float)):
            key_evidence.append(f"{key}: {value}")
    if not key_evidence:
        key_evidence.append(f"fault_context: {fault}")
    summary = (
        f"The digital twin detected a {fault.lower()} pattern with {confidence:.1f}% confidence. "
        f"The evidence prioritizes thermal and residual deviations while accounting for ambient conditions."
    )
    return {
        "success": False,
        "provider": "local-fallback",
        "summary": summary,
        "key_evidence": key_evidence,
        "affected_regions": inference_result.get("affected_region", []),
        "confidence_pct": round(confidence, 2),
    }


@router.post(
    "/assess",
    response_model=LiveInferenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Assess live telemetry with the trained ML pipeline",
    description="Run anomaly detection, fault classification, health scoring, and RUL estimation on a current telemetry frame.",
)
async def assess_live_telemetry(request: LiveInferenceRequest) -> LiveInferenceResponse:
    """Evaluate one telemetry frame using the cached ML artifacts."""
    try:
        result = live_inference_service.evaluate_telemetry(request.telemetry)
        if request.expected is not None:
            merged = dict(request.telemetry)
            merged.update(request.expected)
            result = live_inference_service.evaluate_telemetry(merged)
        return LiveInferenceResponse(**result)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive error handling
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Inference failed: {exc}") from exc


@router.post(
    "/explain",
    status_code=status.HTTP_200_OK,
    summary="Generate an explainable AI summary using the digital twin evidence",
    description="Convert the engine evidence and residuals into a human-readable explanation backed by the physics model and XAI providers when available.",
)
async def explain_live_telemetry(request: LiveInferenceRequest) -> Dict[str, Any]:
    """Package the live inference results into explainable evidence for the frontend dashboard."""
    try:
        result = live_inference_service.evaluate_telemetry(request.telemetry)
        if request.expected is not None:
            merged = dict(request.telemetry)
            merged.update(request.expected)
            result = live_inference_service.evaluate_telemetry(merged)

        payload = {
            "engine_id": request.engine_id,
            "timestamp": "live",
            "operating_conditions": {
                "altitude_ft": float(request.telemetry.get("altitude_ft", 0.0)),
                "ambient_temperature_c": float(request.telemetry.get("ambient_temperature_c", 15.0)),
                "throttle": float(request.telemetry.get("throttle", 50.0)),
                "engine_load": float(request.telemetry.get("engine_load", 0.0)),
            },
            "actual_parameters": {
                "egt_c": float(request.telemetry.get("egt_c", 0.0)),
                "cht_c": float(request.telemetry.get("cht_c", 0.0)),
                "oil_pressure_bar": float(request.telemetry.get("oil_pressure_bar", 0.0)),
                "oil_temperature_c": float(request.telemetry.get("oil_temperature_c", 0.0)),
                "fuel_flow_lph": float(request.telemetry.get("fuel_flow_lph", 0.0)),
                "vibration_g": float(request.telemetry.get("vibration_g", 0.0)),
            },
            "physics_model_expected": {
                "egt_c": float(live_inference_service._expected_state_for(request.telemetry)["expected_egt_c"]),
                "cht_c": float(live_inference_service._expected_state_for(request.telemetry)["expected_cht_c"]),
                "oil_pressure_bar": float(live_inference_service._expected_state_for(request.telemetry)["expected_oil_pressure_bar"]),
                "oil_temperature_c": float(live_inference_service._expected_state_for(request.telemetry)["expected_oil_temperature_c"]),
                "fuel_flow_lph": float(live_inference_service._expected_state_for(request.telemetry)["expected_fuel_flow_lph"]),
                "vibration_g": float(live_inference_service._expected_state_for(request.telemetry)["expected_vibration_g"]),
            },
            "residuals": {
                "egt_c": float(request.telemetry.get("egt_c", 0.0)) - float(live_inference_service._expected_state_for(request.telemetry)["expected_egt_c"]),
                "cht_c": float(request.telemetry.get("cht_c", 0.0)) - float(live_inference_service._expected_state_for(request.telemetry)["expected_cht_c"]),
                "oil_pressure_bar": float(request.telemetry.get("oil_pressure_bar", 0.0)) - float(live_inference_service._expected_state_for(request.telemetry)["expected_oil_pressure_bar"]),
                "oil_temperature_c": float(request.telemetry.get("oil_temperature_c", 0.0)) - float(live_inference_service._expected_state_for(request.telemetry)["expected_oil_temperature_c"]),
                "fuel_flow_lph": float(request.telemetry.get("fuel_flow_lph", 0.0)) - float(live_inference_service._expected_state_for(request.telemetry)["expected_fuel_flow_lph"]),
                "vibration_g": float(request.telemetry.get("vibration_g", 0.0)) - float(live_inference_service._expected_state_for(request.telemetry)["expected_vibration_g"]),
            },
            "physics_health_assessment": {
                "health_index": float(result.get("engine_health", 100.0)),
                "health_status": result.get("status", "HEALTHY"),
                "degradation_trend": "stable",
            },
            "physics_anomaly_indicators": {
                "anomaly_detected": bool(result.get("anomaly", False)),
                "anomaly_score": float(result.get("anomaly_score", 0.0)),
            },
            "probable_affected_regions": result.get("affected_region", []),
            "physics_model_summary": {
                "overall_condition": result.get("status", "HEALTHY"),
                "primary_concern": result.get("probable_fault", "NORMAL"),
                "severity": float(result.get("severity", 0.0)),
            },
        }

        if extract_xai_evidence is not None and build_xai_prompt is not None and XAIProviderManager is not None:
            prompt = build_xai_prompt(extract_xai_evidence(payload))
            manager = XAIProviderManager()
            xai_result = manager.generate_explanation(prompt)
            if xai_result.get("success") and xai_result.get("response"):
                response_payload = {
                    "engine_id": request.engine_id,
                    "provider": xai_result.get("provider"),
                    "summary": xai_result["response"].get("summary", "Explainable AI summary available."),
                    "key_evidence": xai_result["response"].get("key_evidence", []),
                    "affected_regions": xai_result["response"].get("affected_regions", result.get("affected_region", [])),
                    "confidence_pct": float(result.get("fault_probability", 0.0)),
                    "fault": result.get("probable_fault", "NORMAL"),
                    "status": "ok",
                }
                return response_payload

        return {
            "engine_id": request.engine_id,
            "provider": "local-fallback",
            "summary": (
                f"The digital twin detected {result.get('probable_fault', 'NORMAL').lower()} with "
                f"{float(result.get('fault_probability', 0.0)):.1f}% confidence. "
                "Residual and thermal evidence support the diagnosis within the bounds of the physics-informed model."
            ),
            "key_evidence": [
                f"fault_context: {result.get('probable_fault', 'NORMAL')}",
                f"anomaly_score: {float(result.get('anomaly_score', 0.0)):.3f}",
                f"engine_health: {float(result.get('engine_health', 100.0)):.1f}",
            ],
            "affected_regions": result.get("affected_region", []),
            "confidence_pct": float(result.get("fault_probability", 0.0)),
            "fault": result.get("probable_fault", "NORMAL"),
            "status": "ok",
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive error handling
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Explainability generation failed: {exc}") from exc
