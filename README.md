# AI-Enabled Physics-Informed Digital Twin for MALE UAV Aero-Piston Engine

> **RESEARCH & ENGINEERING PROTOTYPE NOTICE**  
> This software is an experimental digital twin prototype representing a Rotax 914-inspired turbocharged aero-piston engine for MALE UAV propulsion systems.  
> It **MUST NOT** claim aircraft certification, guaranteed Remaining Useful Life (RUL), exact component diagnosis, or flight safety certification.

---

## Architecture Overview

```text
Real-time/simulated telemetry
        ↓
Physics-based Digital Twin
        ↓
Expected engine behaviour
        ↓
Actual vs Expected residuals
        ↓
Health assessment
        ↓
AI anomaly detection
        ↓
Fault classification
        ↓
Degradation tracking
        ↓
RUL estimation
        ↓
Mission simulation
        ↓
Mission reliability assessment
        ↓
Maintenance decision support
        ↓
REST API + WebSocket
        ↓
Frontend
```

---

## Phase 0: Project Foundation

This phase establishes the backend skeleton:
- FastAPI web service
- Pydantic Settings & Environment variable configuration
- Structured logging
- Verification endpoints:
  - `GET /api/health`
  - `GET /api/system/info`
  - `GET /docs` (Swagger UI)
  - `GET /openapi.json`
- Automated test suite (pytest)

### Running the Backend

From the workspace root or `backend` folder:

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

---

## Phase 4: Fault Simulation

The project includes a decoupled fault injection layer separate from the normal engine telemetry simulator. The shared state is persisted in `backend/data/fault_state.json` and consumed by the live simulator without replacing the physics model or simulator logic.

### Run the simulator and fault controller

Terminal 1:

```bash
cd rotax
python simulator.py
```

Terminal 2:

```bash
cd rotax
python fault_simulator.py --fault OVERHEATING --severity 50
```

To clear the fault:

```bash
cd rotax
python fault_simulator.py --clear
```

The simulator reads the current fault state each loop and ramps the effective severity gradually to avoid instantaneous jumps.

---

## Phase 5: Data Pipeline and PostgreSQL Persistence

The project keeps the existing database infrastructure and extends it toward the required Phase 5 schema. The database layer supports PostgreSQL while retaining SQLite compatibility for local development and tests.

### Database objects

Required table families are present in the SQLAlchemy metadata, including:
- `engines`
- `telemetry`
- `health_records`
- `faults`
- `predictions`
- `physics_predictions`
- `missions`
- `mission_results`
- `maintenance_records`

The schema compatibility logic in `backend/app/models/database.py` adds missing columns to an existing database instead of dropping an active database.

### PostgreSQL configuration

Set environment variables before connecting to PostgreSQL:

```bash
set POSTGRES_HOST=localhost
set POSTGRES_PORT=5432
set POSTGRES_DB=rotax914_db
set POSTGRES_USER=rotax_user
set POSTGRES_PASSWORD=rotax_pass
```

If `DATABASE_URL` is already present, it takes precedence.

### Local verification commands

```bash
cd backend
python -m pytest tests/test_database.py -q
```

This verifies that the Phase 5 tables exist and that telemetry can be inserted and queried through the project service layer.

### Useful database checks

```bash
cd backend
python -c "from app.models.database import init_db; init_db(); print('db ready')"
python -c "from app.models.database import SessionLocal; from app.models.engine import EngineModel; db=SessionLocal(); print(db.query(EngineModel).count()); db.close()"
```

The existing project remains compatible with the SQLite fallback when PostgreSQL is not configured, which is useful for local test runs and rapid iteration.

---

## Phase 6: ML Training Pipeline

The project now includes a dedicated training pipeline that generates synthetic telemetry and fault examples from the physics model, then trains separate models for:

- anomaly detection using Isolation Forest,
- fault classification using Random Forest,
- RUL estimation using Random Forest regression.

These training scripts are intentionally separated from real-time inference and are not retrained every time the backend starts.

### Training scripts

From the project root:

```bash
python ml/training/train_anomaly.py
python ml/training/train_fault.py
python ml/training/train_rul.py
```

Artifacts are saved under `ml/models/`:

