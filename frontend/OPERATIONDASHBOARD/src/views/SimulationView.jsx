import React, { useMemo, useState } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  ChevronRight,
  Download,
  Gauge,
  RefreshCcw,
  ShieldAlert,
  Thermometer,
  TrendingUp,
  Wind,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const BASELINE = {
  altitude: 5000,
  ambientTemperature: 28,
  windSpeed: 12,
  durationHours: 2.3,
  throttle: 82,
  engineLoad: 78,
  rpm: 5100,
  fuelFlow: 3.3,
  cht: 172,
  egt: 648,
  oilTemp: 92,
  oilPressure: 4.2,
  vibration: 1.8,
  coolingEfficiency: 100,
  mechanicalHealth: 100,
  missionCompletion: 87,
  health: 94,
  rul: 143,
  risk: 'LOW',
};

const PRESETS = {
  CURRENT: { ...BASELINE },
  HIGH_ALTITUDE: {
    ...BASELINE,
    altitude: 8000,
    throttle: 82,
    engineLoad: 82,
    durationHours: 3.2,
  },
  HIGH_THROTTLE: {
    ...BASELINE,
    throttle: 90,
    engineLoad: 86,
    durationHours: 2.8,
  },
  HOT_AMBIENT: {
    ...BASELINE,
    ambientTemperature: 40,
    throttle: 85,
    engineLoad: 82,
    durationHours: 3.1,
  },
  LONG_DURATION: {
    ...BASELINE,
    durationHours: 4.6,
    engineLoad: 81,
    throttle: 84,
  },
  COOLING_DEGRADATION: {
    ...BASELINE,
    coolingEfficiency: 85,
    engineLoad: 82,
    throttle: 84,
    durationHours: 3.0,
  },
  MECHANICAL_DEGRADATION: {
    ...BASELINE,
    mechanicalHealth: 88,
    vibration: 2.4,
    engineLoad: 83,
    throttle: 86,
    durationHours: 2.8,
  },
};

const SCENARIO_HISTORY = [
  { time: '21:14', scenario: 'High Altitude', changed: 'Altitude +3,000 ft', health: '-3%', rul: '-7 h', risk: 'Moderate', result: 'Completed' },
  { time: '21:02', scenario: 'High Throttle', changed: 'Throttle +10%', health: '-5%', rul: '-12 h', risk: 'High', result: 'Completed' },
  { time: '20:49', scenario: 'Hot Ambient', changed: 'Ambient +12 °C', health: '-2%', rul: '-5 h', risk: 'Moderate', result: 'Completed' },
];

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function formatDelta(value, unit = '') {
  const sign = value > 0 ? '+' : '';
  return `${sign}${value}${unit}`;
}

