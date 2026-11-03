import React from 'react';

export default function GaugeDonut({ value, color = '#10b981', size = 110, strokeWidth = 10, label = '', variant = 'donut' }) {
  const safeValue = Number.isFinite(Number(value)) ? Math.max(0, Math.min(100, Number(value))) : 0;

  if (variant === 'instrument') {
    return (
      <div
        className="instrument-meter"
        style={{ '--meter-color': color }}
        aria-label={`${safeValue}% ${label}`}
      >
        <div className="instrument-meter-value">{safeValue}%</div>
        <div className="instrument-meter-track" aria-hidden="true">
          <span style={{ width: `${safeValue}%` }} />
          <i style={{ left: `${safeValue}%` }} />
        </div>
        <div className="instrument-meter-scale">
          <span>0</span>
          <span>50</span>
          <span>100%</span>
        </div>
      </div>
    );
  }

  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (safeValue / 100) * circumference;
  const ticks = Array.from({ length: 12 }, (_, index) => index * 30);

  return (
    <div className="instrument-gauge relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90" aria-label={`${safeValue}% ${label}`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#cbd5e1"
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeLinecap="round"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
        {ticks.map((angle) => (
          <line
            key={angle}
            x1={size / 2}
            y1={strokeWidth / 2 + 2}
            x2={size / 2}
            y2={strokeWidth / 2 + 6}
            stroke="#94a3b8"
            strokeWidth="1"
            transform={`rotate(${angle} ${size / 2} ${size / 2})`}
          />
        ))}
      </svg>
      <div className="absolute flex flex-col items-center justify-center text-center">
        <span className="text-2xl font-black text-slate-900 leading-none tracking-tight font-mono">
          {safeValue}%
        </span>
        {label && <span className="text-[10px] font-semibold text-slate-500 mt-0.5">{label}</span>}
      </div>
    </div>
  );
}
