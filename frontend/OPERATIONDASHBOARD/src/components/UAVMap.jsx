import React, { useState } from 'react';
import { Navigation, Plus, Minus, Maximize2, ExternalLink } from 'lucide-react';

export default function UAVMap({ isLarge = false }) {
  const [zoom, setZoom] = useState(1);

  return (
    <div className={`relative w-full ${isLarge ? 'h-[440px]' : 'h-[230px]'} bg-slate-900 rounded-xl overflow-hidden shadow-xs border border-slate-200 select-none`}>
      {/* Satellite Imagery Background */}
      <div 
        className="absolute inset-0 bg-cover bg-center transition-transform duration-300"
        style={{ 
          backgroundImage: `url('/satellite_map.png')`,
          transform: `scale(${zoom})`
        }}
      >
        <div className="absolute inset-0 bg-slate-900/20 backdrop-brightness-95"></div>
      </div>

      {/* SVG Overlay for Waypoints, Flight Path & Restricted Zone */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none z-10">
        {/* Polygon: Restricted Airspace */}
        <polygon 
          points="280,40 380,50 390,140 310,160 260,110" 
          fill="rgba(239, 68, 68, 0.35)" 
          stroke="#ef4444" 
          strokeWidth="2" 
          strokeDasharray="4 3" 
        />
        <text x="310" y="100" fill="#fca5a5" fontSize="10" fontWeight="bold" textAnchor="middle">
          Restricted Airspace
        </text>

        {/* Flight Route Path Lines */}
        {/* Completed Leg: WP-1 to WP-3 */}
        <path 
          d="M 30,180 L 100,140 L 170,120" 
          fill="none" 
          stroke="#10b981" 
          strokeWidth="3.5" 
          strokeLinecap="round" 
        />
        {/* Active Leg: WP-3 to WP-4 */}
        <path 
          d="M 170,120 L 250,100" 
          fill="none" 
          stroke="#06b6d4" 
          strokeWidth="3.5" 
          strokeLinecap="round" 
        />
        {/* Upcoming Leg: WP-4 to WP-6 */}
        <path 
          d="M 250,100 L 320,70 L 390,40" 
          fill="none" 
          stroke="#3b82f6" 
          strokeWidth="2.5" 
          strokeDasharray="5 4" 
          strokeLinecap="round" 
        />

        {/* Waypoint Nodes */}
        {[
          { id: 'WP-1', x: 30, y: 180, status: 'completed' },
          { id: 'WP-2', x: 100, y: 140, status: 'completed' },
          { id: 'WP-3', x: 170, y: 120, status: 'active' },
          { id: 'WP-4', x: 250, y: 100, status: 'upcoming' },
          { id: 'WP-5', x: 320, y: 70, status: 'upcoming' },
          { id: 'WP-6', x: 390, y: 40, status: 'upcoming' },
        ].map((wp) => (
          <g key={wp.id} className="pointer-events-auto">
            <circle 
              cx={wp.x} 
              cy={wp.y} 
              r={wp.status === 'active' ? '6' : '4.5'} 
              fill={wp.status === 'completed' ? '#10b981' : wp.status === 'active' ? '#06b6d4' : '#eab308'} 
              stroke="#ffffff" 
              strokeWidth="2" 
            />
            <rect 
              x={wp.x - 16} 
              y={wp.y + 8} 
              width="32" 
              height="14" 
              rx="3" 
              fill="rgba(15, 23, 42, 0.85)" 
            />
            <text 
              x={wp.x} 
              y={wp.y + 18} 
              fill="#ffffff" 
              fontSize="8" 
              fontWeight="bold" 
              textAnchor="middle"
            >
              {wp.id}
            </text>
          </g>
        ))}

        {/* Active UAV Icon Marker at WP-4 Position */}
        <g className="animate-pulse">
          <circle cx="250" cy="100" r="14" fill="rgba(6, 182, 212, 0.3)" />
        </g>
      </svg>

      {/* UAV Info Tooltip Pinned to Marker */}
      <div className="absolute top-[55px] left-[175px] z-20 bg-slate-950/90 text-white p-2 rounded-lg border border-cyan-500/50 shadow-xl backdrop-blur-md">
        <div className="flex items-center space-x-1.5 text-[11px] font-bold text-cyan-400">
          <Navigation className="w-3.5 h-3.5 transform rotate-45" />
          <span>UAV-2026-045</span>
        </div>
        <div className="text-[9px] text-slate-300 space-y-0.5 mt-0.5 font-mono">
          <div>Alt: 5,200 ft</div>
          <div>GS: 120 kt</div>
        </div>
      </div>

      {/* Top Left Zoom Controls */}
      <div className="absolute top-3 left-3 z-20 flex flex-col space-y-1 bg-slate-900/80 backdrop-blur-md p-1 rounded-lg border border-slate-700/80">
        <button 
          onClick={() => setZoom((z) => Math.min(z + 0.2, 1.8))} 
          className="p-1 text-slate-300 hover:text-white hover:bg-slate-800 rounded transition"
          title="Zoom In"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>
        <button 
          onClick={() => setZoom((z) => Math.max(z - 0.2, 0.8))} 
          className="p-1 text-slate-300 hover:text-white hover:bg-slate-800 rounded transition"
          title="Zoom Out"
        >
          <Minus className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Top Right Expand Control */}
      <div className="absolute top-3 right-3 z-20 flex items-center space-x-2">
        {isLarge && (
          <button className="flex items-center space-x-1 bg-slate-900/80 hover:bg-slate-800 text-slate-200 text-xs px-2.5 py-1 rounded-lg border border-slate-700 backdrop-blur-md transition">
            <ExternalLink className="w-3 h-3" />
            <span>View 3D Route</span>
          </button>
        )}
        <button className="p-1.5 bg-slate-900/80 hover:bg-slate-800 text-slate-200 rounded-lg border border-slate-700 backdrop-blur-md transition">
          <Maximize2 className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Bottom Right Route Legend Box */}
      <div className="absolute bottom-3 right-3 z-20 bg-slate-950/85 backdrop-blur-md px-2.5 py-1.5 rounded-lg border border-slate-800 text-[10px] text-slate-300 space-y-1">
        <div className="flex items-center space-x-2">
          <span className="w-3 h-0.5 bg-emerald-500 rounded"></span>
          <span>Completed</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-0.5 bg-cyan-400 rounded"></span>
          <span>In Progress</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-0.5 border-b-2 border-dashed border-blue-400"></span>
          <span>Upcoming</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 bg-red-500/40 border border-red-500 rounded-xs"></span>
          <span>No-Fly Zone</span>
        </div>
      </div>
    </div>
  );
}
