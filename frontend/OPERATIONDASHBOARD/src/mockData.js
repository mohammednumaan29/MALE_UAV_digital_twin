// Centralized dynamic telemetry and configuration data for Rotax 914 UAV Engine Monitoring System

export const INITIAL_PARAMETERS = {
  rpm: { label: 'RPM', val: 5120, unit: 'RPM', range: '4,800 - 5,400', status: 'normal', color: '#10b981', min: 4000, max: 6000 },
  egt: { label: 'EGT', val: 648, unit: '°C', range: '600 - 720', status: 'normal', color: '#ef4444', min: 500, max: 800 },
  cht: { label: 'CHT', val: 185, unit: '°C', range: '50 - 200', status: 'critical', color: '#f59e0b', min: 50, max: 220 },
  oilPressure: { label: 'Oil Pressure', val: 4.2, unit: 'bar', range: '3.0 - 6.0', status: 'normal', color: '#3b82f6', min: 2.0, max: 7.0 },
  oilTemp: { label: 'Oil Temp', val: 92, unit: '°C', range: '70 - 110', status: 'normal', color: '#8b5cf6', min: 50, max: 130 },
  fuelFlow: { label: 'Fuel Flow', val: 3.3, unit: 'L/h', range: '2.5 - 4.0', status: 'normal', color: '#10b981', min: 1.5, max: 5.0 },
  vibration: { label: 'Vibration', val: 1.8, unit: 'mm/s', range: '0.0 - 3.0', status: 'warning', color: '#06b6d4', min: 0.0, max: 5.0 },
  engineLoad: { label: 'Engine Load', val: 76, unit: '%', range: '60 - 90', status: 'normal', color: '#10b981', min: 0, max: 100 },
};

export const TELEMETRY_TRENDS_DATA = [
  { time: '09:55', rpm: 5090, egt: 630, cht: 172, oilP: 4.2 },
  { time: '10:00', rpm: 5100, egt: 635, cht: 174, oilP: 4.2 },
  { time: '10:05', rpm: 5105, egt: 638, cht: 176, oilP: 4.1 },
  { time: '10:10', rpm: 5115, egt: 640, cht: 179, oilP: 4.1 },
  { time: '10:15', rpm: 5120, egt: 642, cht: 181, oilP: 4.1 },
  { time: '10:20', rpm: 5118, egt: 645, cht: 183, oilP: 4.0 },
  { time: '10:24', rpm: 5120, egt: 648, cht: 185, oilP: 4.2 },
];

export const LIVE_DATA_TABLE = [
  { time: '10:24:17', rpm: 5120, egt: 648, cht: 185, oilP: 4.2, oilT: 92, fuel: 3.3, vib: 1.8, load: 76, isCritical: true },
  { time: '10:24:12', rpm: 5118, egt: 646, cht: 183, oilP: 4.1, oilT: 91, fuel: 3.2, vib: 1.7, load: 75 },
  { time: '10:24:07', rpm: 5115, egt: 645, cht: 182, oilP: 4.1, oilT: 91, fuel: 3.3, vib: 1.6, load: 75 },
  { time: '10:24:02', rpm: 5110, egt: 642, cht: 181, oilP: 4.0, oilT: 90, fuel: 3.2, vib: 1.6, load: 74 },
  { time: '10:23:57', rpm: 5108, egt: 640, cht: 185, oilP: 4.0, oilT: 90, fuel: 3.1, vib: 1.7, load: 74, isHighlight: true },
  { time: '10:23:52', rpm: 5105, egt: 638, cht: 180, oilP: 4.0, oilT: 89, fuel: 3.1, vib: 1.5, load: 73 },
  { time: '10:23:47', rpm: 5102, egt: 637, cht: 178, oilP: 3.9, oilT: 89, fuel: 3.0, vib: 1.5, load: 73 },
  { time: '10:23:42', rpm: 5100, egt: 635, cht: 176, oilP: 3.9, oilT: 88, fuel: 3.0, vib: 1.4, load: 72 },
  { time: '10:23:37', rpm: 5098, egt: 634, cht: 175, oilP: 3.9, oilT: 88, fuel: 2.9, vib: 1.4, load: 72 },
  { time: '10:23:32', rpm: 5095, egt: 632, cht: 174, oilP: 3.8, oilT: 87, fuel: 2.9, vib: 1.3, load: 71 },
];

