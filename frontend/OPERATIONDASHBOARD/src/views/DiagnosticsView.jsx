import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  RefreshCw,
  TriangleAlert,
} from 'lucide-react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { COMPONENT_HEALTH } from '../mockData';

const DEFAULT_DIAGNOSTICS = {
  health: null,
  faultCodes: [],
  tests: [],
  sensors: [],
  maintenance: [],
  systemStatus: null,
};

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

const statusPalette = {
  normal: 'bg-emerald-500/15 text-emerald-700 border border-emerald-500/25',
  warning: 'bg-amber-500/15 text-amber-700 border border-amber-500/25',
  critical: 'bg-red-500/15 text-red-700 border border-red-500/25',
  unknown: 'bg-slate-500/10 text-slate-700 border border-slate-200',
  valid: 'bg-emerald-500/15 text-emerald-700 border border-emerald-500/25',
  drift: 'bg-amber-500/15 text-amber-700 border border-amber-500/25',
  spike: 'bg-amber-500/15 text-amber-700 border border-amber-500/25',
  stuck: 'bg-orange-500/15 text-orange-700 border border-orange-500/25',
  dropout: 'bg-red-500/15 text-red-700 border border-red-500/25',
  noisy: 'bg-amber-500/15 text-amber-700 border border-amber-500/25',
  invalid: 'bg-red-500/15 text-red-700 border border-red-500/25',
  degraded: 'bg-amber-500/15 text-amber-700 border border-amber-500/25',
  stable: 'bg-emerald-500/15 text-emerald-700 border border-emerald-500/25',
  watch: 'bg-blue-500/15 text-blue-700 border border-blue-500/25',
  analysis: 'bg-slate-700/10 text-slate-700 border border-slate-300',
};

const faultHypotheses = [
  {
    id: 'cooling',
    name: 'Cooling Degradation',
    probability: 82,
    severity: 'warning',
    component: 'Cooling System',
    status: 'ACTIVE',
    summary: 'CHT is increasing faster than the expected Digital Twin trajectory while engine load remains elevated. EGT shows a correlated increase. Oil pressure remains within the expected range.',
    evidence: [
      { parameter: 'CHT', actual: 172, expected: 165, residual: 7, contribution: 'High', status: 'warning' },
      { parameter: 'EGT', actual: 648, expected: 640, residual: 8, contribution: 'Medium', status: 'warning' },
      { parameter: 'Vibration', actual: 1.8, expected: 1.3, residual: 0.5, contribution: 'Low', status: 'watch' },
      { parameter: 'Oil Pressure', actual: 4.2, expected: 4.3, residual: -0.1, contribution: 'Low', status: 'normal' },
    ],
    metrics: {
      engineHealth: 94,
      anomalyScore: 0.82,
      diagnosticConfidence: 89,
      rul: 143,
      missionRisk: 'MODERATE',
      componentHealth: 94,
    },
  },
  {
    id: 'ambient',
    name: 'High Ambient Temperature',
    probability: 41,
    severity: 'watch',
    component: 'Environmental Load',
    status: 'PENDING',
    summary: 'External temperature and density conditions are driving higher thermal load. The engine remains stable but the thermal margin is narrowing.',
    evidence: [
      { parameter: 'Ambient Temp', actual: -5, expected: -8, residual: 3, contribution: 'Medium', status: 'watch' },
      { parameter: 'EGT', actual: 648, expected: 642, residual: 6, contribution: 'Medium', status: 'warning' },
      { parameter: 'CHT', actual: 172, expected: 168, residual: 4, contribution: 'Medium', status: 'warning' },
      { parameter: 'Fuel Flow', actual: 3.3, expected: 3.1, residual: 0.2, contribution: 'Low', status: 'normal' },
    ],
    metrics: {
      engineHealth: 96,
      anomalyScore: 0.58,
      diagnosticConfidence: 81,
      rul: 162,
      missionRisk: 'LOW',
      componentHealth: 93,
    },
  },
  {
    id: 'load',
    name: 'High Engine Load',
    probability: 28,
    severity: 'watch',
    component: 'Power / Load',
    status: 'PENDING',
    summary: 'The current operating point keeps the engine near the high-load envelope. This is increasing thermal and mechanical stress, but not yet dominant.',
    evidence: [
      { parameter: 'Engine Load', actual: 76, expected: 68, residual: 8, contribution: 'Medium', status: 'watch' },
      { parameter: 'CHT', actual: 172, expected: 166, residual: 6, contribution: 'Medium', status: 'warning' },
      { parameter: 'RPM', actual: 5100, expected: 5050, residual: 50, contribution: 'Low', status: 'normal' },
      { parameter: 'Oil Temp', actual: 92, expected: 90, residual: 2, contribution: 'Low', status: 'normal' },
    ],
    metrics: {
      engineHealth: 95,
      anomalyScore: 0.47,
      diagnosticConfidence: 78,
      rul: 175,
      missionRisk: 'LOW',
      componentHealth: 91,
    },
  },
  {
    id: 'sensor',
    name: 'CHT Sensor Bias',
    probability: 9,
    severity: 'normal',
    component: 'Sensor Integrity',
    status: 'REVIEW',
    summary: 'Sensor drift remains a secondary possibility, but correlated EGT and load evidence reduces the likelihood that the signal is isolated to a single sensor.',
    evidence: [
      { parameter: 'CHT Sensor', actual: 'VALID', expected: 'VALID', residual: 'None', contribution: 'Low', status: 'valid' },
      { parameter: 'EGT Sensor', actual: 'VALID', expected: 'VALID', residual: 'None', contribution: 'Low', status: 'valid' },
      { parameter: 'RPM Sensor', actual: 'VALID', expected: 'VALID', residual: 'None', contribution: 'Low', status: 'valid' },
      { parameter: 'Telemetry Stream', actual: 'STABLE', expected: 'STABLE', residual: 'None', contribution: 'Low', status: 'stable' },
    ],
    metrics: {
      engineHealth: 97,
      anomalyScore: 0.12,
      diagnosticConfidence: 96,
      rul: 181,
      missionRisk: 'LOW',
      componentHealth: 98,
    },
  },
];

