import React, { useMemo, useState } from 'react';
import GaugeDonut from '../components/GaugeDonut';
import {
  Activity,
  ArrowRight,
  ChevronRight,
  Compass,
  Gauge,
  Play,
  ShieldAlert,
  Thermometer,
  Wind,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const phaseData = [
  { name: 'Takeoff', duration: '00:08', load: 91, peak: 95, thermal: 'HIGH', healthImpact: '-2%', status: 'normal' },
  { name: 'Climb', duration: '00:22', load: 84, peak: 89, thermal: 'MODERATE', healthImpact: '-1%', status: 'normal' },
  { name: 'Cruise', duration: '01:34', load: 72, peak: 82, thermal: 'LOW', healthImpact: '0%', status: 'watch' },
  { name: 'Loiter', duration: '00:46', load: 68, peak: 73, thermal: 'LOW', healthImpact: '0%', status: 'normal' },
  { name: 'Descent', duration: '00:18', load: 61, peak: 66, thermal: 'LOW', healthImpact: '+1%', status: 'normal' },
  { name: 'Landing', duration: '00:09', load: 56, peak: 60, thermal: 'LOW', healthImpact: '+2%', status: 'normal' },
];

const capabilityBars = [
  { label: 'Thermal Capacity', value: 92, delta: '18 °C', tone: 'amber' },
  { label: 'Power Margin', value: 18, delta: '18%', tone: 'blue' },
  { label: 'Fuel Margin', value: 24, delta: '24%', tone: 'emerald' },
  { label: 'Mechanical Margin', value: 14, delta: '14%', tone: 'amber' },
  { label: 'Lubrication Margin', value: 31, delta: '31%', tone: 'emerald' },
  { label: 'Overall Mission Margin', value: 18, delta: '18%', tone: 'blue' },
];

const riskContributors = [
  { rank: '01', title: 'Thermal Stress', value: 42 },
  { rank: '02', title: 'Mechanical Degradation', value: 24 },
  { rank: '03', title: 'High Engine Load', value: 18 },
  { rank: '04', title: 'Ambient Temperature', value: 10 },
  { rank: '05', title: 'Telemetry Uncertainty', value: 6 },
];

const missionDemandSeries = [
  { time: '00:00', capability: 100, demand: 48, margin: 52 },
  { time: '00:30', capability: 95, demand: 60, margin: 35 },
  { time: '01:00', capability: 90, demand: 70, margin: 20 },
  { time: '01:30', capability: 87, demand: 76, margin: 11 },
  { time: '02:00', capability: 84, demand: 80, margin: 4 },
  { time: '02:30', capability: 81, demand: 78, margin: 3 },
];

const thermalTrend = [
  { time: '00:00', cht: 158 },
  { time: '00:15', cht: 162 },
  { time: '00:30', cht: 165 },
  { time: '00:45', cht: 168 },
  { time: '01:00', cht: 170 },
  { time: '01:15', cht: 173 },
  { time: '01:30', cht: 172 },
];

function assessMissionState({ engineHealth, completionProbability, thermalMargin, missionRemainingHours, rulHours, faultProbability, load, uncertainty }) {
  if (completionProbability >= 90 && engineHealth >= 93 && thermalMargin >= 20 && rulHours >= missionRemainingHours * 20 && faultProbability < 0.25) {
    return { status: 'READY', tone: 'emerald', reason: 'Current engine condition supports continued mission operation within expected thermal and load envelopes.' };
  }
  if (completionProbability >= 75 || thermalMargin >= 10 || faultProbability >= 0.35 || load >= 80) {
    return { status: 'MONITOR', tone: 'amber', reason: 'Thermal margin is narrowing and sustained high-load operation should be monitored closely.' };
  }
  if (completionProbability >= 55 || thermalMargin < 10 || rulHours < missionRemainingHours * 10 || uncertainty > 0.25) {
    return { status: 'RESTRICTED', tone: 'orange', reason: 'Operating margin is reduced and mission continuity requires caution and active monitoring.' };
  }
  return { status: 'RETURN TO BASE', tone: 'red', reason: 'Engine capability and mission demand are no longer aligned with a safe completion margin.' };
}

function statusClassMap(tone) {
  const map = {
    emerald: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    amber: 'border-amber-200 bg-amber-50 text-amber-700',
    orange: 'border-orange-200 bg-orange-50 text-orange-700',
    red: 'border-red-200 bg-red-50 text-red-700',
    blue: 'border-blue-200 bg-blue-50 text-blue-700',
  };
  return map[tone] || map.blue;
}

export default function MissionView({ onNavigate }) {
  const [activePhase, setActivePhase] = useState('Cruise');

  const missionAssessment = useMemo(
    () =>
      assessMissionState({
        engineHealth: 94,
        completionProbability: 87,
        thermalMargin: 18,
        missionRemainingHours: 2.3,
        rulHours: 143,
        faultProbability: 0.82,
        load: 78,
        uncertainty: 0.18,
      }),
    []
  );

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="page-shell space-y-5">
        <header className="dashboard-header flex-col lg:flex-row">
          <div>
            <div className="dashboard-eyebrow">Mission</div>
            <h2>Mission reliability, operational condition and completion assessment</h2>
          </div>

          <div className="dashboard-status-row">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 font-semibold text-emerald-700">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              LIVE
            </span>
            <span className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 font-semibold text-slate-700">Digital Twin: SYNCHRONIZED</span>
            <span className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 font-semibold text-slate-700">Data Quality: 98.7%</span>
            <span className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 font-mono font-bold text-slate-800">Last Update: 21:14:32</span>
          </div>
        </header>

        <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
          <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
            <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Mission ID</div>
            <div className="mt-2 text-lg font-black text-slate-900">UAV-2026-045</div>
            <div className="text-[11px] text-slate-500">Surveillance</div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
            <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Mission Status</div>
            <div className={`mt-2 inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase ${statusClassMap(missionAssessment.tone)}`}>
              <Play className="h-3 w-3 fill-current" />
              {missionAssessment.status}
            </div>
            <div className="mt-2 text-[11px] text-slate-500">Current phase: Cruise</div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
            <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Remaining Mission</div>
            <div className="mt-2 font-mono text-xl font-black text-slate-900">02:18:37</div>
            <div className="text-[11px] text-slate-500">62% mission time remains</div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
            <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Engine Health</div>
            <div className="mt-2 text-2xl font-black text-slate-900">94%</div>
            <div className="text-[11px] text-emerald-700">Healthy</div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
            <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Thermal Margin</div>
            <div className="mt-2 font-mono text-xl font-black text-slate-900">+18 °C</div>
            <div className="text-[11px] text-amber-700">Trending up</div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
            <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Mission Completion</div>
            <div className="mt-2 text-2xl font-black text-slate-900">87%</div>
            <div className="text-[11px] text-blue-700">Likely to complete</div>
          </div>
        </section>

        <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-4 flex items-center justify-between gap-4">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Mission Status</div>
                <div className="mt-1 text-lg font-black tracking-tight text-slate-900">Operational assessment</div>
              </div>
              <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase ${statusClassMap(missionAssessment.tone)}`}>
                <ShieldAlert className="h-3.5 w-3.5" />
                {missionAssessment.status}
              </span>
            </div>

            <div className="grid gap-4 md:grid-cols-[0.95fr_1.05fr] md:items-center">
              <div className="flex justify-center">
                <GaugeDonut value={87} color="#3b82f6" size={120} strokeWidth={10} label="Mission completion" />
              </div>

              <div className="space-y-3">
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Confidence</span>
                    <span className="font-mono text-sm font-black text-slate-900">89%</span>
                  </div>
                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-200">
                    <div className="h-full rounded-full bg-blue-500" style={{ width: '89%' }} />
                  </div>
                </div>

                <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Current engine condition</div>
                  <div className="mt-1 text-sm leading-6 text-slate-700">{missionAssessment.reason}</div>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Mission Conditions</div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-2.5">
                <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">
                  <Compass className="h-3.5 w-3.5 text-sky-500" />
                  Altitude
                </div>
                <div className="mt-1 font-mono text-lg font-black text-slate-900">5,200 ft</div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-2.5">
                <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">
                  <Gauge className="h-3.5 w-3.5 text-violet-500" />
                  Airspeed
                </div>
                <div className="mt-1 font-mono text-lg font-black text-slate-900">34 m/s</div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-2.5">
                <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">
                  <Thermometer className="h-3.5 w-3.5 text-amber-500" />
                  Ambient Temp
                </div>
                <div className="mt-1 font-mono text-lg font-black text-slate-900">28 °C</div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-2.5">
                <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">
                  <Wind className="h-3.5 w-3.5 text-blue-500" />
                  Wind
                </div>
                <div className="mt-1 font-mono text-lg font-black text-slate-900">12 m/s</div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-2.5">
                <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">
                  <Gauge className="h-3.5 w-3.5 text-sky-500" />
                  Air Density
                </div>
                <div className="mt-1 font-mono text-lg font-black text-slate-900">0.84 kg/m³</div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-2.5">
                <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">
                  <Activity className="h-3.5 w-3.5 text-emerald-500" />
                  Engine Load
                </div>
                <div className="mt-1 font-mono text-lg font-black text-slate-900">78%</div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-2.5">
                <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Throttle</div>
                <div className="mt-1 font-mono text-lg font-black text-slate-900">82%</div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-2.5">
                <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Flight Phase</div>
                <div className="mt-1 text-lg font-black uppercase text-slate-900">Cruise</div>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Engine → Mission Capability</div>
            <div className="space-y-3">
              {capabilityBars.map((item) => (
                <div key={item.label} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <span className="text-[11px] font-bold uppercase tracking-[0.12em] text-slate-600">{item.label}</span>
                    <span className="font-mono text-[11px] font-bold text-slate-800">{item.delta}</span>
                  </div>
                  <div className="h-2.5 overflow-hidden rounded-full bg-slate-200">
                    <div
                      className={`h-full rounded-full ${
                        item.tone === 'amber'
                          ? 'bg-amber-500'
                          : item.tone === 'emerald'
                            ? 'bg-emerald-500'
                            : 'bg-blue-500'
                      }`}
                      style={{ width: `${Math.min(item.value, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Mission Risk Assessment</div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Mission completion probability</div>
                <div className="mt-2 text-4xl font-black tracking-tight text-slate-900">87%</div>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Risk Level</div>
                <div className="mt-2 inline-flex rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-[10px] font-bold uppercase text-amber-700">MODERATE</div>
              </div>
            </div>

            <div className="mt-4 space-y-2">
              <div className="flex items-center justify-between text-[11px] text-slate-600">
                <span>Risk trend</span>
                <span className="font-bold text-amber-700">↑ Increasing</span>
              </div>
              <div className="flex items-center justify-between text-[11px] text-slate-600">
                <span>Primary risk</span>
                <span className="font-bold text-slate-800">Rising CHT</span>
              </div>
              <div className="flex items-center justify-between text-[11px] text-slate-600">
                <span>Secondary risk</span>
                <span className="font-bold text-slate-800">Mechanical vibration</span>
              </div>
            </div>

            <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3">
              <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Risk contributors</div>
              <div className="space-y-2.5">
                {riskContributors.map((item) => (
                  <div key={item.rank}>
                    <div className="mb-1 flex items-center justify-between text-[11px] text-slate-700">
                      <span className="font-bold text-slate-800">{item.rank}</span>
                      <span className="font-semibold">{item.title}</span>
                      <span className="font-mono font-bold text-slate-900">{item.value}%</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                      <div className="h-full rounded-full bg-blue-500" style={{ width: `${item.value}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Engine health vs mission demand</div>
            <div className="aero-chart h-64 w-full rounded-lg">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={missionDemandSeries}>
                  <defs>
                    <linearGradient id="capabilityFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="time" tickLine={false} axisLine={false} tick={{ fill: '#64748b', fontSize: 11 }} />
                  <YAxis tickLine={false} axisLine={false} tick={{ fill: '#64748b', fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 11 }} />
                  <Area type="monotone" dataKey="capability" stroke="#3b82f6" fill="none" strokeWidth={2} />
                  <Line type="monotone" dataKey="demand" stroke="#0f172a" strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Thermal Margin</div>
            <div className="grid gap-2 sm:grid-cols-2">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Current CHT</div>
                <div className="mt-1 font-mono text-3xl font-black text-slate-900">172 °C</div>
              </div>
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Expected CHT</div>
                <div className="mt-1 font-mono text-3xl font-black text-slate-900">165 °C</div>
              </div>
            </div>
            <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3">
              <div className="flex items-center justify-between text-[11px] text-slate-600">
                <span>Maximum safe threshold</span>
                <span className="font-mono font-bold text-slate-900">190 °C</span>
              </div>
              <div className="mt-2 flex items-center justify-between text-[11px] text-slate-600">
                <span>Remaining margin</span>
                <span className="font-mono font-bold text-amber-700">18 °C</span>
              </div>
              <div className="mt-3 h-2.5 overflow-hidden rounded-full bg-slate-200">
                <div className="h-full rounded-full bg-amber-500" style={{ width: '71%' }} />
              </div>
            </div>
            <div className="aero-chart mt-4 h-24 w-full rounded-lg">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={thermalTrend}>
                  <defs>
                    <linearGradient id="thermalFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.25} />
                      <stop offset="100%" stopColor="#f59e0b" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <Area type="monotone" dataKey="cht" stroke="#f59e0b" fill="none" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Mission Phase Performance</div>
                <div className="mt-1 text-lg font-black tracking-tight text-slate-900">Operational timeline</div>
              </div>
              <button type="button" onClick={() => setActivePhase('Cruise')} className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-slate-700">Current: Cruise</button>
            </div>

            <div className="mb-4 flex gap-2 overflow-x-auto pb-1">
              {phaseData.map((phase) => (
                <button
                  key={phase.name}
                  type="button"
                  onClick={() => setActivePhase(phase.name)}
                  className={`min-w-22.5 rounded-lg border px-2 py-1.5 text-left text-[10px] font-bold uppercase ${activePhase === phase.name ? 'border-blue-200 bg-blue-50 text-blue-700' : 'border-slate-200 bg-slate-50 text-slate-600'}`}
                >
                  {phase.name}
                </button>
              ))}
            </div>

            <div className="space-y-3">
              {phaseData.map((phase) => (
                <div key={phase.name} className={`rounded-xl border p-3 ${activePhase === phase.name ? 'border-blue-200 bg-blue-50/60' : 'border-slate-200 bg-slate-50'}`}>
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <span className="text-sm font-black text-slate-900">{phase.name}</span>
                    <span className="font-mono text-[11px] font-bold text-slate-700">{phase.duration}</span>
                  </div>
                  <div className="grid gap-2 sm:grid-cols-3 text-[11px] text-slate-600">
                    <div><span className="font-semibold text-slate-500">Load</span><div className="mt-1 font-mono font-bold text-slate-900">{phase.load}%</div></div>
                    <div><span className="font-semibold text-slate-500">Peak</span><div className="mt-1 font-mono font-bold text-slate-900">{phase.peak}%</div></div>
                    <div><span className="font-semibold text-slate-500">Thermal</span><div className="mt-1 font-bold text-slate-900">{phase.thermal}</div></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Power & Load Margin</div>
              <div className="space-y-3">
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="flex items-center justify-between text-[11px] text-slate-600">
                    <span>Current load</span>
                    <span className="font-mono font-bold text-slate-900">78%</span>
                  </div>
                  <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-slate-200">
                    <div className="h-full rounded-full bg-blue-500" style={{ width: '78%' }} />
                  </div>
                </div>

                <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="flex items-center justify-between text-[11px] text-slate-600">
                    <span>Recommended max sustained</span>
                    <span className="font-mono font-bold text-slate-900">82%</span>
                  </div>
                  <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-slate-200">
                    <div className="h-full rounded-full bg-amber-500" style={{ width: '82%' }} />
                  </div>
                </div>
                <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[11px] text-amber-800">Available margin is 4% before recommended sustained load threshold.</div>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Fuel Margin</div>
              <div className="grid gap-2 text-[11px] text-slate-600">
                <div className="flex items-center justify-between"><span>Fuel remaining</span><span className="font-mono font-bold text-slate-900">15.8 L</span></div>
                <div className="flex items-center justify-between"><span>Estimated required</span><span className="font-mono font-bold text-slate-900">7.2 L</span></div>
                <div className="flex items-center justify-between"><span>Reserve</span><span className="font-mono font-bold text-emerald-700">8.6 L</span></div>
                <div className="flex items-center justify-between"><span>Endurance</span><span className="font-mono font-bold text-slate-900">05:40 h</span></div>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">RUL vs Mission Requirement</div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Estimated RUL</div>
                <div className="mt-1 text-3xl font-black text-slate-900">143 h</div>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Required mission time</div>
                <div className="mt-1 text-3xl font-black text-slate-900">2.3 h</div>
              </div>
            </div>
            <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3">
              <div className="flex items-center justify-between text-[11px] text-slate-600">
                <span>RUL / Mission ratio</span>
                <span className="font-mono font-bold text-slate-900">62×</span>
              </div>
              <div className="mt-2 flex items-center justify-between text-[11px] text-slate-600">
                <span>Prediction confidence</span>
                <span className="font-mono font-bold text-slate-900">82%</span>
              </div>
              <div className="mt-2 inline-flex rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[10px] font-bold uppercase text-emerald-700">SUFFICIENT</div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Mission Confidence</div>
            <div className="space-y-3">
              <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 p-3 text-[11px] text-slate-600">
                <span>Completion probability</span>
                <span className="font-mono font-bold text-slate-900">87%</span>
              </div>
              <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 p-3 text-[11px] text-slate-600">
                <span>Prediction confidence</span>
                <span className="font-mono font-bold text-slate-900">82%</span>
              </div>
              <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 p-3 text-[11px] text-slate-600">
                <span>Telemetry confidence</span>
                <span className="font-mono font-bold text-slate-900">96%</span>
              </div>
              <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 p-3 text-[11px] text-slate-600">
                <span>Risk confidence</span>
                <span className="font-mono font-bold text-slate-900">84%</span>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Recommended Action</div>
            <div className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase ${statusClassMap(missionAssessment.tone)}`}>MONITOR</div>
            <div className="mt-3 space-y-2 text-sm text-slate-600">
              <div><span className="font-semibold text-slate-800">Reason:</span> Engine thermal margin is decreasing during sustained high-load operation.</div>
              <div><span className="font-semibold text-slate-800">Recommended:</span> Maintain moderate engine load, avoid prolonged high throttle, continue monitoring CHT and EGT, review cooling performance after mission.</div>
            </div>
            <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3">
              <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Priority</div>
              <div className="mt-1 text-lg font-black tracking-tight text-slate-900">MEDIUM</div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <button type="button" onClick={() => onNavigate && onNavigate('diagnostics')} className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.12em] text-slate-700">View Diagnostics <ChevronRight className="h-3.5 w-3.5" /></button>
              <button type="button" onClick={() => onNavigate && onNavigate('simulation')} className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.12em] text-slate-700">Run What-If <ArrowRight className="h-3.5 w-3.5" /></button>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Mission Event Log</div>
                <div className="mt-1 text-lg font-black tracking-tight text-slate-900">Recent operational changes</div>
              </div>
              <button type="button" className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-slate-700">Timeline</button>
            </div>

            <div className="space-y-3">
              {[
                { time: '21:14:32', title: 'CHT deviation detected', status: 'warning' },
                { time: '21:11:08', title: 'EGT deviation', status: 'watch' },
                { time: '20:52:41', title: 'Vibration spike', status: 'warning' },
                { time: '20:47:09', title: 'Fuel flow variation', status: 'normal' },
              ].map((event) => (
                <div key={`${event.time}-${event.title}`} className="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-2.5">
                  <div className="mt-0.5 flex h-7 w-7 items-center justify-center rounded-full border border-slate-200 bg-white text-[10px] font-bold text-slate-700">{event.time.split(':')[0]}</div>
                  <div className="min-w-0 flex-1">
                    <div className="font-mono text-[11px] font-bold text-slate-500">{event.time}</div>
                    <div className="text-sm font-semibold text-slate-800">{event.title}</div>
                  </div>
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${event.status === 'warning' ? 'bg-amber-100 text-amber-700' : event.status === 'watch' ? 'bg-blue-100 text-blue-700' : 'bg-emerald-100 text-emerald-700'}`}>
                    {event.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}