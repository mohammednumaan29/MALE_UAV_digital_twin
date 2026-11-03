import React, { useEffect, useState } from 'react';
import GaugeDonut from '../components/GaugeDonut';
import Engine3DView from '../components/Engine3DView';
import {
  MoreVertical,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  ChevronRight,
  Gauge,
  Activity,
  Fuel,
  Zap,
  FileText,
  Heart,
  Target,
  Database,
  ClipboardList,
} from 'lucide-react';
import { ResponsiveContainer, LineChart, Line } from 'recharts';
import { COMPONENT_HEALTH } from '../mockData';

const ENGINE_ID = 'rotax914-uav-01';

const EMPTY_TELEMETRY = {
  rpm: 0,
  egt_c: 0,
  cht_c: 0,
  oil_pressure_bar: 0,
  oil_temperature_c: 0,
  fuel_flow_lph: 0,
  vibration_g: 0,
  altitude_ft: 0,
  ambient_temperature_c: 0,
  throttle: 0,
  engine_load: 0,
  power_kw: 0,
};

const buildTelemetryFrame = (telemetry = EMPTY_TELEMETRY) => ({
  rpm: Number(telemetry.rpm ?? 0),
  egt_c: Number(telemetry.egt_c ?? telemetry.egt ?? 0),
  cht_c: Number(telemetry.cht_c ?? telemetry.cht ?? 0),
  oil_pressure_bar: Number(telemetry.oil_pressure_bar ?? telemetry.oilP ?? 0),
  oil_temperature_c: Number(telemetry.oil_temperature_c ?? telemetry.oilT ?? 0),
  fuel_flow_lph: Number(telemetry.fuel_flow_lph ?? telemetry.fuel ?? 0),
  vibration_g: Number(telemetry.vibration_g ?? telemetry.vib ?? 0),
  altitude_ft: Number(telemetry.altitude_ft ?? 0),
  ambient_temperature_c: Number(telemetry.ambient_temperature_c ?? telemetry.ambientTemp ?? 0),
  throttle: Number(telemetry.throttle ?? 0),
  engine_load: Number(telemetry.engine_load ?? telemetry.load ?? 0),
  power_kw: Number(telemetry.power_kw ?? 0),
});

