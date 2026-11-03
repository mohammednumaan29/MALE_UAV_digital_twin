import React, { useState } from 'react';
import { Maximize2, Info } from 'lucide-react';

export default function SensorBluePrint() {
  const [activeSensor, setActiveSensor] = useState('cyl3_cht');

  const sensors = [
    { id: 'rpm_head', x: 75, y: 160, label: 'RPM Hall Sensor', val: '5,120 RPM', status: 'normal', color: '#10b981' },
    { id: 'egt_cyl1', x: 210, y: 100, label: 'EGT Sensor (Cyl 1)', val: '648 °C', status: 'warning', color: '#f59e0b' },
    { id: 'cht_cyl2', x: 275, y: 100, label: 'CHT Sensor (Cyl 2)', val: '172 °C', status: 'normal', color: '#10b981' },
    { id: 'cyl3_cht', x: 210, y: 220, label: 'CHT Sensor (Cyl 3)', val: '185 °C', status: 'critical', color: '#ef4444' },
    { id: 'oil_press', x: 280, y: 190, label: 'Oil Pressure Transducer', val: '4.2 bar', status: 'sensor', color: '#3b82f6' },
    { id: 'oil_temp', x: 220, y: 280, label: 'Oil Temp Thermocouple', val: '92 °C', status: 'normal', color: '#10b981' },
  ];

  return (
    <div className="relative w-full h-[320px] bg-slate-900 rounded-xl overflow-hidden shadow-xs border border-slate-800 p-4 flex flex-col justify-between select-none">
      {/* Top Title Bar */}
      <div className="flex items-center justify-between z-10">
        <h3 className="font-bold text-white text-sm tracking-wide">Sensor Locations</h3>
        
        {/* Top Right Status Legend */}
        <div className="flex items-center space-x-3 text-[11px] text-slate-300 bg-slate-800/80 px-2.5 py-1 rounded-lg border border-slate-700">
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-emerald-500"></span> Normal</span>
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-amber-500"></span> Warning</span>
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-red-500"></span> Critical</span>
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-blue-500"></span> Sensor</span>
          <button className="ml-2 text-slate-400 hover:text-white">
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Sensor photo with interactive hotspots */}
      <div className="relative flex-1 flex items-center justify-center my-2">
        <img
          src="/sensor.png"
          alt="Engine sensor locations"
          className="absolute inset-0 w-full h-full object-contain"
        />
        <svg viewBox="0 0 350 300" className="w-full h-full max-h-[220px]">
          {/* Sensor Nodes & Hotspots */}
          {sensors.map((s) => {
            const isSelected = activeSensor === s.id;
            return (
              <g 
                key={s.id} 
                onClick={() => setActiveSensor(s.id)}
                className="cursor-pointer group"
              >
                {/* Outer Glow */}
                <circle 
                  cx={s.x} 
                  cy={s.y} 
                  r={isSelected ? 10 : 7} 
                  fill={s.color} 
                  opacity={isSelected ? '0.4' : '0.25'} 
                  className={s.status === 'critical' ? 'animate-ping' : ''}
                />
                {/* Core Dot */}
                <circle 
                  cx={s.x} 
                  cy={s.y} 
                  r="5" 
                  fill={s.color} 
                  stroke="#ffffff" 
                  strokeWidth="2" 
                />
              </g>
            );
          })}
        </svg>

        {/* Selected Sensor Information Card Floating Overlay */}
        {activeSensor && (
          <div className="absolute bottom-1 left-2 z-20 bg-slate-950/90 border border-slate-700 px-3 py-1.5 rounded-lg shadow-xl text-xs text-white flex items-center space-x-2">
            <Info className="w-4 h-4 text-cyan-400" />
            <div>
              <div className="font-bold text-slate-100">
                {sensors.find(s => s.id === activeSensor)?.label}
              </div>
              <div className="text-[10px] font-mono text-cyan-400 font-semibold">
                Current Reading: {sensors.find(s => s.id === activeSensor)?.val}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
