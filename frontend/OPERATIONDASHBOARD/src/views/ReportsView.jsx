import React, { useMemo, useState } from 'react';
import {
  ChevronRight,
  Download,
  FileText,
  Search,
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
import {
  COMPONENT_HEALTH,
  LIVE_DATA_TABLE,
  TELEMETRY_TRENDS_DATA,
} from '../mockData';

const REPORTS = [
  { id: 'mission-027', type: 'Mission Report', mission: '#027', date: '08 Sep 2026', status: 'Completed', health: 91, risk: 'Moderate', faults: 3 },
  { id: 'diagnostic-027', type: 'Diagnostic Report', mission: '#027', date: '08 Sep 2026', status: 'Completed', health: 91, risk: 'Moderate', faults: 1 },
  { id: 'simulation-027', type: 'Simulation Report', mission: '#027', date: '08 Sep 2026', status: 'Completed', health: 91, risk: 'Moderate', faults: '-' },
];

const TIMELINE = [
  ['18:42', 'Mission started', 'normal'],
  ['18:51', 'Takeoff', 'normal'],
  ['19:14', 'Climb', 'normal'],
  ['20:03', 'Cruise', 'normal'],
  ['21:41', 'CHT deviation detected', 'warning'],
  ['21:42', 'Cooling degradation classified', 'warning'],
  ['21:44', 'Mission risk increased', 'warning'],
  ['22:17', 'Risk stabilized', 'normal'],
  ['23:17', 'Mission completed', 'normal'],
];

const PARAMETER_META = {
  rpm: { label: 'RPM', unit: 'RPM', key: 'rpm', expected: 5092 },
  cht: { label: 'CHT', unit: '°C', key: 'cht', expected: 165 },
  egt: { label: 'EGT', unit: '°C', key: 'egt', expected: 640 },
  oilPressure: { label: 'Oil Pressure', unit: 'bar', key: 'oilP', expected: 4.3 },
  oilTemp: { label: 'Oil Temperature', unit: '°C', key: 'oilT', expected: 90 },
  fuelFlow: { label: 'Fuel Flow', unit: 'L/h', key: 'fuel', expected: 3.2 },
  vibration: { label: 'Vibration', unit: 'mm/s', key: 'vib', expected: 1.2 },
  engineLoad: { label: 'Engine Load', unit: '%', key: 'load', expected: 70 },
};

const EVENT_ROWS = [
  { time: '02:41:18', event: 'CHT deviation', component: 'Cooling', severity: 'Warning', probability: 82, confidence: 89, status: 'Resolved', impact: 'Moderate' },
  { time: '02:52:04', event: 'Vibration increase', component: 'Mechanical', severity: 'Warning', probability: 64, confidence: 79, status: 'Resolved', impact: 'Low' },
  { time: '03:10:22', event: 'CHT above threshold', component: 'Cylinder 3', severity: 'Critical', probability: 92, confidence: 94, status: 'Active', impact: 'High' },
];

function average(values) {
  return values.reduce((sum, value) => sum + Number(value || 0), 0) / values.length;
}

function fixed(value, digits = 0) {
  return Number(value).toFixed(digits);
}

function statusTone(status) {
  if (['Critical', 'High'].includes(status)) return 'border-red-200 bg-red-50 text-red-700';
  if (['Warning', 'Moderate', 'Active'].includes(status)) return 'border-amber-200 bg-amber-50 text-amber-700';
  return 'border-emerald-200 bg-emerald-50 text-emerald-700';
}

function Section({ title, eyebrow, children, className = '' }) {
  return (
    <section className={`ui-card ${className}`}>
      <div className="mb-3 flex items-center justify-between border-b border-slate-100 pb-3">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">{eyebrow}</div>
          <h3 className="mt-1 text-sm font-semibold text-slate-900">{title}</h3>
        </div>
      </div>
      {children}
    </section>
  );
}

function Badge({ children }) {
  return <span className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase ${statusTone(children)}`}>{children}</span>;
}

export default function ReportsView({ onNavigate }) {
  const [reportType, setReportType] = useState('Mission Report');
  const [severity, setSeverity] = useState('All');
  const [eventStatus, setEventStatus] = useState('All');
  const [component, setComponent] = useState('All');
  const [query, setQuery] = useState('');
  const [metric, setMetric] = useState('cht');
  const [generationState, setGenerationState] = useState('idle');
  const [exporting, setExporting] = useState(null);

  const currentReport = REPORTS.find((report) => report.type === reportType) || REPORTS[0];
  const latest = LIVE_DATA_TABLE[0];
  const health = 91;
  const rul = 136;

  const filteredEvents = useMemo(
    () =>
      EVENT_ROWS.filter((event) => severity === 'All' || event.severity === severity)
        .filter((event) => eventStatus === 'All' || event.status === eventStatus)
        .filter((event) => component === 'All' || event.component === component)
        .filter((event) => `${event.event} ${event.component} ${event.time}`.toLowerCase().includes(query.toLowerCase())),
    [component, eventStatus, query, severity],
  );

  const telemetryRows = Object.entries(PARAMETER_META).map(([id, meta]) => {
    const values = LIVE_DATA_TABLE.map((row) => row[meta.key]);
    const final = latest[meta.key];
    const min = Math.min(...values);
    const max = Math.max(...values);
    const avg = average(values);
    const warning = id === 'cht' || id === 'vibration';
    return { id, ...meta, avg, min, max, final, status: warning ? 'Warning' : 'Valid' };
  });

  const chartData = TELEMETRY_TRENDS_DATA.map((point, index) => {
    const key = PARAMETER_META[metric].key;
    const livePoint = LIVE_DATA_TABLE[LIVE_DATA_TABLE.length - 1 - index] || LIVE_DATA_TABLE[0];
    return {
      time: point.time,
      value: point[key] ?? livePoint[key],
    };
  });

  const reportPayload = {
    report: currentReport,
    summary: { engineHealthInitial: 94, engineHealthFinal: health, missionRisk: 'MODERATE', completionProbability: 87, faultEvents: filteredEvents.length },
    telemetry: telemetryRows,
    diagnostics: filteredEvents,
    rul: { estimateHours: rul, lowerBound: 128, upperBound: 145, confidence: 82 },
    recommendation: 'Inspect cooling performance, monitor CHT and EGT, and avoid prolonged high-load operation until inspection.',
  };

  const generateReport = () => {
    setGenerationState('generating');
    window.setTimeout(() => setGenerationState('ready'), 500);
  };

  const exportReport = (format) => {
    if (format === 'PDF') return;
    setExporting(format);
    const content = format === 'JSON'
      ? JSON.stringify(reportPayload, null, 2)
      : ['Parameter,Average,Minimum,Maximum,Final,Status', ...telemetryRows.map((row) => `${row.label},${fixed(row.avg, 2)},${row.min},${row.max},${row.final},${row.status}`)].join('\n');
    const blob = new Blob([content], { type: format === 'JSON' ? 'application/json' : 'text/csv' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${currentReport.id}.${format.toLowerCase()}`;
    link.click();
    URL.revokeObjectURL(link.href);
    window.setTimeout(() => setExporting(null), 500);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="page-shell space-y-4">
        <header className="dashboard-header flex-col lg:flex-row">
          <div>
            <div className="dashboard-eyebrow">Reports</div>
            <h2>Mission records, diagnostic history and Digital Twin analysis</h2>
          </div>
          <div className="dashboard-status-row">
            <span className="rounded-lg border border-emerald-200 bg-emerald-50 px-2.5 py-1.5 font-bold text-emerald-700">DATA STATUS</span>
            <span className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-slate-700">Digital Twin: SYNCHRONIZED</span>
            <span className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-slate-700">Data Quality: 98.7%</span>
            <button type="button" onClick={generateReport} className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-2 text-[11px] font-bold uppercase text-white hover:bg-blue-700">
              <FileText className="h-3.5 w-3.5" /> {generationState === 'generating' ? 'Generating...' : generationState === 'ready' ? 'Report Ready' : 'Generate Report'}
            </button>
          </div>
        </header>

        <section className="grid gap-3 rounded-xl border border-slate-200 bg-white p-3 shadow-sm md:grid-cols-2 lg:grid-cols-6">
          <select value={reportType} onChange={(event) => setReportType(event.target.value)} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-800">
            {['Mission Report', 'Diagnostic Report', 'Engine Health Report', 'Simulation Report'].map((item) => <option key={item}>{item}</option>)}
          </select>
          <select className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-800"><option>Mission #027</option></select>
          <select className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-800"><option>08 Sep 2026</option></select>
          <select value={severity} onChange={(event) => setSeverity(event.target.value)} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-800"><option>All</option><option>Warning</option><option>Critical</option></select>
          <select value={eventStatus} onChange={(event) => setEventStatus(event.target.value)} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-800"><option>All</option><option>Resolved</option><option>Active</option></select>
          <div className="relative"><Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search reports, events or components..." className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-8 pr-2 text-xs outline-none focus:border-blue-400" /></div>
        </section>

        <section className="grid gap-3 md:grid-cols-3 lg:grid-cols-6">
          {[
            ['Mission Status', 'COMPLETED', 'emerald'],
            ['Engine Health', `${health}%`, 'emerald'],
            ['Mission Risk', 'MODERATE', 'amber'],
            ['Fault Events', `${filteredEvents.length}`, 'amber'],
            ['RUL', `${rul} h`, 'amber'],
            ['Data Quality', '98.7%', 'emerald'],
          ].map(([label, value, tone]) => (
            <div key={label} className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
              <div className="text-[10px] font-bold uppercase tracking-[0.15em] text-slate-500">{label}</div>
              <div className={`mt-2 font-mono text-xl font-bold ${tone === 'amber' ? 'text-amber-700' : 'text-slate-900'}`}>{value}</div>
            </div>
          ))}
        </section>

        <Section eyebrow="Mission #027" title="Engineering summary">
          <div className="grid gap-4 lg:grid-cols-[1.5fr_1fr]">
            <div className="text-sm leading-6 text-slate-700">
              Mission completed with moderate thermal degradation during sustained cruise operation. The Digital Twin detected increasing CHT deviation relative to the expected engine trajectory. Diagnostic analysis indicates probable cooling-system degradation with high confidence. Engine health decreased from 94% to {health}%, and estimated RUL changed from 143 h to {rul} h.
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {[['Start', '18:42:12'], ['End', '23:17:44'], ['Duration', '04:35:32'], ['Probability', '87%']].map(([label, value]) => <div key={label} className="rounded-lg border border-slate-200 bg-slate-50 p-2"><div className="text-slate-500">{label}</div><div className="mt-1 font-mono font-bold text-slate-900">{value}</div></div>)}
            </div>
          </div>
        </Section>

        <div className="grid gap-4 lg:grid-cols-2">
          <Section eyebrow="Mission performance" title="Operational summary">
            <div className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
              {[['Duration', '04:35 h'], ['Avg Load', '72%'], ['Peak Load', '86%'], ['Avg RPM', '5080'], ['Peak CHT', '185 °C'], ['Peak EGT', '670 °C'], ['Avg Fuel', '3.3 L/h'], ['Peak Vibration', '1.8 mm/s']].map(([label, value]) => <div key={label} className="rounded-lg bg-slate-50 p-2"><div className="text-slate-500">{label}</div><div className="mt-1 font-mono font-bold text-slate-900">{value}</div></div>)}
            </div>
          </Section>
          <Section eyebrow="Component health summary" title="Health indices">
            <div className="space-y-2">
              {COMPONENT_HEALTH.filter((item) => ['Cooling System', 'Lubrication System', 'Fuel System', 'Ignition System', 'Mechanical (Pistons, Crank)', 'Sensors & Electronics'].includes(item.name)).map((item) => <div key={item.name}><div className="mb-1 flex justify-between text-xs"><span className="text-slate-600">{item.name}</span><span className="font-mono font-bold text-slate-900">{item.pct}%</span></div><div className="h-2 rounded-full bg-slate-200"><div className={`h-full rounded-full ${item.status === 'warning' ? 'bg-amber-500' : 'bg-emerald-500'}`} style={{ width: `${item.pct}%` }} /></div></div>)}
            </div>
          </Section>
        </div>

        <Section eyebrow="Engine health trend" title="Mission health history">
          <div className="aero-chart h-55 rounded-lg">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={[{ time: 'Start', health: 94 }, { time: '01:30', health: 93 }, { time: '03:00', health: 92 }, { time: '04:35', health: 91 }]}>
                <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="time" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#64748b' }} />
                <YAxis domain={[85, 100]} tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#64748b' }} />
                <Tooltip />
                <Line dataKey="health" name="Engine health %" type="monotone" stroke="#2563eb" strokeWidth={2.5} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Section>

        <Section eyebrow="Key telemetry parameters" title="Recorded telemetry summary">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-xs"><thead><tr className="border-b border-slate-200 text-slate-500"><th className="pb-2 pr-4">Parameter</th><th className="pb-2 pr-4">Average</th><th className="pb-2 pr-4">Minimum</th><th className="pb-2 pr-4">Maximum</th><th className="pb-2 pr-4">Final</th><th className="pb-2">Status</th></tr></thead><tbody>{telemetryRows.map((row) => <tr key={row.id} className="border-b border-slate-100 text-slate-700"><td className="py-2 pr-4 font-semibold">{row.label}</td><td className="py-2 pr-4 font-mono">{fixed(row.avg, row.id === 'oilPressure' || row.id === 'fuelFlow' || row.id === 'vibration' ? 2 : 0)} {row.unit}</td><td className="py-2 pr-4 font-mono">{row.min}</td><td className="py-2 pr-4 font-mono">{row.max}</td><td className="py-2 pr-4 font-mono font-bold">{row.final} {row.unit}</td><td className="py-2"><Badge>{row.status}</Badge></td></tr>)}</tbody></table>
          </div>
        </Section>

        <Section eyebrow="Mission telemetry trend" title="Parameter trend">
          <div className="mb-3 flex flex-wrap gap-2">{Object.entries(PARAMETER_META).map(([id, meta]) => <button key={id} type="button" onClick={() => setMetric(id)} className={`rounded-lg border px-2 py-1 text-[10px] font-bold uppercase ${metric === id ? 'border-blue-200 bg-blue-50 text-blue-700' : 'border-slate-200 bg-slate-50 text-slate-600'}`}>{meta.label}</button>)}</div>
          <div className="aero-chart h-57.5 rounded-lg"><ResponsiveContainer width="100%" height="100%"><LineChart data={chartData}><CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} /><XAxis dataKey="time" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#64748b' }} /><YAxis tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#64748b' }} /><Tooltip /><Line dataKey="value" name={PARAMETER_META[metric].label} type="monotone" stroke="#2563eb" strokeWidth={2.5} dot={{ r: 3 }} /></LineChart></ResponsiveContainer></div>
        </Section>

        <div className="grid gap-4 lg:grid-cols-2">
          <Section eyebrow="Diagnostic events" title="Recorded events">
            <div className="mb-3 flex gap-2"><select value={component} onChange={(event) => setComponent(event.target.value)} className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-1 text-[11px]"><option>All</option><option>Cooling</option><option>Mechanical</option><option>Cylinder 3</option></select></div>
            <div className="overflow-x-auto"><table className="min-w-full text-left text-[11px]"><thead><tr className="border-b border-slate-200 text-slate-500"><th className="pb-2 pr-3">Time</th><th className="pb-2 pr-3">Event</th><th className="pb-2 pr-3">Component</th><th className="pb-2 pr-3">Severity</th><th className="pb-2">Status</th></tr></thead><tbody>{filteredEvents.map((event) => <tr key={`${event.time}-${event.event}`} className="border-b border-slate-100"><td className="py-2 pr-3 font-mono">{event.time}</td><td className="py-2 pr-3 font-semibold">{event.event}</td><td className="py-2 pr-3">{event.component}</td><td className="py-2 pr-3"><Badge>{event.severity}</Badge></td><td className="py-2"><Badge>{event.status}</Badge></td></tr>)}</tbody></table></div>
          </Section>
          <Section eyebrow="Fault analysis" title="Cooling system degradation">
            <div className="grid grid-cols-2 gap-2 text-xs"><div><span className="text-slate-500">Probability</span><strong className="ml-2 font-mono">82%</strong></div><div><span className="text-slate-500">Confidence</span><strong className="ml-2 font-mono">89%</strong></div><div><span className="text-slate-500">Severity</span><span className="ml-2"><Badge>Warning</Badge></span></div><div><span className="text-slate-500">Status</span><span className="ml-2"><Badge>Resolved</Badge></span></div></div>
            <div className="mt-4 grid grid-cols-2 gap-2 text-xs">{[['CHT residual', '+7 °C'], ['EGT residual', '+8 °C'], ['Engine Load', '+6%'], ['Vibration', 'Normal'], ['Oil Pressure', 'Normal'], ['Affected', 'Cooling System']].map(([label, value]) => <div key={label} className="rounded-lg bg-slate-50 p-2"><div className="text-slate-500">{label}</div><div className="mt-1 font-mono font-bold text-slate-900">{value}</div></div>)}</div>
          </Section>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <Section eyebrow="Digital Twin assessment" title="Actual vs expected residuals">
            <div className="space-y-2 text-xs">{[['CHT', '185 °C', '178 °C', '+7 °C'], ['EGT', '648 °C', '640 °C', '+8 °C'], ['RPM', '5120', '5112', '+8'], ['Oil Pressure', '4.2 bar', '4.3 bar', '-0.1 bar']].map(([label, actual, expected, residual]) => <div key={label} className="grid grid-cols-4 gap-2 rounded-lg bg-slate-50 p-2"><span className="font-semibold">{label}</span><span>Actual <b className="font-mono">{actual}</b></span><span>Expected <b className="font-mono">{expected}</b></span><b className="font-mono text-amber-700">{residual}</b></div>)}</div>
          </Section>
          <Section eyebrow="Sensor integrity" title="Telemetry confidence">
            <div className="space-y-2 text-xs">{[['CHT Sensor', '96%', 'Valid'], ['EGT Sensor', '98%', 'Valid'], ['RPM Sensor', '99%', 'Valid'], ['Oil Pressure', '97%', 'Valid'], ['Telemetry Stream', '98.7%', 'Stable']].map(([label, value, state]) => <div key={label} className="flex items-center justify-between border-b border-slate-100 py-2"><span>{label}</span><span className="font-mono font-bold">{value}</span><Badge>{state}</Badge></div>)}</div>
          </Section>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <Section eyebrow="Degradation analysis" title="Health change"><div className="grid grid-cols-2 gap-2 text-xs"><div className="rounded-lg bg-slate-50 p-2">Initial health<strong className="mt-1 block font-mono text-lg">94%</strong></div><div className="rounded-lg bg-slate-50 p-2">Final health<strong className="mt-1 block font-mono text-lg">91%</strong></div></div><div className="mt-3 text-xs text-slate-600">Change <strong className="font-mono text-amber-700">-3%</strong> · Trend gradual</div></Section>
          <Section eyebrow="Remaining useful life" title="RUL estimate"><div className="font-mono text-3xl font-bold text-slate-900">{rul} h</div><div className="mt-2 text-xs text-slate-600">Prediction interval <strong>128–145 h</strong></div><div className="mt-1 text-xs text-slate-600">Confidence <strong>82%</strong> · Estimate, not a guaranteed failure time</div></Section>
          <Section eyebrow="Mission impact" title="Reliability assessment"><div className="space-y-2 text-xs"><div className="flex justify-between"><span>Completion probability</span><b>87%</b></div><div className="flex justify-between"><span>Risk</span><Badge>Moderate</Badge></div><div className="flex justify-between"><span>Primary risk</span><b>Thermal stress</b></div><button type="button" onClick={() => onNavigate && onNavigate('mission')} className="mt-2 inline-flex items-center gap-1 text-[11px] font-bold uppercase text-blue-700">View Mission <ChevronRight className="h-3.5 w-3.5" /></button></div></Section>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <Section eyebrow="Simulation summary" title="No simulation associated with this mission"><div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-4 text-xs text-slate-600">No simulation data is recorded for Mission #027. Run a scenario in Simulation to associate a what-if analysis with this mission.</div><button type="button" onClick={() => onNavigate && onNavigate('simulation')} className="mt-3 inline-flex items-center gap-1 text-[11px] font-bold uppercase text-blue-700">View Simulation <ChevronRight className="h-3.5 w-3.5" /></button></Section>
          <Section eyebrow="Recommended action" title="MONITOR / INSPECT"><div className="text-xs leading-5 text-slate-700">Thermal degradation was observed during sustained high-load operation.</div><ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-slate-700"><li>Review cooling-system condition</li><li>Inspect after mission</li><li>Monitor CHT and EGT</li><li>Avoid prolonged high-load operation until inspection</li></ul><div className="mt-3 flex items-center justify-between text-xs"><span>Priority: <b>MEDIUM</b></span><button type="button" onClick={() => onNavigate && onNavigate('diagnostics')} className="inline-flex items-center gap-1 font-bold uppercase text-blue-700">View Diagnostics <ChevronRight className="h-3.5 w-3.5" /></button></div></Section>
        </div>

        <Section eyebrow="Mission event timeline" title="Operational sequence">
          <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-9">{TIMELINE.map(([time, label, tone]) => <div key={`${time}-${label}`} className="border-l-2 border-slate-200 pl-2"><div className="font-mono text-[10px] text-slate-500">{time}</div><div className={`mt-1 text-[11px] font-semibold ${tone === 'warning' ? 'text-amber-700' : 'text-slate-700'}`}>{label}</div></div>)}</div>
        </Section>

        <div className="grid gap-4 lg:grid-cols-2">
          <Section eyebrow="Data quality" title="Report data quality"><div className="grid grid-cols-2 gap-2 text-xs">{[['Telemetry Coverage', '98.7%'], ['Packet Loss', '0.8%'], ['Sensor Coverage', '99%'], ['Timestamp Consistency', '99.2%'], ['Noise Level', 'Low'], ['Overall Quality', 'Good']].map(([label, value]) => <div key={label} className="flex justify-between rounded-lg bg-slate-50 p-2"><span className="text-slate-500">{label}</span><b>{value}</b></div>)}</div></Section>
          <Section eyebrow="Analysis confidence" title="Confidence by evidence source"><div className="space-y-2 text-xs">{[['Diagnostic Confidence', '89%'], ['RUL Confidence', '82%'], ['Mission Risk Confidence', '84%'], ['Telemetry Confidence', '96%'], ['Overall Assessment', '86%']].map(([label, value]) => <div key={label} className="flex items-center justify-between border-b border-slate-100 py-2"><span>{label}</span><b className="font-mono">{value}</b></div>)}</div></Section>
        </div>

        <Section eyebrow="Report history" title="Generated engineering records">
          <div className="overflow-x-auto"><table className="min-w-full text-left text-xs"><thead><tr className="border-b border-slate-200 text-slate-500"><th className="pb-2 pr-4">Report</th><th className="pb-2 pr-4">Mission</th><th className="pb-2 pr-4">Date</th><th className="pb-2 pr-4">Status</th><th className="pb-2 pr-4">Health</th><th className="pb-2 pr-4">Risk</th><th className="pb-2">Actions</th></tr></thead><tbody>{REPORTS.map((report) => <tr key={report.id} className="border-b border-slate-100"><td className="py-2 pr-4 font-semibold">{report.type}</td><td className="py-2 pr-4">{report.mission}</td><td className="py-2 pr-4 font-mono">{report.date}</td><td className="py-2 pr-4"><Badge>{report.status}</Badge></td><td className="py-2 pr-4 font-mono">{report.health}%</td><td className="py-2 pr-4"><Badge>{report.risk}</Badge></td><td className="py-2"><button type="button" onClick={() => setReportType(report.type)} className="mr-3 font-bold uppercase text-blue-700">View</button><button type="button" onClick={() => exportReport('JSON')} className="font-bold uppercase text-slate-600">Export</button></td></tr>)}</tbody></table></div>
        </Section>

        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-3 text-xs shadow-sm">
          <span className="text-slate-600">Export the selected report data. PDF export is not available in the current application.</span>
          <div className="flex gap-2"><button type="button" onClick={() => exportReport('CSV')} className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 font-bold text-slate-700 hover:bg-slate-50"><Download className="h-3.5 w-3.5" /> {exporting === 'CSV' ? 'Exporting...' : 'CSV'}</button><button type="button" onClick={() => exportReport('JSON')} className="inline-flex items-center gap-1 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 font-bold text-blue-700 hover:bg-blue-100"><Download className="h-3.5 w-3.5" /> {exporting === 'JSON' ? 'Exporting...' : 'JSON'}</button><button type="button" disabled title="PDF export is not implemented" className="cursor-not-allowed rounded-lg border border-slate-200 px-3 py-2 font-bold text-slate-400">PDF</button></div>
        </div>
      </div>
    </div>
  );
}