- `anomaly_model.pkl`
- `fault_model.pkl`
- `rul_model.pkl`

### Expected printout

Each script prints:

- dataset size,
- feature count,
- training/test sizes,
- evaluation metrics,
- save path.

### Local verification

```bash
cd backend
pytest tests/test_ml_pipeline.py -q
```

This checks the synthetic dataset and validates that all three training scripts create model artifacts successfully.

---

## Phase 7: Real-Time ML Inference

The project includes a persistent live inference service that loads the trained artifacts once at backend startup, then evaluates telemetry frames without retraining on each loop.

### Runtime behavior

- `live_inference_service` loads `anomaly_model.pkl`, `fault_model.pkl`, and `rul_model.pkl` once
- telemetry is converted to the same physics-informed feature ordering used during training
- anomaly detection, fault classification, health scoring, and RUL estimation run in the same inference pass
- the result includes evidence, affected regions, severity, and confidence bounds

### Local verification commands

```bash
cd backend
python -c "import sys; sys.path.insert(0, '.'); from app.services.live_inference_service import live_inference_service; telemetry = {'rpm': 5200, 'egt_c': 740, 'cht_c': 122, 'oil_pressure_bar': 3.3, 'oil_temperature_c': 96, 'fuel_flow_lph': 17.8, 'vibration_g': 0.22, 'altitude_ft': 1500, 'ambient_temperature_c': 22, 'throttle': 68, 'engine_load': 0.74, 'power_kw': 59}; print(live_inference_service.evaluate_telemetry(telemetry))"
```

This returns a structured live assessment such as health score, status, anomaly flag, probable fault, severity, RUL, confidence range, and affected subsystem region.

---

## Phase 8: Health Engine

The project now includes a dedicated health engine that aggregates the contributions from:

- residuals (thermal, lubrication, vibration, power/efficiency drift)
- anomaly score
- fault probability
- fault severity
- operating conditions and sensor deviations

The service is implemented in `backend/app/services/health_service.py` and is used by the live inference pipeline in `backend/app/services/live_inference_service.py`.

### Weighting model

The score is intentionally explainable rather than arbitrary. A 100-point baseline is reduced by:

- anomaly score contribution (0-25 points)
- fault probability contribution (0-30 points)
- severity contribution (0-20 points)
- thermal residual contribution (0-12 points)
- vibration contribution (0-8 points)
- lubrication contribution (0-5 points)

These weights are configurable through `HEALTHY_THRESHOLD`, `NORMAL_THRESHOLD`, `DEGRADED_THRESHOLD`, and `HEALTH_SCORE_WEIGHTS` in `backend/app/config/settings.py`.

### Status thresholds

- 90.0 to 100.0: HEALTHY
- 70.0 to 89.99: NORMAL
- 40.0 to 69.99: DEGRADED
- 0.0 to 39.99: CRITICAL

### Local verification

```bash
cd backend
python -c "from app.services.health_service import HealthEngine; print(HealthEngine().compute(anomaly_score=0.2, fault_probability=15.0, severity=0.1, residuals={'egt_residual': 6.0, 'cht_residual': 4.0, 'oil_temperature_residual': 3.0, 'oil_pressure_residual': 0.2, 'vibration_residual': 0.02}, vibration_g=0.15, oil_pressure_bar=3.6))"
```

This produces a health index and status in the configured ranges.

---

## Phase 9: FastAPI Routes and Engine API Surface

The backend now exposes the required engine, fault-control, mission, and health endpoints while preserving the existing telemetry API.

### Core routes

- `POST /api/telemetry`
- `GET /api/telemetry/{engine_id}`
- `GET /api/telemetry/latest`
- `GET /api/telemetry/history`
- `GET /api/health/{engine_id}`
- `GET /api/faults/{engine_id}`
- `GET /api/predictions/{engine_id}`
- `GET /api/rul/{engine_id}`
- `POST /api/fault/activate`
- `POST /api/fault/deactivate`
- `GET /api/fault/status`
- `POST /api/mission/simulate`
- `GET /api/mission/{mission_id}`
- `GET /api/replay/{mission_id}`
- `GET /api/engine/{engine_id}/state`