function computeSimulation(scenario) {
  const altitudeDelta = (scenario.altitude - BASELINE.altitude) / 1000;
  const throttleDelta = (scenario.throttle - BASELINE.throttle) / 10;
  const tempDelta = (scenario.ambientTemperature - BASELINE.ambientTemperature) / 10;
  const durationDelta = (scenario.durationHours - BASELINE.durationHours) / 1.5;
  const coolingDelta = (scenario.coolingEfficiency - BASELINE.coolingEfficiency) / 100;
  const mechDelta = (scenario.mechanicalHealth - BASELINE.mechanicalHealth) / 100;

  const predictedCht = BASELINE.cht + altitudeDelta * 11 + throttleDelta * 7 + tempDelta * 6 + (1 - scenario.coolingEfficiency / 100) * 18;
  const predictedEgt = BASELINE.egt + altitudeDelta * 26 + throttleDelta * 18 + tempDelta * 12 + (1 - scenario.coolingEfficiency / 100) * 20;
  const predictedRpm = BASELINE.rpm - altitudeDelta * 120 + throttleDelta * 110;
  const predictedOilTemp = BASELINE.oilTemp + tempDelta * 6 + throttleDelta * 4 + (1 - scenario.coolingEfficiency / 100) * 10;
  const predictedOilPressure = BASELINE.oilPressure - throttleDelta * 0.38 + durationDelta * 0.1;
  const predictedFuelFlow = BASELINE.fuelFlow + throttleDelta * 0.28 + altitudeDelta * 0.15;
  const predictedVibration = BASELINE.vibration + Math.max(0, throttleDelta * 0.17) + Math.max(0, -mechDelta) * 0.35;
  const predictedEngineLoad = clamp(BASELINE.engineLoad + throttleDelta * 12 + altitudeDelta * 4, 50, 100);
  const health = clamp(
    BASELINE.health - altitudeDelta * 3.4 - throttleDelta * 3.8 - tempDelta * 2.6 - (1 - scenario.coolingEfficiency / 100) * 8 - (1 - scenario.mechanicalHealth / 100) * 5,
    65,
    99,
  );
  const missionCompletion = clamp(
    BASELINE.missionCompletion - altitudeDelta * 10 - throttleDelta * 8 - tempDelta * 7 - (1 - scenario.coolingEfficiency / 100) * 12,
    40,
    98,
  );
  const rul = clamp(
    BASELINE.rul - Math.max(0, durationDelta * 11) - (1 - scenario.coolingEfficiency / 100) * 24 - (1 - scenario.mechanicalHealth / 100) * 18,
    48,
    180,
  );

  const riskLevel = missionCompletion < 75 ? 'HIGH' : missionCompletion < 85 ? 'MODERATE' : 'LOW';
  const riskPhrase = missionCompletion < 75 ? 'Operation with restriction' : missionCompletion < 85 ? 'Continue with monitoring' : 'Nominal';

  const componentHealth = {
    Cooling: clamp(97 - (1 - scenario.coolingEfficiency / 100) * 34, 68, 99),
    Lubrication: clamp(97 - (1 - scenario.mechanicalHealth / 100) * 12, 70, 100),
    Fuel: clamp(95 - Math.max(0, throttleDelta) * 7 - altitudeDelta * 1.5, 70, 99),
    Ignition: clamp(97 - throttleDelta * 4, 72, 99),
    Mechanical: clamp(BASELINE.mechanicalHealth - (1 - scenario.mechanicalHealth / 100) * 24 - Math.max(0, throttleDelta) * 6, 60, 99),
  };

  const responseSeries = [
    { time: '0', baseline: BASELINE.cht, simulated: predictedCht * 0.92 },
    { time: '0.5h', baseline: BASELINE.cht, simulated: predictedCht * 0.96 },
    { time: '1h', baseline: BASELINE.cht, simulated: predictedCht },
    { time: '1.5h', baseline: BASELINE.cht + 4, simulated: predictedCht + 4 },
    { time: '2h', baseline: BASELINE.cht + 6, simulated: predictedCht + 9 },
    { time: '2.5h', baseline: BASELINE.cht + 8, simulated: predictedCht + 14 },
  ];

  const riskContributors = [
    { label: 'Thermal Stress', value: 24 + Math.max(0, scenario.ambientTemperature - 28) * 0.8 + Math.max(0, scenario.throttle - 82) * 0.9 },
    { label: 'Engine Load', value: 18 + Math.max(0, scenario.engineLoad - BASELINE.engineLoad) * 1.6 },
    { label: 'Fuel Consumption', value: 9 + Math.max(0, predictedFuelFlow - BASELINE.fuelFlow) * 18 },
    { label: 'Mechanical Stress', value: 6 + Math.max(0, BASELINE.mechanicalHealth - scenario.mechanicalHealth) * 0.65 },
  ];

  const sensitivity = [
    { label: 'Altitude', value: 88, level: 'High' },
    { label: 'Throttle', value: 82, level: 'High' },
    { label: 'Ambient Temperature', value: 68, level: 'Medium' },
    { label: 'Mission Duration', value: 44, level: 'Low' },
    { label: 'Cooling Efficiency', value: 76, level: 'High' },
  ];

  const interpretation = `Raising altitude from ${BASELINE.altitude.toLocaleString()} ft to ${scenario.altitude.toLocaleString()} ft increases thermal and combustion stress under the selected throttle condition. The Digital Twin predicts higher EGT and CHT, reducing the available thermal margin and estimated RUL.`;

  return {
    predictedCht,
    predictedEgt,
    predictedRpm,
    predictedOilTemp,
    predictedOilPressure,
    predictedFuelFlow,
    predictedVibration,
    predictedEngineLoad,
    missionCompletion,
    health,
    rul,
    riskLevel,
    riskPhrase,
    componentHealth,
    responseSeries,
    riskContributors,
    sensitivity,
    interpretation,
  };
}

