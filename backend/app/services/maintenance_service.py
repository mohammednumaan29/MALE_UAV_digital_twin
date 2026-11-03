"""Maintenance advisory generation for engine health assessment."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.fault import FaultRecordModel
from app.models.health import HealthRecordModel
from app.models.maintenance import MaintenanceRecordModel


class MaintenanceAdvisoryService:
    """Build decision-support recommendations from fault and health trend data."""

    FAULT_RECOMMENDATIONS = {
        "NORMAL": "Continue routine line checks and scheduled inspection cadence.",
        "FUEL_MIXTURE_DEGRADATION": "Inspect the fuel/mixture delivery system, verify mixture quality, and check for restricted flow or abnormal combustion indications.",
        "OVERHEATING": "Inspect the cooling and cylinder thermal system, review hot-running trends, and check for airflow, cooling, and combustion imbalance.",
        "LUBRICATION_DEGRADATION": "Inspect the lubrication system and review oil-pressure and oil-temperature trends before the next mission.",
        "ABNORMAL_VIBRATION": "Inspect the engine mounts, bearings, and rotating assembly for imbalance, looseness, or abnormal vibration signatures.",
        "SENSOR_ANOMALY": "Verify sensor calibration, cross-check redundant measurements, and inspect for drift, spikes, or stuck readings.",
    }

    def _severity_label(self, severity_value: float) -> str:
        if severity_value >= 0.8:
            return "Extreme"
        if severity_value >= 0.5:
            return "High"
        if severity_value >= 0.3:
            return "Medium"
        if severity_value > 0.0:
            return "Low"
        return "Minimal"

    def _trend_label(self, latest_health: Optional[HealthRecordModel], previous_health: Optional[HealthRecordModel]) -> str:
        if latest_health is None:
            return "Stable"
        if previous_health is None:
            return "Monitoring"
        if latest_health.health_index < previous_health.health_index:
            return "Increasing"
        if latest_health.health_index > previous_health.health_index:
            return "Improving"
        return "Stable"

    def generate_advisory(self, engine_id: str, db: Session) -> Dict[str, Any]:
        latest_fault = (
            db.query(FaultRecordModel)
            .filter(FaultRecordModel.engine_id == engine_id)
            .order_by(FaultRecordModel.timestamp.desc(), FaultRecordModel.id.desc())
            .first()
        )
        fault_name = (latest_fault.fault_type if latest_fault else "NORMAL").upper()
        fault_severity = float(latest_fault.severity if latest_fault else 0.0)
        severity_label = self._severity_label(fault_severity)

        health_records = (
            db.query(HealthRecordModel)
            .filter(HealthRecordModel.engine_id == engine_id)
            .order_by(HealthRecordModel.timestamp.desc(), HealthRecordModel.id.desc())
            .limit(2)
            .all()
        )
        latest_health = health_records[0] if health_records else None
        previous_health = health_records[1] if len(health_records) > 1 else None
        trend_label = self._trend_label(latest_health, previous_health)
        recommendation = self.FAULT_RECOMMENDATIONS.get(fault_name, self.FAULT_RECOMMENDATIONS["NORMAL"])

        advisory = {
            "engine_id": engine_id,
            "fault": fault_name,
            "trend": trend_label,
            "severity": severity_label,
            "severity_value": round(fault_severity, 3),
            "recommendation": recommendation,
            "description": (
                f"FAULT: {fault_name}\n"
                f"TREND: {trend_label}\n"
                f"SEVERITY: {severity_label}\n"
                f"RECOMMENDATION: {recommendation}"
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "maintenance_type": "ADVISORY",
            "related_fault": fault_name if fault_name != "NORMAL" else None,
        }

        record = MaintenanceRecordModel(
            engine_id=engine_id,
            timestamp=datetime.now(timezone.utc),
            maintenance_type="ADVISORY",
            description=advisory["description"],
            related_fault=advisory["related_fault"],
            notes=f"trend={trend_label}; severity={severity_label}; severity_value={fault_severity}",
            severity_level=severity_label,
        )
        db.add(record)
        db.commit()
        return advisory


maintenance_advisory_service = MaintenanceAdvisoryService()