### Local verification commands

```bash
cd backend
pytest tests/test_phase9_api.py -q
```

```bash
cd backend
python -c "from fastapi.testclient import TestClient; from app.main import app; client=TestClient(app); print(client.get('/api/fault/status').json()); print(client.get('/api/telemetry/rotax914-uav-01?limit=1').json())"
```

This validates the fault controller, engine history route, and state snapshot API contract.

---

## Phase 10: WebSocket Real-Time Telemetry

The backend exposes a persistent websocket stream for engine telemetry and ML/health outputs.

### Route

- `WS /ws/telemetry/{engine_id}`

The stream emits a JSON payload every second with:

- timestamp
- telemetry
- physics expected values
- residuals
- health
- anomaly status and score
- active fault name
- fault probability and severity
- RUL range
- affected region

### Local verification commands

```bash
cd backend
pytest tests/test_phase10_websocket.py -q
```

```bash
cd backend
python -c "from fastapi.testclient import TestClient; from app.main import app; client=TestClient(app); with client.websocket_connect('/ws/telemetry/rotax914-uav-01') as ws: print(ws.receive_json())"
```

This validates that the websocket stays open and pushes a structured live telemetry payload without reconnecting every cycle.

---

## Phase 11: Mission Simulation and Risk Assessment

The mission layer now uses the existing `MissionProfile` flight-condition logic and a deterministic degradation model to simulate mission trajectories over altitude, temperature, throttle, and duration. It produces a mission summary that includes:

- predicted degradation
- health start/end values
- mission risk (LOW / MEDIUM / HIGH / CRITICAL)
- estimated RUL
- explainable recommendations
- timeline and RUL trend values for replay/visualization

### Run a standalone mission simulation

```bash
cd rotax
python mission_simulator.py --duration-hours 8 --altitude-ft 12000 --ambient-temperature-c 38 --throttle 65 --mission-type SURVEILLANCE
```

### API usage

```bash
cd backend
python -c "from fastapi.testclient import TestClient; from app.main import app; client=TestClient(app); payload={'engine_id':'rotax914-uav-01','duration_hours':8,'altitude_ft':12000,'ambient_temperature_c':38,'throttle':65,'mission_type':'SURVEILLANCE'}; print(client.post('/api/mission/simulate', json=payload).json())"
```

This keeps the mission simulation separate from the live engine simulator while still using the existing physics model and mission metadata flow already present in the project.

---

## Phase 12: Mission Replay and Timeline Playback

Mission replay is stored alongside each mission result so the application can restore the original trajectory, health trend, and RUL trend without re-simulating the whole mission on demand.

### What is stored

The mission result record now persists:

- `telemetry_snapshot`
- `health_trend_snapshot`
- `rul_trend_snapshot`
- `fault_events_snapshot`

These values are restored by `/api/replay/{mission_id}` and are suitable for timeline playback in the UI or dashboard.

### Local verification

```bash
cd backend
pytest tests/test_phase9_api.py -q
```

This confirms that a mission can be simulated, persisted, and replayed through the API while preserving the mission timeline for frontend playback.

---

## Phase 13: Maintenance Advisory

The project now generates explainable maintenance advisories from the active engine fault and the recent health trend. The recommendation is intentionally advisory only and does not authorize autonomous maintenance action.

### Advisory logic

The recommendation is generated using:

- the latest fault type
- the current fault severity
- the recent health trend
- the fault-specific maintenance guidance map

Examples:

- `OVERHEATING` → inspect cooling and cylinder thermal conditions
- `LUBRICATION_DEGRADATION` → inspect lubrication system and oil-pressure trend
- `ABNORMAL_VIBRATION` → inspect mounts, bearings, and rotating assembly
- `SENSOR_ANOMALY` → verify calibration and compare redundant sensor sources

### Local verification

```bash
cd backend
pytest tests/test_phase13_maintenance.py -q
```

And the runtime API endpoint:

```bash
cd backend
python -c "from fastapi.testclient import TestClient; from app.main import app; client=TestClient(app); client.post('/api/fault/activate', json={'engine_id':'rotax914-uav-01','fault_type':'OVERHEATING','severity':0.5}); print(client.get('/api/maintenance/rotax914-uav-01').json())"
```