export default function SimulationView({ onNavigate }) {
  const [scenario, setScenario] = useState({ ...BASELINE });
  const [simState, setSimState] = useState('ready');
  const [activePreset, setActivePreset] = useState('CURRENT');
  const [activeMetric, setActiveMetric] = useState('CHT');
  const [lastUpdated, setLastUpdated] = useState('21:14:32');

  const prediction = useMemo(() => computeSimulation(scenario), [scenario]);

  const baselineSummary = useMemo(
    () => ({
      rpm: BASELINE.rpm,
      egt: BASELINE.egt,
      cht: BASELINE.cht,
      oilTemp: BASELINE.oilTemp,
      oilPressure: BASELINE.oilPressure,
      fuelFlow: BASELINE.fuelFlow,
      vibration: BASELINE.vibration,
      engineLoad: BASELINE.engineLoad,
      health: BASELINE.health,
      rul: BASELINE.rul,
      missionCompletion: BASELINE.missionCompletion,
    }),
    [],
  );

  const handlePreset = (key) => {
    setActivePreset(key);
    setScenario({ ...PRESETS[key] });
    setSimState('ready');
  };

  const handleReset = () => {
    setScenario({ ...BASELINE });
    setActivePreset('CURRENT');
    setSimState('ready');
  };

  const handleRunSimulation = () => {
    setSimState('running');
    window.setTimeout(() => {
      setSimState('complete');
      setLastUpdated(
        new Date().toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        }),
      );
    }, 600);
  };

  const controls = [
    { label: 'Altitude', key: 'altitude', unit: 'ft', min: 3000, max: 12000, step: 100 },
    { label: 'Ambient Temperature', key: 'ambientTemperature', unit: '°C', min: -10, max: 50, step: 1 },
    { label: 'Wind Speed', key: 'windSpeed', unit: 'm/s', min: 0, max: 40, step: 1 },
    { label: 'Mission Duration', key: 'durationHours', unit: 'h', min: 0.5, max: 8, step: 0.1 },
    { label: 'Throttle', key: 'throttle', unit: '%', min: 40, max: 100, step: 1 },
    { label: 'Engine Load', key: 'engineLoad', unit: '%', min: 40, max: 100, step: 1 },
    { label: 'Cooling Efficiency', key: 'coolingEfficiency', unit: '%', min: 60, max: 100, step: 1 },
    { label: 'Mechanical Health', key: 'mechanicalHealth', unit: '%', min: 70, max: 100, step: 1 },
  ];

  const metricOptions = ['RPM', 'CHT', 'EGT', 'Oil Temperature', 'Oil Pressure', 'Fuel Flow', 'Vibration', 'Engine Load'];

  const comparisonRows = [
    ['Altitude', `${BASELINE.altitude.toLocaleString()} ft`, `${scenario.altitude.toLocaleString()} ft`, `${formatDelta(scenario.altitude - BASELINE.altitude, ' ft')}`],
    ['Throttle', `${BASELINE.throttle}%`, `${scenario.throttle}%`, `${formatDelta(scenario.throttle - BASELINE.throttle, '%')}`],
    ['CHT', `${BASELINE.cht} °C`, `${Math.round(prediction.predictedCht)} °C`, `${formatDelta(Math.round(prediction.predictedCht - BASELINE.cht), ' °C')}`],
    ['EGT', `${BASELINE.egt} °C`, `${Math.round(prediction.predictedEgt)} °C`, `${formatDelta(Math.round(prediction.predictedEgt - BASELINE.egt), ' °C')}`],
    ['Fuel Flow', `${BASELINE.fuelFlow.toFixed(1)} L/h`, `${prediction.predictedFuelFlow.toFixed(1)} L/h`, `${formatDelta(prediction.predictedFuelFlow - BASELINE.fuelFlow, ' L/h')}`],
    ['Health', `${BASELINE.health}%`, `${Math.round(prediction.health)}%`, `${formatDelta(Math.round(prediction.health - BASELINE.health), '%')}`],
    ['RUL', `${BASELINE.rul} h`, `${Math.round(prediction.rul)} h`, `${formatDelta(Math.round(prediction.rul - BASELINE.rul), ' h')}`],
    ['Mission Risk', BASELINE.risk, prediction.riskLevel, prediction.riskLevel === BASELINE.risk ? '—' : '↑'],
  ];

  const simulationChartData = [
    { time: '0', baseline: 165, simulated: 168 },
    { time: '25m', baseline: 166, simulated: 170 },
    { time: '50m', baseline: 167, simulated: 173 },
    { time: '75m', baseline: 168, simulated: 176 },
    { time: '100m', baseline: 170, simulated: 179 },
    { time: '125m', baseline: 171, simulated: 182 },
    { time: '150m', baseline: 172, simulated: 186 },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="page-shell space-y-4">
        <header className="dashboard-header flex-col lg:flex-row">
          <div>
            <div className="dashboard-eyebrow">Simulation</div>
            <h2>Digital Twin what-if analysis and mission-condition evaluation</h2>
          </div>

          <div className="dashboard-status-row">
            <span className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 font-semibold text-emerald-700">SIMULATION READY</span>
            <span className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-slate-700">Digital Twin: SYNCHRONIZED</span>
            <span className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-slate-700">Model Version: v3.7</span>
            <span className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-slate-700">Data Quality: 98.7%</span>
            <span className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 font-mono text-slate-800">Last Update: {lastUpdated}</span>
          </div>
        </header>

        <section className="grid gap-3 xl:grid-cols-[1.1fr_0.9fr_0.9fr_0.9fr_0.9fr] rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Scenario</div>
            <div className="mt-2 flex items-center gap-2">
              <select
                value={activePreset}
                onChange={(event) => handlePreset(event.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-[11px] font-semibold text-slate-800 focus:outline-none"
              >
                {Object.keys(PRESETS).map((key) => (
                  <option key={key} value={key}>{key.replace(/_/g, ' ')}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Baseline</div>
            <div className="mt-2 text-sm font-bold text-slate-900">Current Engine State</div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Model</div>
            <div className="mt-2 text-sm font-bold text-slate-900">Hybrid Physics + AI</div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Simulation Horizon</div>
            <div className="mt-2 font-mono text-lg font-black text-slate-900">2.5 h</div>
          </div>

          <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 p-3">
            <button
              type="button"
              onClick={handleRunSimulation}
              className="flex-1 rounded-lg bg-blue-600 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.12em] text-white shadow-sm transition hover:bg-blue-700"
            >
              {simState === 'running' ? 'RUNNING' : 'RUN SIMULATION'}
            </button>
            <button
              type="button"
              onClick={handleReset}
              className="rounded-lg border border-slate-200 bg-white px-2.5 py-2 text-[11px] font-bold uppercase tracking-[0.12em] text-slate-700"
            >
              <RefreshCcw className="h-3.5 w-3.5" />
            </button>
          </div>
        </section>

        <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Scenario Parameters</div>
                <div className="mt-1 text-lg font-black tracking-tight text-slate-900">Mission and engine conditions</div>
              </div>
              <div className="rounded-full border border-slate-200 bg-slate-50 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-slate-600">Cruise</div>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              {controls.map((control) => (
                <div key={control.key} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="mb-2 flex items-center justify-between text-[11px] font-semibold text-slate-600">
                    <span>{control.label}</span>
                    <span className="font-mono font-bold text-slate-900">
                      {Number(scenario[control.key]).toFixed(control.key === 'durationHours' ? 1 : 0)} {control.unit}
                    </span>
                  </div>
                  <input
                    type="range"
                    min={control.min}
                    max={control.max}
                    step={control.step}
                    value={scenario[control.key]}
                    onChange={(event) => setScenario((current) => ({ ...current, [control.key]: Number(event.target.value) }))}
                    className="w-full accent-blue-600"
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Baseline State</div>
            <div className="space-y-2">
              {[
                ['RPM', `${baselineSummary.rpm.toLocaleString()} RPM`],
                ['CHT', `${baselineSummary.cht} °C`],
                ['EGT', `${baselineSummary.egt} °C`],
                ['Oil Temperature', `${baselineSummary.oilTemp} °C`],
                ['Fuel Flow', `${baselineSummary.fuelFlow.toFixed(1)} L/h`],
                ['Engine Health', `${baselineSummary.health}%`],
                ['RUL', `${baselineSummary.rul} h`],
                ['Mission Completion', `${baselineSummary.missionCompletion}%`],
              ].map(([label, value]) => (
                <div key={label} className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-2 text-[12px] text-slate-700">
                  <span className="font-medium text-slate-600">{label}</span>
                  <span className="font-mono font-bold text-slate-900">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Simulation Result</div>
                <div className="mt-1 text-lg font-black tracking-tight text-slate-900">Scenario: {activePreset.replace(/_/g, ' ')}</div>
              </div>
              <span
                className={`rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase ${
                  prediction.riskLevel === 'HIGH'
                    ? 'border-red-200 bg-red-50 text-red-700'
                    : prediction.riskLevel === 'MODERATE'
                      ? 'border-amber-200 bg-amber-50 text-amber-700'
                      : 'border-emerald-200 bg-emerald-50 text-emerald-700'
                }`}
              >
                {prediction.riskLevel}
              </span>
            </div>

            <div className="grid gap-3 md:grid-cols-4">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Mission completion</div>
                <div className="mt-2 font-mono text-[32px] font-black text-slate-900">{Math.round(prediction.missionCompletion)}%</div>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Engine health</div>
                <div className="mt-2 font-mono text-[32px] font-black text-slate-900">{Math.round(prediction.health)}%</div>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Predicted RUL</div>
                <div className="mt-2 font-mono text-[32px] font-black text-slate-900">{Math.round(prediction.rul)}h</div>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Confidence</div>
                <div className="mt-2 font-mono text-[32px] font-black text-slate-900">82%</div>
              </div>
            </div>

            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div className="text-[11px] font-semibold text-slate-600">Outcome</div>
                <div className="mt-2 text-lg font-black uppercase text-slate-900">{prediction.riskPhrase}</div>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div className="text-[11px] font-semibold text-slate-600">Mission risk</div>
                <div className="mt-2 text-lg font-black uppercase text-slate-900">{prediction.riskLevel}</div>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Predicted engine response</div>
            <div className="space-y-3">
              {[
                ['RPM', Math.round(prediction.predictedRpm), `${formatDelta(Math.round(prediction.predictedRpm - baselineSummary.rpm), '')}`],
                ['CHT', `${Math.round(prediction.predictedCht)} °C`, `${formatDelta(Math.round(prediction.predictedCht - BASELINE.cht), ' °C')}`],
                ['EGT', `${Math.round(prediction.predictedEgt)} °C`, `${formatDelta(Math.round(prediction.predictedEgt - BASELINE.egt), ' °C')}`],
                ['Oil Temperature', `${Math.round(prediction.predictedOilTemp)} °C`, `${formatDelta(Math.round(prediction.predictedOilTemp - BASELINE.oilTemp), ' °C')}`],
                ['Oil Pressure', `${prediction.predictedOilPressure.toFixed(1)} bar`, `${formatDelta(prediction.predictedOilPressure - BASELINE.oilPressure, ' bar')}`],
                ['Fuel Flow', `${prediction.predictedFuelFlow.toFixed(1)} L/h`, `${formatDelta(prediction.predictedFuelFlow - BASELINE.fuelFlow, ' L/h')}`],
                ['Vibration', `${prediction.predictedVibration.toFixed(2)} g`, `${formatDelta(prediction.predictedVibration - BASELINE.vibration, ' g')}`],
              ].map(([label, value, delta]) => (
                <div key={label} className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[12px] text-slate-700">
                  <span className="font-medium text-slate-600">{label}</span>
                  <span className="flex items-center gap-2">
                    <span className="font-mono font-bold text-slate-900">{value}</span>
                    <span className={`font-mono text-[10px] font-bold ${Number(delta.replace(/[^0-9.-]/g, '')) >= 0 ? 'text-amber-700' : 'text-emerald-700'}`}>
                      {delta}
                    </span>
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Simulated engine response</div>
                <div className="mt-1 text-lg font-black tracking-tight text-slate-900">Baseline vs scenario</div>
              </div>
              <div className="flex gap-2 text-[10px] font-bold uppercase tracking-[0.12em]">
                {metricOptions.map((metric) => (
                  <button
                    key={metric}
                    type="button"
                    onClick={() => setActiveMetric(metric)}
                    className={`rounded-lg border px-2 py-1 ${activeMetric === metric ? 'border-blue-200 bg-blue-50 text-blue-700' : 'border-slate-200 bg-slate-50 text-slate-600'}`}
                  >
                    {metric}
                  </button>
                ))}
              </div>
            </div>

            <div className="aero-chart h-62.5 w-full rounded-lg">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={simulationChartData}>
                  <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="time" tickLine={false} axisLine={false} tick={{ fill: '#64748b', fontSize: 11 }} />
                  <YAxis tickLine={false} axisLine={false} tick={{ fill: '#64748b', fontSize: 11 }} />
                  <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid #e2e8f0', background: '#fff' }} />
                  <Legend />
                  <Line type="monotone" dataKey="baseline" name="Baseline" stroke="#94a3b8" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="simulated" name="Simulation" stroke="#2563eb" strokeWidth={2.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Thermal response</div>
              <div className="space-y-3">
                <div className="flex items-center justify-between text-[12px] text-slate-700">
                  <span>Baseline CHT</span>
                  <span className="font-mono font-bold text-slate-900">{BASELINE.cht} °C</span>
                </div>
                <div className="flex items-center justify-between text-[12px] text-slate-700">
                  <span>Predicted CHT</span>
                  <span className="font-mono font-bold text-slate-900">{Math.round(prediction.predictedCht)} °C</span>
                </div>
                <div className="flex items-center justify-between text-[12px] text-slate-700">
                  <span>Max safe threshold</span>
                  <span className="font-mono font-bold text-slate-900">190 °C</span>
                </div>
                <div className="flex items-center justify-between text-[12px] text-slate-700">
                  <span>Remaining thermal margin</span>
                  <span className="font-mono font-bold text-amber-700">{Math.max(0, 190 - Math.round(prediction.predictedCht))} °C</span>
                </div>
                <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-slate-200">
                  <div
                    className="h-full rounded-full bg-amber-500"
                    style={{ width: `${Math.min((Math.round(prediction.predictedCht) / 190) * 100, 100)}%` }}
                  />
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Power & load response</div>
              <div className="space-y-2 text-[12px] text-slate-700">
                <div className="flex items-center justify-between"><span>Baseline load</span><span className="font-mono font-bold text-slate-900">{BASELINE.engineLoad}%</span></div>
                <div className="flex items-center justify-between"><span>Scenario load</span><span className="font-mono font-bold text-slate-900">{Math.round(prediction.predictedEngineLoad)}%</span></div>
                <div className="flex items-center justify-between"><span>Peak load</span><span className="font-mono font-bold text-slate-900">{Math.round(Math.min(prediction.predictedEngineLoad + 8, 95))}%</span></div>
                <div className="flex items-center justify-between"><span>Available margin</span><span className="font-mono font-bold text-amber-700">{Math.max(0, 100 - Math.round(prediction.predictedEngineLoad))}%</span></div>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Fuel consumption</div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Baseline</div>
                <div className="mt-2 font-mono text-3xl font-black text-slate-900">{BASELINE.fuelFlow.toFixed(1)}L/h</div>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Scenario</div>
                <div className="mt-2 font-mono text-3xl font-black text-slate-900">{prediction.predictedFuelFlow.toFixed(1)}L/h</div>
              </div>
            </div>
            <div className="mt-4 space-y-2 text-[12px] text-slate-700">
              <div className="flex items-center justify-between"><span>Estimated mission fuel</span><span className="font-mono font-bold text-slate-900">{(prediction.predictedFuelFlow * scenario.durationHours).toFixed(1)} L</span></div>
              <div className="flex items-center justify-between"><span>Reserve</span><span className="font-mono font-bold text-emerald-700">{(18 - prediction.predictedFuelFlow * scenario.durationHours).toFixed(1)} L</span></div>
              <div className="flex items-center justify-between"><span>Additional consumption</span><span className="font-mono font-bold text-amber-700">+{(prediction.predictedFuelFlow - BASELINE.fuelFlow).toFixed(1)} L/h</span></div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Engine health impact</div>
            <div className="space-y-3">
              <div className="flex items-center justify-between text-[12px] text-slate-700"><span>Baseline health</span><span className="font-mono font-bold text-slate-900">{BASELINE.health}%</span></div>
              <div className="flex items-center justify-between text-[12px] text-slate-700"><span>Simulation health</span><span className="font-mono font-bold text-slate-900">{Math.round(prediction.health)}%</span></div>
              <div className="flex items-center justify-between text-[12px] text-slate-700"><span>Change</span><span className="font-mono font-bold text-red-700">{formatDelta(Math.round(prediction.health - BASELINE.health), '%')}</span></div>
              <div className="space-y-2 pt-2">
                {Object.entries(prediction.componentHealth).map(([label, value]) => (
                  <div key={label}>
                    <div className="mb-1 flex items-center justify-between text-[11px] text-slate-600">
                      <span>{label}</span>
                      <span className="font-mono font-bold text-slate-900">{Math.round(value)}%</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                      <div className="h-full rounded-full bg-emerald-500" style={{ width: `${value}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Predicted degradation</div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Current degradation</div>
                <div className="mt-2 text-lg font-black text-slate-900">Low</div>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Scenario degradation</div>
                <div className="mt-2 text-lg font-black text-slate-900">Moderate</div>
              </div>
            </div>
            <div className="aero-chart mt-4 h-28 w-full rounded-lg">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={prediction.responseSeries}>
                  <defs>
                    <linearGradient id="degradationFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#60a5fa" stopOpacity={0.28} />
                      <stop offset="100%" stopColor="#60a5fa" stopOpacity={0.04} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="time" tickLine={false} axisLine={false} tick={{ fill: '#64748b', fontSize: 11 }} />
                  <YAxis tickLine={false} axisLine={false} tick={{ fill: '#64748b', fontSize: 11 }} />
                  <Area type="monotone" dataKey="baseline" stroke="#94a3b8" fill="none" strokeWidth={2} />
                  <Line type="monotone" dataKey="simulated" stroke="#2563eb" strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">RUL impact</div>
            <div className="space-y-3">
              <div className="flex items-center justify-between text-[12px] text-slate-700"><span>Baseline RUL</span><span className="font-mono font-bold text-slate-900">{BASELINE.rul} h</span></div>
              <div className="flex items-center justify-between text-[12px] text-slate-700"><span>Scenario RUL</span><span className="font-mono font-bold text-slate-900">{Math.round(prediction.rul)} h</span></div>
              <div className="flex items-center justify-between text-[12px] text-slate-700"><span>Difference</span><span className="font-mono font-bold text-red-700">{formatDelta(Math.round(prediction.rul - BASELINE.rul), ' h')}</span></div>
              <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div className="flex items-center justify-between text-[11px] text-slate-600">
                  <span>Prediction interval</span>
                  <span className="font-mono font-bold text-slate-900">128–145 h</span>
                </div>
                <div className="mt-3 flex items-center justify-between text-[11px] text-slate-600">
                  <span>Confidence</span>
                  <span className="font-mono font-bold text-slate-900">82%</span>
                </div>
                <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-200">
                  <div className="h-full rounded-full bg-blue-500" style={{ width: '82%' }} />
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Mission outcome</div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Baseline completion</div>
                <div className="mt-2 font-mono text-3xl font-black text-slate-900">{BASELINE.missionCompletion}%</div>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Scenario completion</div>
                <div className="mt-2 font-mono text-3xl font-black text-slate-900">{Math.round(prediction.missionCompletion)}%</div>
              </div>
            </div>
            <div className="mt-4 space-y-2 text-[12px] text-slate-700">
              <div className="flex items-center justify-between"><span>Change</span><span className="font-mono font-bold text-red-700">{formatDelta(Math.round(prediction.missionCompletion - BASELINE.missionCompletion), ' pts')}</span></div>
              <div className="flex items-center justify-between"><span>Primary driver</span><span className="font-bold text-slate-900">Increased thermal stress</span></div>
              <div className="flex items-center justify-between"><span>Secondary driver</span><span className="font-bold text-slate-900">Higher sustained load</span></div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Risk change</div>
            <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 p-3">
              <span className="font-medium text-slate-600">Baseline</span>
              <span className="font-mono font-bold text-emerald-700">LOW</span>
            </div>
            <div className="my-2 flex justify-center text-slate-400"><ArrowRight className="h-4 w-4" /></div>
            <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 p-3">
              <span className="font-medium text-slate-600">Simulation</span>
              <span className="font-mono font-bold text-amber-700">{prediction.riskLevel}</span>
            </div>
            <div className="mt-4 space-y-2">
              {prediction.riskContributors.map((item) => (
                <div key={item.label}>
                  <div className="mb-1 flex items-center justify-between text-[11px] text-slate-600">
                    <span>{item.label}</span>
                    <span className="font-mono font-bold text-slate-900">{Math.round(item.value)}%</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                    <div className="h-full rounded-full bg-blue-500" style={{ width: `${Math.min(item.value, 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="grid gap-4 xl:grid-cols-[1fr_1fr]">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Parameter sensitivity</div>
            <div className="space-y-3">
              {prediction.sensitivity.map((item) => (
                <div key={item.label}>
                  <div className="mb-1 flex items-center justify-between text-[11px] text-slate-600">
                    <span>{item.label}</span>
                    <span className="font-bold text-slate-900">{item.level}</span>
                  </div>
                  <div className="h-2.5 overflow-hidden rounded-full bg-slate-200">
                    <div className="h-full rounded-full bg-blue-500" style={{ width: `${item.value}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Simulation interpretation</div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-[13px] leading-6 text-slate-700">
              {prediction.interpretation}
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => onNavigate && onNavigate('mission')}
                className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.12em] text-slate-700"
              >
                View Mission Impact <ChevronRight className="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                onClick={() => onNavigate && onNavigate('diagnostics')}
                className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.12em] text-slate-700"
              >
                View Diagnostics <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </section>

        <section className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Scenario comparison</div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-[12px]">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500">
                    <th className="pb-2 pr-4">Parameter</th>
                    <th className="pb-2 pr-4">Baseline</th>
                    <th className="pb-2 pr-4">Scenario</th>
                    <th className="pb-2">Δ</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonRows.map(([label, baselineValue, simValue, delta]) => (
                    <tr key={label} className="border-b border-slate-100 text-slate-700">
                      <td className="py-2 pr-4 font-medium">{label}</td>
                      <td className="py-2 pr-4 font-mono font-bold">{baselineValue}</td>
                      <td className="py-2 pr-4 font-mono font-bold">{simValue}</td>
                      <td className="py-2 font-mono font-bold text-slate-900">{delta}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Recommended action</div>
                <div className="mt-1 text-lg font-black tracking-tight text-slate-900">Operational guidance</div>
              </div>
              <span
                className={`rounded-full border px-2 py-1 text-[10px] font-bold uppercase ${
                  prediction.riskLevel === 'HIGH'
                    ? 'border-red-200 bg-red-50 text-red-700'
                    : prediction.riskLevel === 'MODERATE'
                      ? 'border-amber-200 bg-amber-50 text-amber-700'
                      : 'border-emerald-200 bg-emerald-50 text-emerald-700'
                }`}
              >
                {prediction.riskLevel === 'HIGH' ? 'RESTRICT' : prediction.riskLevel === 'MODERATE' ? 'MONITOR' : 'CONTINUE'}
              </span>
            </div>
            <div className="space-y-3 text-[13px] text-slate-700">
              <div><span className="font-semibold text-slate-900">Reason:</span> Scenario produces reduced thermal margin and increased predicted degradation.</div>
              <div><span className="font-semibold text-slate-900">Recommendation:</span> Avoid prolonged operation at this load profile and review cooling efficiency before continuing the mission.</div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => onNavigate && onNavigate('mission')}
                className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.12em] text-slate-700"
              >
                View Mission Impact <ChevronRight className="h-3.5 w-3.5" />
              </button>
              <button type="button" className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.12em] text-slate-700">
                <Download className="h-3.5 w-3.5" /> Save Scenario
              </button>
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Simulation history</div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-[12px]">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500">
                  <th className="pb-2 pr-4">Time</th>
                  <th className="pb-2 pr-4">Scenario</th>
                  <th className="pb-2 pr-4">Changed Parameters</th>
                  <th className="pb-2 pr-4">Health Impact</th>
                  <th className="pb-2 pr-4">RUL Impact</th>
                  <th className="pb-2 pr-4">Risk</th>
                  <th className="pb-2">Result</th>
                </tr>
              </thead>
              <tbody>
                {SCENARIO_HISTORY.map((item) => (
                  <tr key={`${item.time}-${item.scenario}`} className="border-b border-slate-100 text-slate-700">
                    <td className="py-2 pr-4 font-mono font-bold">{item.time}</td>
                    <td className="py-2 pr-4 font-semibold">{item.scenario}</td>
                    <td className="py-2 pr-4">{item.changed}</td>
                    <td className="py-2 pr-4 font-mono">{item.health}</td>
                    <td className="py-2 pr-4 font-mono">{item.rul}</td>
                    <td className="py-2 pr-4 font-bold uppercase text-slate-900">{item.risk}</td>
                    <td className="py-2 font-bold text-slate-900">{item.result}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}