const physicsResidualRows = [
  { parameter: 'CHT', actual: 172, expected: 165, residual: 7, unit: '°C' },
  { parameter: 'EGT', actual: 648, expected: 640, residual: 8, unit: '°C' },
  { parameter: 'Oil Pressure', actual: 4.2, expected: 4.3, residual: -0.1, unit: 'bar' },
  { parameter: 'RPM', actual: 5100, expected: 5092, residual: 8, unit: 'RPM' },
];

const residualSeries = {
  CHT: [
    { time: '00:00', actual: 165, expected: 164, threshold: 175 },
    { time: '00:10', actual: 167, expected: 164, threshold: 175 },
    { time: '00:20', actual: 169, expected: 165, threshold: 175 },
    { time: '00:30', actual: 171, expected: 165, threshold: 175 },
    { time: '00:40', actual: 172, expected: 165, threshold: 175 },
    { time: '00:50', actual: 174, expected: 166, threshold: 175 },
  ],
  EGT: [
    { time: '00:00', actual: 635, expected: 632, threshold: 665 },
    { time: '00:10', actual: 639, expected: 634, threshold: 665 },
    { time: '00:20', actual: 642, expected: 636, threshold: 665 },
    { time: '00:30', actual: 645, expected: 638, threshold: 665 },
    { time: '00:40', actual: 648, expected: 640, threshold: 665 },
    { time: '00:50', actual: 650, expected: 640, threshold: 665 },
  ],
  RPM: [
    { time: '00:00', actual: 5088, expected: 5090, threshold: 5200 },
    { time: '00:10', actual: 5091, expected: 5091, threshold: 5200 },
    { time: '00:20', actual: 5094, expected: 5092, threshold: 5200 },
    { time: '00:30', actual: 5098, expected: 5092, threshold: 5200 },
    { time: '00:40', actual: 5100, expected: 5092, threshold: 5200 },
    { time: '00:50', actual: 5104, expected: 5092, threshold: 5200 },
  ],
  'Oil Pressure': [
    { time: '00:00', actual: 4.3, expected: 4.3, threshold: 3.8 },
    { time: '00:10', actual: 4.3, expected: 4.3, threshold: 3.8 },
    { time: '00:20', actual: 4.2, expected: 4.3, threshold: 3.8 },
    { time: '00:30', actual: 4.2, expected: 4.3, threshold: 3.8 },
    { time: '00:40', actual: 4.2, expected: 4.3, threshold: 3.8 },
    { time: '00:50', actual: 4.2, expected: 4.3, threshold: 3.8 },
  ],
  'Oil Temperature': [
    { time: '00:00', actual: 88, expected: 87, threshold: 105 },
    { time: '00:10', actual: 89, expected: 88, threshold: 105 },
    { time: '00:20', actual: 90, expected: 89, threshold: 105 },
    { time: '00:30', actual: 91, expected: 90, threshold: 105 },
    { time: '00:40', actual: 92, expected: 90, threshold: 105 },
    { time: '00:50', actual: 93, expected: 91, threshold: 105 },
  ],
  'Fuel Flow': [
    { time: '00:00', actual: 3.1, expected: 3.0, threshold: 4.2 },
    { time: '00:10', actual: 3.2, expected: 3.1, threshold: 4.2 },
    { time: '00:20', actual: 3.2, expected: 3.1, threshold: 4.2 },
    { time: '00:30', actual: 3.3, expected: 3.1, threshold: 4.2 },
    { time: '00:40', actual: 3.3, expected: 3.1, threshold: 4.2 },
    { time: '00:50', actual: 3.4, expected: 3.2, threshold: 4.2 },
  ],
  Vibration: [
    { time: '00:00', actual: 1.4, expected: 1.2, threshold: 2.5 },
    { time: '00:10', actual: 1.5, expected: 1.2, threshold: 2.5 },
    { time: '00:20', actual: 1.5, expected: 1.3, threshold: 2.5 },
    { time: '00:30', actual: 1.6, expected: 1.3, threshold: 2.5 },
    { time: '00:40', actual: 1.7, expected: 1.4, threshold: 2.5 },
    { time: '00:50', actual: 1.8, expected: 1.4, threshold: 2.5 },
  ],
};

const sensorStatusData = [
  { sensor: 'CHT Sensor', status: 'VALID', confidence: 96 },
  { sensor: 'EGT Sensor', status: 'VALID', confidence: 98 },
  { sensor: 'RPM Sensor', status: 'VALID', confidence: 99 },
  { sensor: 'Oil Pressure Sensor', status: 'VALID', confidence: 97 },
  { sensor: 'Telemetry Stream', status: 'STABLE', confidence: 95 },
];