export default function OverviewView({ parameters, onNavigate }) {
  const [engineState, setEngineState] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [explainability, setExplainability] = useState(null);
  const [backendStatus, setBackendStatus] = useState('offline');

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        const stateResponse = await fetch(`/api/engine/${ENGINE_ID}/state`);
        const stateData = stateResponse.ok ? await stateResponse.json() : null;

        setEngineState(stateData);

        const telemetryFrame = buildTelemetryFrame(stateData?.telemetry ?? EMPTY_TELEMETRY);

        const [systemResponse, inferenceResponse, explanationResponse] = await Promise.all([
          fetch('/api/system/info'),
          fetch('/api/inference/assess', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              engine_id: ENGINE_ID,
              telemetry: telemetryFrame,
            }),
          }),
          fetch('/api/inference/explain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              engine_id: ENGINE_ID,
              telemetry: telemetryFrame,
            }),
          }),
        ]);

        const systemData = systemResponse.ok ? await systemResponse.json() : null;
        const inferenceData = inferenceResponse.ok ? await inferenceResponse.json() : null;
        const explainData = explanationResponse.ok ? await explanationResponse.json() : null;

        setBackendStatus(systemData || inferenceData || explainData ? 'online' : 'offline');
        setDashboardData(inferenceData || stateData?.latest_prediction ? {
          ...stateData?.latest_prediction,
          engine_health: stateData?.health?.health_index ?? inferenceData?.engine_health,
          probable_fault: stateData?.latest_prediction?.fault_type ?? inferenceData?.probable_fault ?? 'NORMAL',
          fault_probability: stateData?.latest_prediction?.fault_probability ?? inferenceData?.fault_probability ?? 0,
          evidence: stateData?.latest_prediction?.evidence ?? inferenceData?.evidence ?? {},
          ...inferenceData,
        } : (inferenceData || null));
        setExplainability(explainData || null);
      } catch (error) {
        setBackendStatus('offline');
        setDashboardData(null);
        setExplainability(null);
      }
    };

    let socket = null;
    try {
      socket = new WebSocket(`ws://localhost:8000/ws/telemetry/${ENGINE_ID}`);
      socket.onopen = () => setBackendStatus('online');
      socket.onmessage = (event) => {
        const payload = JSON.parse(event.data);

        setEngineState((current) => ({
          ...(current ?? {}),
          telemetry: payload.telemetry ?? current?.telemetry ?? EMPTY_TELEMETRY,
          health: {
            ...(current?.health ?? {}),
            health_index: payload.health?.health_index ?? current?.health?.health_index ?? 100,
            status: payload.health?.status ?? current?.health?.status ?? 'HEALTHY',
          },
          latest_prediction: {
            ...(current?.latest_prediction ?? {}),
            fault_type: payload.fault ?? current?.latest_prediction?.fault_type ?? 'NORMAL',
            fault_probability: payload.fault_probability ?? current?.latest_prediction?.fault_probability ?? 0,
            evidence: payload.evidence ?? current?.latest_prediction?.evidence ?? {},
          },
          latest_fault: {
            ...(current?.latest_fault ?? {}),
            fault_type: payload.fault ?? current?.latest_fault?.fault_type ?? 'NORMAL',
            status: payload.fault ? 'ACTIVE' : current?.latest_fault?.status ?? 'RESOLVED',
          },
        }));

        setDashboardData((current) => ({
          ...(current ?? {}),
          ...payload,
          fault_probability: payload.fault_probability ?? payload.confidence ?? current?.fault_probability ?? 0,
          probable_fault: payload.fault ?? payload.probable_fault ?? current?.probable_fault ?? 'NORMAL',
          engine_health: payload.health?.health_index ?? payload.engine_health ?? current?.engine_health ?? 91,
          evidence: payload.evidence ?? current?.evidence ?? {},
        }));

        const evidence = payload.evidence || {};
        const entries = Object.entries(evidence)
          .filter(([, value]) => typeof value === 'number' || typeof value === 'string')
          .slice(0, 5)
          .map(([key, value]) => `${key}: ${value}`);
        setExplainability({
          summary: `The digital twin detected ${payload.fault ?? 'NORMAL'} with ${payload.fault_probability ?? 0}% confidence. Residual and thermal evidence support the diagnosis.`,
          key_evidence: entries.length ? entries : ['fault_context: NORMAL'],
        });
      };
      socket.onerror = () => setBackendStatus('offline');
      socket.onclose = () => setBackendStatus('offline');
    } catch (error) {
      setBackendStatus('offline');
    }

    loadDashboardData();

    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, []);

  const liveTelemetry = engineState?.telemetry ?? EMPTY_TELEMETRY;
  const live = {
    rpm: liveTelemetry.rpm ?? 0,
    egt: liveTelemetry.egt_c ?? 0,
    cht: liveTelemetry.cht_c ?? 0,
    oilP: liveTelemetry.oil_pressure_bar ?? 0,
    oilT: liveTelemetry.oil_temperature_c ?? 0,
    fuel: liveTelemetry.fuel_flow_lph ?? 0,
    vib: liveTelemetry.vibration_g ?? 0,
    load: liveTelemetry.engine_load ?? 0,
  };

  const health = engineState?.health?.health_index ?? dashboardData?.engine_health ?? 91;
  const completionProbability = engineState?.latest_prediction?.fault_probability ?? dashboardData?.fault_probability ?? 87;
  const activeFaultType = engineState?.latest_prediction?.fault_type ?? dashboardData?.probable_fault ?? engineState?.latest_fault?.fault_type ?? 'NORMAL';
  const activeAlerts = [
    ...(live.cht > 160
      ? [{
          id: 'cht',
          title: 'Cylinder 3 CHT above threshold',
          time: new Date().toLocaleTimeString('en-GB', { hour12: false }),
          type: 'critical',
          msg: `${live.cht.toFixed(0)} °C (Limit: 160 °C)`,
        }]
      : []),
    ...(live.vib > 1.2
      ? [{
          id: 'vibration',
          title: 'Vibration slightly elevated',
          time: new Date().toLocaleTimeString('en-GB', { hour12: false }),
          type: 'warning',
          msg: `${live.vib.toFixed(1)} mm/s (Baseline: 1.2 mm/s)`,
        }]
      : []),
  ];
  const sparkData = (key) =>
    Array.from({ length: 6 }, (_, index) => ({
      val: Number(live[key] ?? 0) + (index - 2),
    }));

  const explanationSummary = explainability?.summary || (
    activeFaultType !== 'NORMAL'
      ? `The digital twin detected ${activeFaultType} with ${completionProbability}% confidence.`
      : 'The local digital twin is using the physics-based evidence model to explain the current engine state.'
  );
  const keyEvidence = explainability?.key_evidence ?? (
    engineState?.latest_prediction?.evidence
      ? Object.entries(engineState.latest_prediction.evidence).slice(0, 4).map(([key, value]) => `${key}: ${value}`)
      : dashboardData?.evidence
        ? Object.entries(dashboardData.evidence).slice(0, 4).map(([key, value]) => `${key}: ${value}`)
        : [
            'fault_context: NORMAL',
            'ambient_condition: moderate',
            'engine_health: 91.0',
          ]
  );

  const liveParameters = [
    { id: 'rpm', label: 'RPM', val: live.rpm, unit: 'RPM', range: '(4,800 – 5,400)', color: '#10b981', dot: 'bg-emerald-500' },
    { id: 'egt', label: 'EGT', val: live.egt, unit: '°C', range: '(600 – 720)', color: '#ef4444', dot: 'bg-red-500' },
    { id: 'cht', label: 'CHT', val: live.cht, unit: '°C', range: '(50 – 200)', color: '#f59e0b', dot: 'bg-amber-500', isAlert: live.cht > 160 },
    { id: 'oilP', label: 'Oil Pressure', val: live.oilP, unit: 'bar', range: '(3.0 – 6.0)', color: '#3b82f6', dot: 'bg-blue-500' },
    { id: 'oilT', label: 'Oil Temp', val: live.oilT, unit: '°C', range: '(70 – 110)', color: '#8b5cf6', dot: 'bg-purple-500' },
    { id: 'fuel', label: 'Fuel Flow', val: live.fuel, unit: 'L/h', range: '(2.5 – 4.0)', color: '#10b981', dot: 'bg-emerald-500' },
    { id: 'vib', label: 'Vibration', val: live.vib, unit: 'mm/s', range: '(0.0 – 3.0)', color: '#06b6d4', dot: 'bg-cyan-500' },
    { id: 'load', label: 'Engine Load', val: live.load, unit: '%', range: '(60 – 90)', color: '#10b981', dot: 'bg-emerald-500' },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="page-shell space-y-5">

      {/* ==================== PAGE HEADER ==================== */}
      <div className="dashboard-header flex-col sm:flex-row">
        <div>
          <div className="dashboard-eyebrow">Overview</div>

          <p className="m-0 text-xs font-medium text-slate-500">
            Real-time engine health, Digital Twin state and mission reliability.
          </p>
        </div>

        <div className="dashboard-status-row">
          <span className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 font-semibold shadow-2xs">
          LIVE&nbsp; | &nbsp;Digital Twin: SYNCHRONIZED
          &nbsp;|&nbsp;
          Data Quality 98.7%
          &nbsp;|&nbsp;
          Flight Phase <span className="text-slate-900">CRUISE</span>
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-2 rounded-xl border border-amber-200 bg-amber-50/70 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-2">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wide text-amber-800">Warning · Cooling performance deviation detected</div>
            <div className="mt-0.5 text-[11px] text-amber-700">CHT +7 °C above Digital Twin expectation · Probability {dashboardData?.fault_probability ?? 82}% · Confidence {dashboardData?.fault_probability ?? 89}%</div>
          </div>
        </div>
        <div className="flex items-center gap-3 text-[11px] font-bold text-blue-700">
          <span className="rounded-full border border-blue-200 bg-blue-50 px-2 py-1 text-[10px] uppercase tracking-wide text-blue-700">
            {backendStatus === 'online' ? 'BACKEND LIVE' : 'DEMO MODE'}
          </span>
          <button type="button" onClick={() => onNavigate('diagnostics')}>VIEW DIAGNOSTICS</button>
          <button type="button" onClick={() => onNavigate('telemetry')}>VIEW TELEMETRY</button>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="mb-3 flex items-center justify-between gap-2">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Explainable AI</p>
            <h3 className="mt-1 text-lg font-bold text-slate-900">{dashboardData?.probable_fault ?? 'NORMAL'}</h3>
          </div>
          <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide text-emerald-700">
            {dashboardData?.fault_probability ?? 82}% confidence
          </span>
        </div>
        <p className="text-sm text-slate-600">{explanationSummary}</p>
        <ul className="mt-3 space-y-2 text-xs text-slate-600">
          {keyEvidence.map((item) => (
            <li key={item} className="flex items-start gap-2 rounded-lg bg-slate-50 px-2 py-1.5">
              <span className="mt-1 h-1.5 w-1.5 rounded-full bg-cyan-500" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* ==================== TOP KPI CARDS ==================== */}
      <div className="ui-kpi-grid grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

        {/* ENGINE HEALTH */}
        <div className="ui-card ui-kpi-card overview-instrument-card health-card">

          <div className="overview-instrument-header flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="p-1 rounded bg-rose-50 text-rose-500">
                <Heart className="w-3.5 h-3.5" />
              </span>

              <span className="overview-instrument-title font-bold text-xs text-slate-800">
                Engine Health
              </span>
            </div>

            <button className="text-slate-400 hover:text-slate-600">
              <MoreVertical className="w-4 h-4" />
            </button>
          </div>

          <div className="overview-instrument-body flex items-center justify-between">

            <GaugeDonut
              value={health}
              color="#10b981"
              variant="instrument"
            />

            <div className="overview-instrument-meta flex flex-col items-end text-right space-y-1">

              <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                <TrendingUp className="w-3 h-3" />
                +2%
              </span>

              <span className="text-[10px] text-slate-400 font-medium">
                vs last hour
              </span>

              <span className="px-2 py-0.5 text-[10px] font-bold text-emerald-700 bg-emerald-100 rounded-md">
                Good
              </span>
            </div>
          </div>

          <p className="overview-instrument-footer text-[11px] text-slate-500">
            All systems within normal range.
          </p>
        </div>


        {/* MISSION COMPLETION CONFIDENCE */}
        <div className="ui-card ui-kpi-card overview-instrument-card confidence-card">

          <div className="overview-instrument-header flex items-center justify-between">

            <div className="flex items-center space-x-2">

              <span className="p-1 rounded bg-blue-50 text-blue-500">
                <Target className="w-3.5 h-3.5" />
              </span>

              <span className="overview-instrument-title font-bold text-xs text-slate-800">
                Mission Completion Confidence
              </span>
            </div>

            <button className="text-slate-400 hover:text-slate-600">
              <MoreVertical className="w-4 h-4" />
            </button>
          </div>

          <div className="overview-instrument-body flex items-center justify-between">

            <GaugeDonut
              value={completionProbability}
              color="#3b82f6"
              variant="instrument"
            />

            <div className="overview-instrument-meta flex flex-col items-end text-right space-y-1">

              <span className="text-[10px] text-slate-500">
                Estimated time to complete
              </span>

              <span className="text-xs font-bold text-slate-900 font-mono">
                2 h 18 min
              </span>

              <span className="px-2 py-0.5 text-[10px] font-bold text-amber-700 bg-amber-100 rounded-md">
                Moderate
              </span>

              <span className="text-[10px] text-slate-500">
                Primary Risk:{' '}
                <strong className="text-slate-800">
                  Elevated CHT
                </strong>
              </span>
            </div>
          </div>
        </div>


        {/* MISSION RISK */}
        <div className="ui-card ui-kpi-card">

          <div className="overview-instrument-header flex items-center justify-between">

            <div className="flex items-center space-x-2">

              <AlertTriangle className="w-4 h-4 text-amber-500" />

              <span className="font-bold text-xs text-slate-800">
                Mission Risk
              </span>
            </div>

            <button className="text-slate-400 hover:text-slate-600">
              <MoreVertical className="w-4 h-4" />
            </button>
          </div>

          <div className="my-2 space-y-2">

            <div className="flex items-center space-x-2 bg-amber-50 border border-amber-200 px-3 py-1 rounded-lg">

              <AlertTriangle className="w-4 h-4 text-amber-600" />

              <span className="text-sm font-bold text-amber-700">
                Moderate
              </span>
            </div>

            <div className="space-y-1 text-[11px] text-slate-600 pl-1 font-medium">

              <div className="flex items-center space-x-2">
                <span className="text-red-500 font-bold">
                  ↑
                </span>
                <span>
                  Cylinder Head Temperature
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <span className="text-amber-500 font-bold">
                  ↑
                </span>
                <span>
                  Engine Load
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <span className="text-amber-500 font-bold">
                  ↑
                </span>
                <span>
                  High Ambient Temperature
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={() => onNavigate('diagnostics')}
            className="text-[11px] font-bold text-blue-600 hover:text-blue-800 flex items-center gap-1 transition"
          >
            View Risk Analysis →
          </button>
        </div>


        {/* DIGITAL TWIN CONFIDENCE */}
        <div className="ui-card ui-kpi-card overview-instrument-card twin-card">

          <div className="overview-instrument-header flex items-center justify-between">

            <div className="flex items-center space-x-2">

              <span className="p-1 rounded bg-teal-50 text-teal-600">
                <Database className="w-3.5 h-3.5" />
              </span>

              <span className="overview-instrument-title font-bold text-xs text-slate-800">
                Digital Twin Confidence
              </span>
            </div>

            <button className="text-slate-400 hover:text-slate-600">
              <MoreVertical className="w-4 h-4" />
            </button>
          </div>

          <div className="overview-instrument-body flex items-center justify-between">

            <GaugeDonut
              value={93}
              color="#0d9488"
              variant="instrument"
            />

            <div className="overview-instrument-meta flex flex-col space-y-1 text-[10px] text-slate-600">

              <span className="px-2 py-0.5 font-bold text-emerald-700 bg-emerald-100 rounded-md self-start">
                High Fidelity
              </span>

              <div className="flex items-center gap-1 text-[10px] text-slate-600 font-medium">
                <CheckCircle className="w-3 h-3 text-emerald-500" />
                Physics Agreement
              </div>

              <div className="flex items-center gap-1 text-[10px] text-slate-600 font-medium">
                <CheckCircle className="w-3 h-3 text-emerald-500" />
                Sensor Consistency
              </div>

              <div className="flex items-center gap-1 text-[10px] text-slate-600 font-medium">
                <CheckCircle className="w-3 h-3 text-emerald-500" />
                Telemetry Quality
              </div>

              <div className="flex items-center gap-1 text-[10px] text-slate-600 font-medium">
                <CheckCircle className="w-3 h-3 text-emerald-500" />
                Model Confidence
              </div>
            </div>
          </div>
        </div>
      </div>


      {/* ==================== MIDDLE ROW ====================
          UAV & Mission Status REMOVED ONLY.
          2D Engine Inspection = 8 columns
          Component Health = 4 columns
      */}
      <div className="overview-middle-grid grid grid-cols-1 lg:grid-cols-12 gap-4">

        {/* 2D ENGINE INSPECTION VIEW */}
        <div className="lg:col-span-8">
          <Engine3DView />
        </div>


        {/* COMPONENT HEALTH */}
        <div className="ui-card lg:col-span-4 flex flex-col justify-start">

          <div className="flex items-center justify-between mb-2">

            <div className="flex items-center space-x-2">

              <span className="p-1 rounded bg-blue-50 text-blue-600">
                <Gauge className="w-3.5 h-3.5" />
              </span>

              <h3 className="font-bold text-xs text-slate-800">
                Component Health
              </h3>
            </div>

            <button
              onClick={() => onNavigate('telemetry')}
              className="text-[11px] font-bold text-blue-600 hover:underline"
            >
              View All &gt;
            </button>
          </div>


          <div className="space-y-2.5">

            {COMPONENT_HEALTH.map((comp) => (

              <div
                key={comp.name}
                className="ui-health-row text-[11px]"
              >

                <span className="text-slate-700 font-medium truncate">
                  {comp.name}
                </span>

                <div className="flex items-center gap-2">

                  <div className="ui-health-bar">

                    <div
                      className={`h-full rounded-full ${
                        comp.status === 'warning'
                          ? 'bg-amber-500'
                          : 'bg-emerald-500'
                      }`}
                      style={{
                        width: `${comp.pct}%`,
                      }}
                    />
                  </div>

                  <span className="font-mono font-bold text-slate-800 text-[10px] text-right">
                    {comp.pct}%
                  </span>
                </div>

                <ChevronRight className="w-3.5 h-3.5 text-slate-400 ml-2 shrink-0" />
              </div>
            ))}
          </div>
        </div>
      </div>


      {/* ==================== BOTTOM ROW ==================== */}
      <div className="overview-bottom-grid grid grid-cols-1 lg:grid-cols-12 gap-4">

        {/* LIVE ENGINE PARAMETERS */}
        <div className="ui-card lg:col-span-5 flex flex-col justify-between">

          <div className="flex items-center justify-between mb-3">

            <div className="flex items-center space-x-2">

              <Activity className="w-4 h-4 text-blue-600" />

              <h3 className="font-bold text-xs text-slate-800">
                Live Engine Parameters
              </h3>
            </div>

            <button
              onClick={() => onNavigate('telemetry')}
              className="text-[11px] font-bold text-blue-600 hover:underline"
            >
              View All →
            </button>
          </div>


          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">

            {liveParameters.map((p) => (

              <div
                key={p.id}
                className={`p-2.5 rounded-lg border flex h-34 min-w-0 flex-col justify-between ${
                  p.isAlert
                    ? 'border-amber-300 bg-amber-50/40'
                    : 'border-slate-100 bg-slate-50/60'
                }`}
              >

                <div className="flex items-center justify-between text-[10px]">

                  <span className="font-semibold text-slate-600 truncate">
                    {p.label}
                  </span>

                  <span
                    className={`w-2 h-2 rounded-full ${p.dot}`}
                  />
                </div>


                <div className="my-1">

                  <span className="text-base font-black text-slate-900 font-mono tracking-tight">
                    {p.val}
                  </span>

                  <span className="text-[10px] font-medium text-slate-500 ml-1">
                    {p.unit}
                  </span>
                </div>


                <span className="text-[9px] text-slate-400">
                  {p.range}
                </span>


                <div className="aero-chart h-10 w-full mt-1">

                  <ResponsiveContainer
                    width="100%"
                    height="100%"
                  >
                    <LineChart
                      data={sparkData(p.id)}
                    >
                      <Line
                        type="monotone"
                        dataKey="val"
                        stroke={p.color}
                        strokeWidth={1.5}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ))}
          </div>
        </div>


        {/* ACTIVE ALERTS */}
        <div className="overview-alerts ui-card lg:col-span-4 flex flex-col">

          <div className="flex items-center justify-between mb-3">

            <div className="flex items-center space-x-2">

              <AlertTriangle className="w-4 h-4 text-red-500" />

              <h3 className="font-bold text-xs text-slate-800">
                Active Alerts ({activeAlerts.length})
              </h3>
            </div>

            <button
              onClick={() => onNavigate('diagnostics')}
              className="text-[11px] font-bold text-blue-600 hover:underline"
            >
              View All →
            </button>
          </div>


          <div className="space-y-3">

            {/* HIGH ALERT */}
            <div className="overview-alert-row p-3 bg-red-50/70 border border-red-200 rounded-lg flex items-start justify-between">

              <div className="flex items-start space-x-2.5">

                <AlertTriangle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />

                <div>

                  <div className="text-[11px] font-bold text-slate-900">
                    Cylinder 3 CHT above threshold
                  </div>

                  <div className="text-[10px] text-red-600 font-semibold mt-0.5">
                    185 °C{' '}
                    <span className="text-slate-500 font-normal">
                      (Limit: 160 °C)
                    </span>
                  </div>
                </div>
              </div>


              <div className="flex flex-col items-end">

                <span className="px-1.5 py-0.5 bg-red-600 text-white text-[9px] font-bold rounded">
                  HIGH
                </span>

                <span className="text-[9px] text-slate-400 font-mono mt-1">
                  10:22:18
                </span>
              </div>
            </div>


            {/* MEDIUM ALERT */}
            <div className="overview-alert-row p-3 bg-amber-50/70 border border-amber-200 rounded-lg flex items-start justify-between">

              <div className="flex items-start space-x-2.5">

                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />

                <div>

                  <div className="text-[11px] font-bold text-slate-900">
                    Vibration slightly elevated
                  </div>

                  <div className="text-[10px] text-amber-700 font-semibold mt-0.5">
                    1.8 mm/s{' '}
                    <span className="text-slate-500 font-normal">
                      (Baseline: 1.2 mm/s)
                    </span>
                  </div>
                </div>
              </div>


              <div className="flex flex-col items-end">

                <span className="px-1.5 py-0.5 bg-amber-500 text-white text-[9px] font-bold rounded">
                  MEDIUM
                </span>

                <span className="text-[9px] text-slate-400 font-mono mt-1">
                  10:18:44
                </span>
              </div>
            </div>


            {/* NOMINAL */}
            <div className="flex items-center space-x-2 p-2 bg-emerald-50 rounded-lg border border-emerald-100 text-[11px] text-emerald-800 font-medium">

              <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />

              <span>
                All other parameters nominal
              </span>
            </div>
          </div>
        </div>


        {/* RECENT MISSION INSIGHTS */}
        <div className="ui-card lg:col-span-3 flex flex-col justify-start">

          <div className="flex items-center justify-between mb-3">

            <div className="flex items-center space-x-2">

              <FileText className="w-4 h-4 text-blue-600" />

              <h3 className="font-bold text-xs text-slate-800">
                Recent Mission Insights
              </h3>
            </div>

            <button
              onClick={() => onNavigate('reports')}
              className="text-[11px] font-bold text-blue-600 hover:underline"
            >
              View All →
            </button>
          </div>


          <div className="space-y-3">

            {/* INSIGHT 1 */}
            <div className="flex items-start space-x-2 text-[11px]">

              <span className="p-1 rounded bg-blue-50 text-blue-600 shrink-0 mt-0.5">
                <ClipboardList className="w-3.5 h-3.5" />
              </span>

              <div className="flex-1">

                <p className="text-slate-800 font-medium">
                  Engine operating within safe limits for current mission profile.
                </p>

                <span className="text-[9px] text-slate-400 font-mono">
                  2 min ago
                </span>
              </div>
            </div>


            {/* INSIGHT 2 */}
            <div className="flex items-start space-x-2 text-[11px]">

              <span className="p-1 rounded bg-amber-50 text-amber-600 shrink-0 mt-0.5">
                <Zap className="w-3.5 h-3.5" />
              </span>

              <div className="flex-1">

                <p className="text-slate-800 font-medium">
                  Slight increase in CHT detected during high load.
                </p>

                <span className="text-[9px] text-slate-400 font-mono">
                  18 min ago
                </span>
              </div>
            </div>


            {/* INSIGHT 3 */}
            <div className="flex items-start space-x-2 text-[11px]">

              <span className="p-1 rounded bg-emerald-50 text-emerald-600 shrink-0 mt-0.5">
                <Fuel className="w-3.5 h-3.5" />
              </span>

              <div className="flex-1">

                <p className="text-slate-800 font-medium">
                  Fuel efficiency nominal.
                </p>

                <span className="text-[9px] text-slate-400 font-mono">
                  36 min ago
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      </div>
    </div>
  );
}