This produces a structured advisory payload with fault, trend, severity, and decision-support recommendation text.

---

## Phase 14: Explainable AI Evidence

The live inference and websocket outputs now package model evidence in a transparent, inspectable form. Every fault prediction includes:

- a residual-based `evidence` object
- contextual operating-state indicators such as `ambient_condition`, `ambient_temperature_c`, and `altitude_ft`
- a standardized `affected_region` list
- probability and severity fields that can be displayed directly in the UI or API clients

This is intentionally explainable research output rather than exact component diagnosis.

### Local verification

```bash
cd backend
python -c "from app.services.live_inference_service import live_inference_service; telemetry={'rpm':5800,'egt_c':710,'cht_c':150,'oil_pressure_bar':4.0,'oil_temperature_c':96,'fuel_flow_lph':18.2,'vibration_g':0.31,'altitude_ft':10000,'ambient_temperature_c':30,'throttle':65,'engine_load':0.72,'power_kw':52}; result=live_inference_service.evaluate_telemetry(telemetry); print(result['probable_fault']); print(result['fault_probability']); print(result['evidence']); print(result['affected_region'])"
```

This confirms that the live ML path keeps residual evidence and mapped subsystem regions available for API and dashboard consumption.

---

## Phase 15: 3D Engine Integration Support

The backend now exposes a standardized affected-region vocabulary for the frontend or 3D model integration layer. These names are intentionally kept as subsystem identifiers rather than exact component diagnoses.

### Canonical region identifiers

- `FUEL_MIXTURE_REGION`
- `COMBUSTION_REGION`
- `CYLINDER_REGION`
- `COOLING_REGION`
- `LUBRICATION_REGION`
- `CRANKSHAFT_REGION`
- `BEARING_REGION`
- `GEARBOX_REGION`
- `ENGINE_MOUNT_REGION`

Example mappings:

- `OVERHEATING` -> `CYLINDER_REGION`, `COOLING_REGION`
- `LUBRICATION_DEGRADATION` -> `LUBRICATION_REGION`, `BEARING_REGION`, `CRANKSHAFT_REGION`
- `ABNORMAL_VIBRATION` -> `CRANKSHAFT_REGION`, `BEARING_REGION`, `GEARBOX_REGION`, `ENGINE_MOUNT_REGION`

### Local verification

```bash
cd backend
pytest tests/test_phase15_3d_regions.py -q
```

This validates that the backend emits region names in the canonical, frontend-friendly form needed for 3D engine visualisation and explainable health overlays.

---

## Phase 16: Docker Configuration

The project includes a Compose-based local deployment stack for the backend, PostgreSQL, and a lightweight frontend placeholder service. It is configured through environment variables and avoids hard-coded credentials.

### Local startup

```bash
cd rotax
docker compose up --build
```

### Services

- `frontend` on `http://localhost:3000`
- `backend` on `http://localhost:8000`
- `postgres` on `localhost:5432`

The stack uses the environment variables in the repository root `.env` and is designed to keep the system runnable locally while remaining compatible with later deployment operations.

---

## Phase 17: Automated Testing

The project includes automated validation for the major acceptance criteria across the digital twin pipeline. These tests cover:

- physics realism and continuity
- fault injection and severity progression
- data persistence and schema compatibility
- ML training artifact generation and feature ordering
- API routes for telemetry, health, prediction, faults, and missions
- WebSocket streaming behavior
- domain-specific health and region behavior

### Run the full suite

```bash
cd backend
python -m pytest tests -q
```

### Targeted validation commands

```bash
cd backend
pytest tests/test_physics.py -q
pytest tests/test_fault_injection.py -q
pytest tests/test_database.py -q
pytest tests/test_ml_pipeline.py -q
pytest tests/test_phase9_api.py -q
pytest tests/test_phase10_websocket.py -q
pytest tests/test_phase13_maintenance.py -q
pytest tests/test_phase15_3d_regions.py -q
```

This ensures the simulator, fault system, persistence layer, ML training, API surface, and websocket telemetry remain aligned with the project’s acceptance requirements.