const degradationSeries = {
  'Engine Health': [
    { mission: 'Mission 01', value: 98 },
    { mission: 'Mission 20', value: 96 },
    { mission: 'Mission 50', value: 93 },
    { mission: 'Mission 80', value: 87 },
    { mission: 'Mission 100', value: 81 },
  ],
  'Cooling Health': [
    { mission: 'Mission 01', value: 98 },
    { mission: 'Mission 20', value: 94 },
    { mission: 'Mission 50', value: 88 },
    { mission: 'Mission 80', value: 82 },
    { mission: 'Mission 100', value: 74 },
  ],
  'Mechanical Health': [
    { mission: 'Mission 01', value: 97 },
    { mission: 'Mission 20', value: 96 },
    { mission: 'Mission 50', value: 92 },
    { mission: 'Mission 80', value: 89 },
    { mission: 'Mission 100', value: 84 },
  ],
  'Lubrication Health': [
    { mission: 'Mission 01', value: 99 },
    { mission: 'Mission 20', value: 98 },
    { mission: 'Mission 50', value: 96 },
    { mission: 'Mission 80', value: 93 },
    { mission: 'Mission 100', value: 91 },
  ],
};

const eventHistory = [
  { time: '21:14:32', event: 'CHT deviation detected', component: 'Cooling', severity: 'warning', probability: '82%', confidence: '89%', status: 'Active', action: 'Monitor' },
  { time: '21:11:08', event: 'EGT deviation', component: 'Combustion', severity: 'warning', probability: '71%', confidence: '84%', status: 'Resolved', action: 'Review' },
  { time: '20:52:41', event: 'Vibration spike', component: 'Mechanical', severity: 'warning', probability: '64%', confidence: '79%', status: 'Resolved', action: 'Monitor' },
  { time: '20:47:09', event: 'Fuel flow variation', component: 'Fuel', severity: 'watch', probability: '38%', confidence: '76%', status: 'Resolved', action: 'Monitor' },
];

const timeline = [
  { time: '02:41:18', title: 'CHT deviation detected' },
  { time: '02:41:23', title: 'Thermal anomaly classified' },
  { time: '02:41:31', title: 'Cooling health reduced' },
  { time: '02:41:45', title: 'RUL recalculated' },
  { time: '02:42:02', title: 'Mission risk increased' },
];

function getBadgeClass(status) {
  const normalized = String(status || 'unknown').toLowerCase();
  return statusPalette[normalized] || statusPalette.unknown;
}

function DiagnosticsHeader({ onRefresh }) {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    if (!onRefresh) return;
    setIsRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <div className="dashboard-header flex-col lg:flex-row">
      <div>
        <div className="dashboard-eyebrow">Diagnostics</div>
        <h2>Engine fault detection, health assessment and root-cause analysis</h2>
      </div>

      <div className="dashboard-status-row">
        <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 font-semibold text-emerald-700">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          LIVE
        </span>
        <span className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 font-semibold text-slate-700">Digital Twin: SYNCHRONIZED</span>
        <span className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 font-semibold text-slate-700">Data Quality: 98.7%</span>
        <span className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 font-mono font-bold text-slate-800">Last Update: 21:14:32</span>
        <button
          type="button"
          onClick={handleRefresh}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 font-semibold text-slate-700 transition hover:bg-slate-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
          {isRefreshing ? 'Refreshing' : 'Refresh'}
        </button>
      </div>
    </div>
  );
}

function SummaryMetric({ label, value, sublabel, tone = 'default' }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
      <div className="mb-1 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">{label}</div>
      <div className="flex items-end justify-between gap-3">
        <div className="text-2xl font-black tracking-tight text-slate-900">{value}</div>
        {tone === 'warning' && <AlertTriangle className="h-4 w-4 text-amber-600" />}
        {tone === 'critical' && <TriangleAlert className="h-4 w-4 text-red-600" />}
        {tone === 'good' && <CheckCircle2 className="h-4 w-4 text-emerald-600" />}
      </div>
      {sublabel && <div className="mt-1 text-[10px] text-slate-500">{sublabel}</div>}
    </div>
  );
}