export const COMPONENT_HEALTH = [
  { name: 'Combustion System', pct: 94, status: 'good' },
  { name: 'Cooling System', pct: 71, status: 'warning' },
  { name: 'Lubrication System', pct: 96, status: 'good' },
  { name: 'Fuel System', pct: 92, status: 'good' },
  { name: 'Ignition System', pct: 95, status: 'good' },
  { name: 'Mechanical (Pistons, Crank)', pct: 89, status: 'warning' },
  { name: 'Sensors & Electronics', pct: 97, status: 'good' },
];

export const ALARMS_EVENTS = [
  { id: 1, title: 'CHT above threshold (185 °C)', time: '10:23:57', type: 'critical', msg: 'Limit: 160 °C' },
  { id: 2, title: 'Vibration slightly elevated', time: '10:18:44', type: 'warning', msg: 'Baseline: 1.2 mm/s' },
  { id: 3, title: 'Fuel flow fluctuation', time: '10:12:31', type: 'info', msg: 'Nominal variance' },
  { id: 4, title: 'Normal operation resumed', time: '09:55:12', type: 'info', msg: 'System check clear' },
];

export const HISTORICAL_CASES = [
  { id: '#A1023', fault: 'Elevated CHT (Cyl 3)', outcome: 'Resolved (Cooling fix)' },
  { id: '#A0876', fault: 'High CHT (Cyl 2)', outcome: 'Resolved (Fuel mixture)' },
  { id: '#A0765', fault: 'CHT + EGT rise', outcome: 'Resolved (Valve cleaning)' },
  { id: '#A0591', fault: 'Intermittent CHT', outcome: 'Resolved (Sensor recalibration)' },
];

export const SCATTER_CORRELATION_DATA = Array.from({ length: 45 }, (_, i) => {
  const load = 10 + i * 2;
  const cht = 100 + load * 1.35 + (Math.random() * 18 - 9);
  return { load, cht: Math.round(cht) };
});

export const RUL_TREND_DATA = [
  { date: '01 Sep', rul: 150 },
  { date: '04 Sep', rul: 120 },
  { date: '07 Sep', rul: 95 },
  { date: '10 Sep', rul: 75 },
  { date: '13 Sep', rul: 55 },
];

export const MISSION_PROFILE_DATA = [
  { time: '00:00', plannedAlt: 0, actualAlt: 0, speed: 0 },
  { time: '00:45', plannedAlt: 3500, actualAlt: 3400, speed: 95 },
  { time: '01:30', plannedAlt: 5200, actualAlt: 5200, speed: 120 },
  { time: '02:15', plannedAlt: 5200, actualAlt: 5200, speed: 120 },
  { time: '03:00', plannedAlt: 5200, actualAlt: 5200, speed: 118 },
  { time: '04:00', plannedAlt: 0, actualAlt: 0, speed: 0 },
];

export const ENGINE_HEALTH_VS_MISSION = [
  { time: '00:00', predicted: 130, actual: 132, threshold: 200 },
  { time: '00:45', predicted: 145, actual: 148, threshold: 200 },
  { time: '01:30', predicted: 160, actual: 170, threshold: 200 },
  { time: '02:15', predicted: 168, actual: 185, threshold: 200 },
  { time: '03:00', predicted: 160, actual: null, threshold: 200 },
  { time: '04:00', predicted: 140, actual: null, threshold: 200 },
];