function FaultProbabilityItem({ name, value, active, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full rounded-xl border p-2 text-left transition ${active ? 'border-blue-200 bg-blue-50/80' : 'border-slate-200 bg-slate-50/60 hover:border-slate-300 hover:bg-white'}`}
    >
      <div className="mb-1 flex items-center justify-between gap-3">
        <span className="text-[11px] font-semibold text-slate-700">{name}</span>
        <span className="font-mono text-[11px] font-bold text-slate-800">{value}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-200">
        <div className="h-full rounded-full bg-blue-500" style={{ width: `${value}%` }} />
      </div>
    </button>
  );
}

function ActiveFaultPanel({ selectedFault, onSelectHypothesis }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-4">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Active Diagnostic Event</div>
          <div className="mt-1 text-lg font-black tracking-tight text-slate-900">Probable Fault</div>
        </div>
        <span className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase ${getBadgeClass(selectedFault.severity)}`}>
          {selectedFault.severity}
        </span>
      </div>

      <div className="mb-3 grid gap-3 lg:grid-cols-[1.3fr_0.7fr]">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Fault</div>
          <div className="mt-1 text-2xl font-black tracking-tight text-slate-900">{selectedFault.name}</div>
          <div className="mt-2 text-sm leading-6 text-slate-600">{selectedFault.summary}</div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
          <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">
            <span>Fault Probability</span>
            <span className="font-mono text-slate-800">{selectedFault.probability}%</span>
          </div>
          <div className="mt-3 h-2.5 overflow-hidden rounded-full bg-slate-200">
            <div className="h-full rounded-full bg-amber-500" style={{ width: `${selectedFault.probability}%` }} />
          </div>
          <div className="mt-4 grid grid-cols-2 gap-2 text-[11px] text-slate-600">
            <div>
              <div className="font-semibold uppercase tracking-[0.14em] text-slate-500">Diagnostic Confidence</div>
              <div className="mt-1 font-mono text-base font-bold text-slate-900">89%</div>
            </div>
            <div>
              <div className="font-semibold uppercase tracking-[0.14em] text-slate-500">Status</div>
              <div className="mt-1 font-mono text-base font-bold text-slate-900">ACTIVE</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
          <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Detected</div>
          <div className="mt-1 font-mono text-sm font-bold text-slate-900">02:41:18</div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
          <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Duration</div>
          <div className="mt-1 font-mono text-sm font-bold text-slate-900">00:03:27</div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
          <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Component</div>
          <div className="mt-1 text-sm font-bold text-slate-900">{selectedFault.component}</div>
        </div>
      </div>

      <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3">
        <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Fault Ranking</div>
        <div className="space-y-2">
          {faultHypotheses.map((fault) => (
            <FaultProbabilityItem
              key={fault.id}
              name={fault.name}
              value={fault.probability}
              active={fault.id === selectedFault.id}
              onClick={() => onSelectHypothesis(fault.id)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function PhysicsAiAssessment({ selectedFault }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4 text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Physics + AI Assessment</div>
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
          <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Physics Model</div>
          <div className="text-sm font-semibold text-slate-700">Expected behavior</div>
          <div className="mt-3 space-y-2 text-sm text-slate-700">
            {physicsResidualRows.map((row) => (
              <div key={row.parameter} className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white px-2 py-1.5">
                <span className="font-semibold text-slate-700">{row.parameter}</span>
                <span className="font-mono text-slate-900">{row.expected}{row.unit}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
          <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">AI / ML Model</div>
          <div className="text-sm font-semibold text-slate-700">Observed anomaly pattern</div>
          <div className="mt-3 space-y-2 text-sm text-slate-700">
            {physicsResidualRows.map((row) => (
              <div key={`${row.parameter}-actual`} className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white px-2 py-1.5">
                <span className="font-semibold text-slate-700">{row.parameter}</span>
                <span className="font-mono text-slate-900">{row.actual}{row.unit}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
          <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Actual vs Expected</div>
          <div className="text-sm font-semibold text-slate-700">Residual</div>
          <div className="mt-3 space-y-2">
            {physicsResidualRows.map((row) => (
              <div key={`${row.parameter}-residual`} className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white px-2 py-1.5">
                <span className="font-semibold text-slate-700">{row.parameter}</span>
                <span className={`font-mono font-bold ${row.residual > 0 ? 'text-amber-700' : 'text-emerald-700'}`}>
                  {row.residual > 0 ? '+' : ''}{row.residual}{row.unit}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
        <strong className="font-bold">Current diagnostic basis:</strong> {selectedFault.summary}
      </div>
    </div>
  );
}

function ResidualChart({ selectedParam, onSelectParam }) {
  const currentData = residualSeries[selectedParam] || residualSeries.CHT;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Model Residual Analysis</div>
          <div className="text-lg font-black tracking-tight text-slate-900">Residual trend</div>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {Object.keys(residualSeries).map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => onSelectParam(key)}
              className={`rounded-lg border px-2 py-1 text-[10px] font-bold uppercase tracking-[0.08em] transition ${selectedParam === key ? 'border-blue-600 bg-blue-600 text-white' : 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-white'}`}
            >
              {key}
            </button>
          ))}
        </div>
      </div>

      <div className="aero-chart h-64 w-full rounded-lg">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={currentData}>
            <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="time" tickLine={false} axisLine={false} tick={{ fill: '#64748b', fontSize: 11 }} />
            <YAxis tickLine={false} axisLine={false} tick={{ fill: '#64748b', fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 11 }}
            />
            <Line type="monotone" dataKey="expected" stroke="#3b82f6" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="actual" stroke="#1e293b" strokeWidth={2.2} dot={false} />
            <Line type="monotone" dataKey="threshold" stroke="#f59e0b" strokeWidth={1.5} strokeDasharray="6 4" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function DiagnosticEvidence({ selectedFault }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Diagnostic Evidence</div>
      <div className="space-y-3">
        {selectedFault.evidence.map((item) => (
          <div key={item.parameter} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <div className="mb-1 flex items-center justify-between gap-4">
              <span className="text-sm font-bold text-slate-800">{item.parameter}</span>
              <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${getBadgeClass(item.status)}`}>{item.status}</span>
            </div>
            <div className="grid gap-2 text-[11px] text-slate-600 sm:grid-cols-3">
              <div>
                <div className="font-semibold uppercase tracking-[0.12em] text-slate-500">Current</div>
                <div className="mt-1 font-mono font-bold text-slate-900">{item.actual}</div>
              </div>
              <div>
                <div className="font-semibold uppercase tracking-[0.12em] text-slate-500">Deviation</div>
                <div className="mt-1 font-mono font-bold text-slate-900">{item.residual > 0 ? '+' : ''}{item.residual}</div>
              </div>
              <div>
                <div className="font-semibold uppercase tracking-[0.12em] text-slate-500">Contribution</div>
                <div className="mt-1 font-bold text-slate-900">{item.contribution}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SensorIntegrityPanel() {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Sensor Integrity Check</div>
      <div className="space-y-2">
        {sensorStatusData.map((item) => (
          <div key={item.sensor} className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
            <div className="flex items-center gap-2">
              <div className="text-sm font-bold text-slate-800">{item.sensor}</div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${getBadgeClass(item.status.toLowerCase())}`}>{item.status}</span>
              <span className="font-mono text-[11px] font-bold text-slate-700">{item.confidence}%</span>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 rounded-xl border border-blue-200 bg-blue-50 p-3">
        <div className="grid gap-2 sm:grid-cols-2">
          <div>
            <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Engine Fault Likelihood</div>
            <div className="mt-1 font-mono text-xl font-black text-slate-900">91%</div>
          </div>
          <div>
            <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Sensor Fault Likelihood</div>
            <div className="mt-1 font-mono text-xl font-black text-slate-900">9%</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ComponentHealthPanel({ selectedComponent, setSelectedComponent }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Component Health</div>
          <div className="mt-1 text-lg font-black tracking-tight text-slate-900">Subsystem condition</div>
        </div>
      </div>

      <div className="space-y-3">
        {COMPONENT_HEALTH.map((component) => (
          <button
            key={component.name}
            type="button"
            onClick={() => setSelectedComponent(component.name)}
            className={`w-full rounded-xl border p-3 text-left transition ${selectedComponent === component.name ? 'border-blue-200 bg-blue-50/80' : 'border-slate-200 bg-slate-50 hover:bg-white'}`}
          >
            <div className="mb-2 flex items-center justify-between gap-3">
              <div className="text-sm font-bold text-slate-800">{component.name}</div>
              <div className="font-mono text-sm font-black text-slate-900">{component.pct}%</div>
            </div>
            <div className="mb-2 h-2.5 overflow-hidden rounded-full bg-slate-200">
              <div className={`h-full rounded-full ${component.status === 'warning' ? 'bg-amber-500' : 'bg-emerald-500'}`} style={{ width: `${component.pct}%` }} />
            </div>
            <div className="flex items-center justify-between text-[10px] uppercase tracking-[0.15em] text-slate-500">
              <span>Trend</span>
              <span className={component.status === 'warning' ? 'text-amber-700' : 'text-emerald-700'}>{component.status === 'warning' ? '↓' : '→'}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function DegradationChart({ selectedComponent, setSelectedComponent }) {
  const metricOptions = ['Engine Health', 'Cooling Health', 'Mechanical Health', 'Lubrication Health'];
  const series = degradationSeries[selectedComponent] || degradationSeries['Engine Health'];

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Component Degradation</div>
          <div className="text-lg font-black tracking-tight text-slate-900">Health history</div>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {metricOptions.map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => setSelectedComponent(key)}
              className={`rounded-lg border px-2 py-1 text-[10px] font-bold uppercase tracking-[0.08em] transition ${selectedComponent === key ? 'border-blue-600 bg-blue-600 text-white' : 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-white'}`}
            >
              {key}
            </button>
          ))}
        </div>
      </div>

      <div className="aero-chart h-60 w-full rounded-lg">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={series}>
            <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="mission" tickLine={false} axisLine={false} tick={{ fill: '#64748b', fontSize: 11 }} />
            <YAxis domain={[60, 100]} tickLine={false} axisLine={false} tick={{ fill: '#64748b', fontSize: 11 }} />
            <Tooltip contentStyle={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 11 }} />
            <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2.2} dot={{ fill: '#3b82f6', r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function RulPrediction() {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Remaining Useful Life</div>
      <div className="mb-2 flex items-end justify-between gap-3">
        <div className="text-4xl font-black tracking-tight text-slate-900">143 h</div>
        <span className="rounded-full border border-amber-200 bg-amber-50 px-2 py-1 text-[10px] font-bold uppercase text-amber-700">Gradual degradation</span>
      </div>
      <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3">
        <div className="mb-2 flex items-center justify-between text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">
          <span>Prediction range</span>
          <span className="font-mono text-slate-800">128–158 h</span>
        </div>
        <div className="mb-2 flex items-center justify-between text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">
          <span>Confidence</span>
          <span className="font-mono text-slate-800">82%</span>
        </div>
        <div className="relative mt-3 h-3 overflow-hidden rounded-full bg-slate-200">
          <div className="absolute inset-y-0 left-0 w-1/2 rounded-full bg-blue-500" />
          <div className="absolute inset-y-0 left-1/2 w-1/3 rounded-full bg-amber-500" />
        </div>
        <div className="mt-2 flex items-center justify-between text-[10px] font-bold uppercase tracking-[0.12em] text-slate-500">
          <span>128 h</span>
          <span className="font-mono text-slate-800">143 h</span>
          <span>158 h</span>
        </div>
      </div>
      <div className="mt-4 text-[11px] text-slate-600">
        Basis: degradation history, current component health, operating load, temperature, vibration, and fault state.
      </div>
    </div>
  );
}

function MissionImpactCard({ onNavigate }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Mission Impact</div>
      <div className="mb-4 grid gap-3 sm:grid-cols-2">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Mission Completion Probability</div>
          <div className="mt-1 text-3xl font-black tracking-tight text-slate-900">87%</div>
        </div>
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Risk Level</div>
          <div className="mt-1 inline-flex rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-[10px] font-bold uppercase text-amber-700">MODERATE</div>
        </div>
      </div>
      <div className="space-y-2 text-sm text-slate-600">
        <div><span className="font-semibold text-slate-800">Primary Risk:</span> Rising CHT</div>
        <div><span className="font-semibold text-slate-800">Expected Impact:</span> Reduced sustained high-load capability</div>
        <div><span className="font-semibold text-slate-800">Recommended Operational Response:</span> Reduce prolonged high throttle and continue monitoring.</div>
      </div>
      <button
        type="button"
        onClick={() => onNavigate('mission')}
        className="mt-4 inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.12em] text-slate-700 transition hover:bg-white"
      >
        View Mission Impact <ChevronRight className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

function RecommendedAction() {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Recommended Action</div>
      <div className="mb-3 inline-flex rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-[10px] font-bold uppercase text-amber-700">MONITOR</div>
      <div className="space-y-2 text-sm text-slate-600">
        <div><span className="font-semibold text-slate-800">Reason:</span> Cooling performance is degrading while oil pressure remains normal.</div>
        <div><span className="font-semibold text-slate-800">Recommended:</span> Reduce prolonged high-load operation, monitor CHT and EGT, review cooling system after mission.</div>
      </div>
      <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3">
        <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Priority</div>
        <div className="mt-1 text-lg font-black tracking-tight text-slate-900">MEDIUM</div>
      </div>
    </div>
  );
}

function DiagnosticTimeline() {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Diagnostic Timeline</div>
      <div className="space-y-4">
        {timeline.map((item, index) => (
          <div key={item.time} className="flex gap-3">
            <div className="flex w-20 shrink-0 justify-end pt-0.5 font-mono text-[11px] font-bold text-slate-500">{item.time}</div>
            <div className="relative flex flex-col items-center">
              <span className="h-3.5 w-3.5 rounded-full border-2 border-blue-500 bg-white" />
              {index < timeline.length - 1 && <span className="mt-1 h-full w-px bg-slate-200" />}
            </div>
            <div className="pb-3 text-sm font-medium text-slate-700">{item.title}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function EventHistoryTable() {
  const [severityFilter, setSeverityFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortKey, setSortKey] = useState('time');
  const [sortDirection, setSortDirection] = useState('desc');

  const filteredRows = useMemo(() => {
    const next = eventHistory.filter((row) => {
      const matchesSeverity = severityFilter === 'all' || row.severity === severityFilter;
      const matchesStatus = statusFilter === 'all' || row.status.toLowerCase() === statusFilter.toLowerCase();
      return matchesSeverity && matchesStatus;
    });

    return [...next].sort((a, b) => {
      const left = a[sortKey] ?? '';
      const right = b[sortKey] ?? '';
      if (sortKey === 'probability' || sortKey === 'confidence') {
        return sortDirection === 'asc'
          ? Number.parseInt(left, 10) - Number.parseInt(right, 10)
          : Number.parseInt(right, 10) - Number.parseInt(left, 10);
      }
      if (sortKey === 'time') {
        return sortDirection === 'asc'
          ? a.time.localeCompare(b.time)
          : b.time.localeCompare(a.time);
      }
      return sortDirection === 'asc'
        ? String(left).localeCompare(String(right))
        : String(right).localeCompare(String(left));
    });
  }, [severityFilter, statusFilter, sortKey, sortDirection]);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Diagnostic Event History</div>
          <div className="mt-1 text-lg font-black tracking-tight text-slate-900">Engineering event log</div>
        </div>
        <div className="flex flex-wrap gap-2">
          <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)} className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-1.5 text-[11px] font-semibold text-slate-700 outline-none focus:border-blue-500">
            <option value="all">All severities</option>
            <option value="warning">Warning</option>
            <option value="watch">Watch</option>
          </select>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-1.5 text-[11px] font-semibold text-slate-700 outline-none focus:border-blue-500">
            <option value="all">All states</option>
            <option value="active">Active</option>
            <option value="resolved">Resolved</option>
          </select>
          <select value={sortKey} onChange={(e) => setSortKey(e.target.value)} className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-1.5 text-[11px] font-semibold text-slate-700 outline-none focus:border-blue-500">
            <option value="time">Sort: Time</option>
            <option value="severity">Sort: Severity</option>
            <option value="probability">Sort: Probability</option>
            <option value="confidence">Sort: Confidence</option>
          </select>
          <button
            type="button"
            onClick={() => {
              setSortDirection((current) => (current === 'asc' ? 'desc' : 'asc'));
            }}
            className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-1.5 text-[11px] font-semibold text-slate-700"
          >
            Sort: {sortDirection === 'asc' ? 'Asc' : 'Desc'}
          </button>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200">
        <table className="min-w-full border-collapse text-left text-[11px]">
          <thead className="bg-slate-100 text-slate-600">
            <tr>
              <th className="px-3 py-2 font-bold uppercase tracking-[0.12em]">Timestamp</th>
              <th className="px-3 py-2 font-bold uppercase tracking-[0.12em]">Event</th>
              <th className="px-3 py-2 font-bold uppercase tracking-[0.12em]">Component</th>
              <th className="px-3 py-2 font-bold uppercase tracking-[0.12em]">Severity</th>
              <th className="px-3 py-2 font-bold uppercase tracking-[0.12em]">Probability</th>
              <th className="px-3 py-2 font-bold uppercase tracking-[0.12em]">Confidence</th>
              <th className="px-3 py-2 font-bold uppercase tracking-[0.12em]">Status</th>
              <th className="px-3 py-2 font-bold uppercase tracking-[0.12em]">Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row) => (
              <tr key={`${row.time}-${row.event}`} className="border-t border-slate-200 bg-white hover:bg-slate-50/80">
                <td className="px-3 py-2 font-mono font-bold text-slate-800">{row.time}</td>
                <td className="px-3 py-2 font-semibold text-slate-800">{row.event}</td>
                <td className="px-3 py-2 text-slate-700">{row.component}</td>
                <td className="px-3 py-2"><span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${getBadgeClass(row.severity)}`}>{row.severity}</span></td>
                <td className="px-3 py-2 font-mono font-bold text-slate-800">{row.probability}</td>
                <td className="px-3 py-2 font-mono font-bold text-slate-800">{row.confidence}</td>
                <td className="px-3 py-2"><span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${getBadgeClass(row.status.toLowerCase())}`}>{row.status}</span></td>
                <td className="px-3 py-2 text-slate-700">{row.action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function DiagnosticsView({ _diagnostics = DEFAULT_DIAGNOSTICS, onNavigate, onRefresh }) {
  const [selectedFaultId, setSelectedFaultId] = useState('cooling');
  const [selectedParam, setSelectedParam] = useState('CHT');
  const [selectedComponent, setSelectedComponent] = useState('Cooling Health');
  const [liveDiagnostics, setLiveDiagnostics] = useState(_diagnostics || DEFAULT_DIAGNOSTICS);
  const [latestExplainability, setLatestExplainability] = useState(null);

  useEffect(() => {
    const loadLiveDiagnostics = async () => {
      try {
        const stateResponse = await fetch(`/api/engine/${ENGINE_ID}/state`);
        const stateData = stateResponse.ok ? await stateResponse.json() : null;

        const telemetryFrame = buildTelemetryFrame(stateData?.telemetry ?? EMPTY_TELEMETRY);
        const [inferenceResponse, explanationResponse] = await Promise.all([
          fetch('/api/inference/assess', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ engine_id: ENGINE_ID, telemetry: telemetryFrame }),
          }),
          fetch('/api/inference/explain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ engine_id: ENGINE_ID, telemetry: telemetryFrame }),
          }),
        ]);

        const inferenceData = inferenceResponse.ok ? await inferenceResponse.json() : null;
        const explanationData = explanationResponse.ok ? await explanationResponse.json() : null;

        const mergedDiagnostics = {
          ...(stateData || {}),
          ...(inferenceData || {}),
          explainability: explanationData || null,
        };

        setLiveDiagnostics(mergedDiagnostics);
        setLatestExplainability(explanationData || null);
      } catch (error) {
        setLiveDiagnostics(_diagnostics || DEFAULT_DIAGNOSTICS);
        setLatestExplainability(null);
      }
    };

    loadLiveDiagnostics();
  }, [_diagnostics]);

  const liveHealth = Number(liveDiagnostics?.health?.health_index ?? liveDiagnostics?.engine_health ?? 94);
  const liveFaultProbability = Number(liveDiagnostics?.fault_probability ?? liveDiagnostics?.latest_prediction?.fault_probability ?? 82);
  const liveFaultType = liveDiagnostics?.probable_fault ?? liveDiagnostics?.latest_prediction?.fault_type ?? liveDiagnostics?.latest_fault?.fault_type ?? 'NORMAL';
  const liveAnomalyScore = Number(liveDiagnostics?.anomaly_score ?? liveDiagnostics?.latest_prediction?.anomaly_score ?? 0.82);
  const liveRulHours = Number(liveDiagnostics?.estimated_rul_hours ?? liveDiagnostics?.latest_prediction?.rul_hours ?? 143);
  const liveFaultStatus = liveDiagnostics?.latest_fault?.status ?? (liveFaultType === 'NORMAL' ? 'RESOLVED' : 'ACTIVE');

  const liveEvidence = liveDiagnostics?.evidence ?? liveDiagnostics?.latest_prediction?.evidence ?? {};
  const evidenceRows = Object.entries(liveEvidence)
    .filter(([, value]) => typeof value === 'number' || typeof value === 'string')
    .slice(0, 4)
    .map(([parameter, value]) => ({
      parameter: parameter.replace(/_/g, ' '),
      actual: value,
      expected: value,
      residual: 0,
      contribution: 'Live',
      status: value > 0 ? 'warning' : 'normal',
    }));

  const activeFaultName = liveFaultType === 'NORMAL' ? 'Normal Operation' : liveFaultType.replace(/_/g, ' ');

  const selectedFault = useMemo(
    () => {
      const fallback = faultHypotheses.find((fault) => fault.id === selectedFaultId) || faultHypotheses[0];
      return {
        ...fallback,
        id: selectedFaultId,
        name: activeFaultName,
        probability: Math.max(0, Math.min(100, liveFaultProbability)),
        severity: liveFaultType === 'NORMAL' ? 'normal' : liveFaultProbability >= 70 ? 'warning' : 'watch',
        summary: latestExplainability?.summary || fallback.summary,
        component: liveDiagnostics?.latest_fault?.source || fallback.component,
        evidence: evidenceRows.length ? evidenceRows : fallback.evidence,
        metrics: {
          ...fallback.metrics,
          engineHealth: Math.round(liveHealth),
          anomalyScore: liveAnomalyScore,
          diagnosticConfidence: Math.round(liveFaultProbability),
          rul: Math.round(liveRulHours),
          missionRisk: liveFaultProbability >= 70 ? 'MODERATE' : 'LOW',
          componentHealth: Math.max(0, Math.min(100, Math.round(liveHealth * 0.98))),
        },
      };
    }, [activeFaultName, evidenceRows, latestExplainability, liveDiagnostics, liveFaultProbability, liveFaultType, liveHealth, liveRulHours, liveAnomalyScore, selectedFaultId]
  );

  const summaryStats = useMemo(
    () => [
      { label: 'ENGINE HEALTH', value: `${Math.round(liveHealth)}%`, sublabel: 'System condition', tone: 'good' },
      { label: 'FAULT STATUS', value: `${liveFaultStatus === 'ACTIVE' ? '1 ACTIVE' : '0 ACTIVE'}`, sublabel: liveFaultType === 'NORMAL' ? 'No active fault' : activeFaultName, tone: liveFaultStatus === 'ACTIVE' ? 'warning' : 'good' },
      { label: 'ANOMALY SCORE', value: liveAnomalyScore.toFixed(2), sublabel: 'Residual level', tone: 'warning' },
      { label: 'RUL', value: `${Math.round(liveRulHours)} h`, sublabel: `Prediction range ${Math.round(liveRulHours * 0.85)}–${Math.round(liveRulHours * 1.15)} h`, tone: 'default' },
      { label: 'CONFIDENCE', value: `${Math.round(liveFaultProbability)}%`, sublabel: 'Diagnostic confidence', tone: 'good' },
      { label: 'MISSION RISK', value: liveFaultProbability >= 70 ? 'MODERATE' : 'LOW', sublabel: 'Current mission impact', tone: liveFaultProbability >= 70 ? 'warning' : 'good' },
    ],
    [activeFaultName, liveAnomalyScore, liveFaultProbability, liveFaultStatus, liveHealth, liveRulHours, liveFaultType]
  );

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="page-shell space-y-5">
        <DiagnosticsHeader onRefresh={onRefresh} />

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
          {summaryStats.map((stat) => (
            <SummaryMetric key={stat.label} label={stat.label} value={stat.value} sublabel={stat.sublabel} tone={stat.tone} />
          ))}
        </div>

        <div className="grid gap-4 xl:grid-cols-[1.4fr_0.9fr]">
          <ActiveFaultPanel selectedFault={selectedFault} onSelectHypothesis={setSelectedFaultId} />
          <div className="space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">What-If Analysis</div>
              <div className="text-sm leading-6 text-slate-600">
                Current condition indicates increased thermal stress. Scenario: increase cruise altitude 5,000 ft → 8,000 ft.
              </div>
              <div className="mt-3 space-y-2 text-sm text-slate-700">
                <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2"><span>CHT</span><span className="font-mono font-bold text-amber-700">+6 °C</span></div>
                <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2"><span>EGT</span><span className="font-mono font-bold text-amber-700">+20 °C</span></div>
                <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2"><span>Health</span><span className="font-mono font-bold text-red-700">-3%</span></div>
                <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2"><span>RUL</span><span className="font-mono font-bold text-red-700">-7 h</span></div>
              </div>
              <button
                type="button"
                onClick={() => onNavigate && onNavigate('simulation')}
                className="mt-4 inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.12em] text-slate-700 transition hover:bg-white"
              >
                Run What-If Simulation <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Quick Actions</div>
              <div className="flex flex-wrap gap-2">
                <button type="button" onClick={() => onNavigate && onNavigate('telemetry')} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.14em] text-slate-700">View Telemetry</button>
                <button type="button" onClick={() => onNavigate && onNavigate('mission')} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.14em] text-slate-700">View Mission Impact</button>
                <button type="button" onClick={() => onNavigate && onNavigate('reports')} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.14em] text-slate-700">Generate Diagnostic Report</button>
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
          <PhysicsAiAssessment selectedFault={selectedFault} />
          <DiagnosticTimeline />
        </div>

        <div className="grid gap-4 xl:grid-cols-2">
          <ResidualChart selectedParam={selectedParam} onSelectParam={setSelectedParam} />
          <DiagnosticEvidence selectedFault={selectedFault} />
        </div>

        <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
          <SensorIntegrityPanel />
          <ComponentHealthPanel selectedComponent={selectedComponent} setSelectedComponent={setSelectedComponent} />
        </div>

        <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
          <DegradationChart selectedComponent={selectedComponent} setSelectedComponent={setSelectedComponent} />
          <RulPrediction />
        </div>

        <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
          <MissionImpactCard onNavigate={onNavigate} />
          <RecommendedAction />
        </div>

        <EventHistoryTable />
      </div>
    </div>
  );
}