import React, { useEffect, useState } from "react";

const PARAMETERS = [
  { id: "rpm", name: "RPM", value: 5120, unit: "RPM", range: "4,800 – 5,400", color: "#10b981" },
  { id: "egt", name: "EGT", value: 648, unit: "°C", range: "600 – 720", color: "#ef4444" },
  { id: "cht", name: "CHT", value: 185, unit: "°C", range: "50 – 200", color: "#f59e0b" },
  { id: "oilPressure", name: "Oil Pressure", value: 4.2, unit: "bar", range: "3.0 – 6.0", color: "#3b82f6" },
  { id: "oilTemp", name: "Oil Temp", value: 92, unit: "°C", range: "70 – 110", color: "#a855f7" },
  { id: "fuelFlow", name: "Fuel Flow", value: 3.3, unit: "L/h", range: "2.5 – 4.0", color: "#10b981" },
  { id: "vibration", name: "Vibration", value: 1.8, unit: "mm/s", range: "0.0 – 3.0", color: "#06b6d4" },
  { id: "engineLoad", name: "Engine Load", value: 76, unit: "%", range: "60 – 90", color: "#10b981" },
];

const SENSORS = [
  {
    id: "rpm",
    name: "Propeller Speed Sensor",
    component: "Propeller / Reduction Gear",
    x: 20.2,
    y: 41.4,
    color: "#22c55e",
    value: "5,120 RPM",
    threshold: "4,800 – 5,400 RPM",
  },
  {
    id: "ambient",
    name: "Ambient Air Temperature Sensor",
    component: "Ambient Air Intake",
    x: 38.3,
    y: 18.2,
    color: "#f97316",
    value: "32 °C",
    threshold: "−20 – 50 °C",
  },
  {
    id: "fuelPressure",
    name: "Fuel Pressure & Temperature Sensor",
    component: "Fuel Delivery System",
    x: 46.4,
    y: 25.2,
    color: "#ef4444",
    value: "3.8 bar",
    threshold: "3.0 – 5.0 bar",
  },
  {
    id: "fuelFlow",
    name: "Fuel Flow Sensor",
    component: "Fuel Flow System",
    x: 58,
    y: 21.1,
    color: "#a855f7",
    value: "3.3 L/h",
    threshold: "2.5 – 4.0 L/h",
  },
  {
    id: "coolant",
    name: "Coolant Expansion Tank Level Sensor",
    component: "Cooling System",
    x: 69.1,
    y: 20.2,
    color: "#f97316",
    value: "82 %",
    threshold: "60 – 100 %",
  },
  {
    id: "intakeTemp",
    name: "Intake Air Temperature Sensor",
    component: "Air Intake",
    x: 74.6,
    y: 24,
    color: "#ef4444",
    value: "41 °C",
    threshold: "10 – 60 °C",
  },
  {
    id: "map",
    name: "Manifold Pressure Sensor (MAP)",
    component: "Intake Manifold",
    x: 78.1,
    y: 28.8,
    color: "#06b6d4",
    value: "1.42 bar",
    threshold: "0.9 – 1.8 bar",
  },
  {
    id: "intercooler",
    name: "Intercooler Outlet Temperature Sensor",
    component: "Intercooler Outlet",
    x: 89.3,
    y: 28,
    color: "#ef4444",
    value: "56 °C",
    threshold: "20 – 70 °C",
  },
  {
    id: "tps",
    name: "Throttle Position Sensor (TPS)",
    component: "Throttle Body",
    x: 80.5,
    y: 38.5,
    color: "#22c55e",
    value: "76 %",
    threshold: "0 – 100 %",
  },
  {
    id: "vibration",
    name: "Vibration Sensor",
    component: "Engine Core",
    x: 65.9,
    y: 53.5,
    color: "#facc15",
    value: "1.8 mm/s",
    threshold: "0 – 1.2 mm/s baseline",
  },
  {
    id: "gearboxTemp",
    name: "Gearbox / Gear Temperature Sensor",
    component: "Gearbox",
    x: 83.2,
    y: 54.1,
    color: "#ef4444",
    value: "78 °C",
    threshold: "50 – 95 °C",
  },
  {
    id: "cht1",
    name: "Cylinder Head Temperature Sensor — Cylinder 1",
    component: "Cylinder Head — Cylinder 1",
    x: 44.1,
    y: 46.5,
    color: "#ef4444",
    value: "154 °C",
    threshold: "50 – 160 °C",
  },
  {
    id: "cht2",
    name: "Cylinder Head Temperature Sensor — Cylinder 2",
    component: "Cylinder Head — Cylinder 2",
    x: 51.8,
    y: 46.5,
    color: "#ef4444",
    value: "157 °C",
    threshold: "50 – 160 °C",
  },
  {
    id: "cht3",
    name: "Cylinder Head Temperature Sensor — Cylinder 3",
    component: "Cylinder Head — Cylinder 3",
    x: 57,
    y: 46,
    color: "#ef4444",
    value: "185 °C",
    threshold: "50 – 160 °C",
    fault: true,
  },
  {
    id: "cht4",
    name: "Cylinder Head Temperature Sensor — Cylinder 4",
    component: "Cylinder Head — Cylinder 4",
    x: 61.5,
    y: 46,
    color: "#ef4444",
    value: "156 °C",
    threshold: "50 – 160 °C",
  },
  {
    id: "egt",
    name: "Exhaust Gas Temperature Sensor (EGT)",
    component: "Exhaust System",
    x: 32.4,
    y: 63.4,
    color: "#ef4444",
    value: "648 °C",
    threshold: "600 – 720 °C",
  },
  {
    id: "oilPressure",
    name: "Oil Pressure Sensor",
    component: "Lubrication System",
    x: 55.3,
    y: 58.6,
    color: "#06b6d4",
    value: "4.2 bar",
    threshold: "3.0 – 6.0 bar",
  },
  {
    id: "oilTemp",
    name: "Oil Temperature Sensor",
    component: "Lubrication System",
    x: 67.8,
    y: 61.9,
    color: "#ef4444",
    value: "92 °C",
    threshold: "70 – 110 °C",
  },
  {
    id: "oilLevel",
    name: "Oil Level Sensor",
    component: "Oil Tank / Sump",
    x: 79.8,
    y: 66,
    color: "#06b6d4",
    value: "76 %",
    threshold: "50 – 100 %",
  },
];

const ENGINE_ID = "rotax914-uav-01";

const INITIAL_HISTORY = {
  rpm: [5088, 5102, 5097, 5110, 5108, 5118, 5106, 5120],
  egt: [642, 645, 644, 647, 649, 646, 650, 648],
  cht: [172, 174, 176, 178, 179, 181, 184, 185],
  oilPressure: [4.25, 4.22, 4.24, 4.18, 4.21, 4.2, 4.23, 4.2],
  oilTemp: [89, 90, 90, 91, 91, 92, 91, 92],
  fuelFlow: [3.2, 3.3, 3.25, 3.3, 3.35, 3.28, 3.3, 3.3],
  vibration: [1.5, 1.55, 1.6, 1.62, 1.7, 1.65, 1.75, 1.8],
  engineLoad: [72, 73, 74, 75, 74, 76, 75, 76],
};

const normalizeTelemetryFrame = (payload) => {
  const frame = payload?.telemetry || payload || {};

  const normalizedEngineLoad = frame.engine_load ?? frame.engineLoad ?? 0;

  return {
    rpm: Number(frame.rpm ?? 0),
    egt: Number(frame.egt_c ?? frame.egt ?? 0),
    cht: Number(frame.cht_c ?? frame.cht ?? 0),
    oilPressure: Number(frame.oil_pressure_bar ?? frame.oilPressure ?? 0),
    oilTemp: Number(frame.oil_temperature_c ?? frame.oilTemp ?? 0),
    fuelFlow: Number(frame.fuel_flow_lph ?? frame.fuelFlow ?? 0),
    vibration: Number(frame.vibration_g ?? frame.vibration ?? 0),
    engineLoad: Number(normalizedEngineLoad > 1 ? normalizedEngineLoad : normalizedEngineLoad * 100),
    altitude: Number(frame.altitude_ft ?? 0),
    ambientTemp: Number(frame.ambient_temperature_c ?? frame.ambientTemp ?? 0),
    throttle: Number(frame.throttle ?? 0),
  };
};

function Icon({ type, size = 17 }) {
  const props = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round",
    strokeLinejoin: "round",
  };

  if (type === "activity") {
    return (
      <svg {...props}>
        <polyline points="3 12 7 12 10 4 14 20 17 12 21 12" />
      </svg>
    );
  }

  if (type === "search") {
    return (
      <svg {...props}>
        <circle cx="11" cy="11" r="6.5" />
        <path d="m16 16 4 4" />
      </svg>
    );
  }

  if (type === "refresh") {
    return (
      <svg {...props}>
        <path d="M20 11a8 8 0 0 0-14.7-4L4 9" />
        <path d="M4 4v5h5" />
        <path d="M4 13a8 8 0 0 0 14.7 4L20 15" />
        <path d="M20 20v-5h-5" />
      </svg>
    );
  }

  if (type === "alert") {
    return (
      <svg {...props}>
        <path d="M12 3 21 19H3L12 3Z" />
        <path d="M12 9v4" />
        <circle cx="12" cy="16" r=".6" fill="currentColor" />
      </svg>
    );
  }

  if (type === "check") {
    return (
      <svg {...props}>
        <circle cx="12" cy="12" r="9" />
        <path d="m8 12 2.5 2.5L16 9" />
      </svg>
    );
  }

  if (type === "database") {
    return (
      <svg {...props}>
        <ellipse cx="12" cy="5" rx="7" ry="3" />
        <path d="M5 5v7c0 1.7 3.1 3 7 3s7-1.3 7-3V5" />
        <path d="M5 12v7c0 1.7 3.1 3 7 3s7-1.3 7-3v-7" />
      </svg>
    );
  }

  if (type === "chart") {
    return (
      <svg {...props}>
        <path d="M4 19V5" />
        <path d="M4 19h16" />
        <polyline points="7 15 10 11 13 13 18 7" />
      </svg>
    );
  }

  return (
    <svg {...props}>
      <circle cx="12" cy="12" r="9" />
    </svg>
  );
}

function Sparkline({ values, color }) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const points = values
    .map((value, index) => {
      const x = (index / Math.max(values.length - 1, 1)) * 100;
      const y = 100 - ((value - min) / range) * 80 - 10;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg viewBox="0 0 100 100" preserveAspectRatio="none">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="2"
        vectorEffect="non-scaling-stroke"
        strokeLinecap="round"
      />
    </svg>
  );
}

function ParameterCard({ parameter, value, history }) {
  const warning = parameter.id === "cht" && value >= 180;
  const [minimum, maximum] = parameter.range.split("–").map((item) => Number(item.replace(",", "").trim()));
  const position = Math.max(0, Math.min(100, ((value - minimum) / (maximum - minimum)) * 100));

  return (
    <div className={`parameter-card ${warning ? "warning" : ""}`}>
      <div className="parameter-header">
        <span>{parameter.name}</span>
        <i style={{ background: parameter.color }} />
      </div>

      <div className="parameter-value">
        {parameter.id === "oilPressure" ||
        parameter.id === "fuelFlow" ||
        parameter.id === "vibration"
          ? Number(value).toFixed(1)
          : Math.round(value)}

        <small>{parameter.unit}</small>
      </div>

      <div className="parameter-range">({parameter.range})</div>

      <div className={`instrument-strip ${warning ? "warning" : ""}`}>
        <span style={{ width: `${position}%`, background: parameter.color }} />
      </div>
      <div className="instrument-readout">
        <span>LIVE</span>
        <span>{warning ? "WATCH" : "NORMAL"}</span>
      </div>

      <div className="sparkline">
        <Sparkline values={history} color={parameter.color} />
      </div>
    </div>
  );
}

function SensorLocations({ values }) {
  const [hoveredSensor, setHoveredSensor] = useState(null);

  const selected =
    SENSORS.find((sensor) => sensor.id === hoveredSensor);

  const isCritical = selected?.id === "cht3" && values.cht >= 180;

  const isWarning = selected?.id === "vibration" && values.vibration >= 1.8;

  return (
    <div className="panel sensor-panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">
            <Icon type="database" />
            Sensor Locations
          </div>

          <div className="panel-subtitle">
            Live sensor positions mapped to actual engine components
          </div>
        </div>

        <div className="live-label">
          <span />
          LIVE DETECTION
        </div>
      </div>

      <div className="sensor-map">
        <img
          src="/engine_3d.png"
          alt="ROTAX 914 engine sensor locations"
          className="engine-map-image"
        />

        {SENSORS.map((sensor) => {
          const critical =
            sensor.id === "cht3" && values.cht >= 180;

          const warning =
            sensor.id === "vibration" &&
            values.vibration >= 1.8;

          return (
            <button
              key={sensor.id}
              className={[
                "sensor-marker",
                critical ? "critical" : "",
                warning ? "warning" : "",
                hoveredSensor === sensor.id ? "selected" : "",
              ].join(" ")}
              style={{
                left: `${sensor.x}%`,
                top: `${sensor.y}%`,
                "--sensor-color": sensor.color,
              }}
              onMouseEnter={() => setHoveredSensor(sensor.id)}
              onMouseLeave={() => setHoveredSensor(null)}
              title={sensor.name}
            >
              <span className="marker-ring" />
              <span className="marker-core" />

              {(critical || warning) && (
                <span className="marker-pulse" />
              )}
            </button>
          );
        })}

        {selected && (
          <div
            className={[
              "detection-card",
              isCritical ? "critical-card" : "",
              isWarning ? "warning-card" : "",
              selected.y < 42 ? "detection-card-below" : "",
              selected.x > 58 ? "detection-card-left" : "",
            ].join(" ")}
            style={{
              left: `${selected.x}%`,
              top: `${selected.y}%`,
            }}
          >
            <div className="detection-title">
              <div className="detection-icon">
                {isCritical || isWarning ? (
                  <Icon type="alert" size={14} />
                ) : (
                  <Icon type="check" size={14} />
                )}
              </div>

              <div>
                <strong>{selected.name}</strong>
                <span>
                  {isCritical
                    ? "CRITICAL DETECTION"
                    : isWarning
                    ? "WARNING DETECTION"
                    : "NORMAL"}
                </span>
              </div>
            </div>

            <div className="detection-component">
              {selected.component}
            </div>

            <div className="detection-row">
              <span>Current Reading</span>
              <strong>
                {selected.id === "cht3"
                  ? `${Math.round(values.cht)} °C`
                  : selected.value}
              </strong>
            </div>

            <div className="detection-row">
              <span>Threshold</span>
              <strong>{selected.threshold}</strong>
            </div>

            {isCritical && (
              <div className="problem-box">
                <Icon type="alert" size={13} />
                <span>
                  Cylinder 3 CHT is{" "}
                  <strong>
                    {Math.round(values.cht - 160)}°C
                  </strong>{" "}
                  above the maximum threshold.
                </span>
              </div>
            )}

            {isWarning && (
              <div className="problem-box warning-problem">
                <Icon type="alert" size={13} />
                <span>
                  Vibration is elevated above the normal baseline.
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="sensor-footer">
        <div>
          <span className="footer-dot" />
          <strong>
            {
              SENSORS.filter(
                (sensor) =>
                  sensor.id === "cht3" && values.cht >= 180
              ).length
            }{" "}
            Critical
          </strong>

          <em />

          <strong>
            {
              SENSORS.filter(
                (sensor) =>
                  sensor.id === "vibration" &&
                  values.vibration >= 1.8
              ).length
            }{" "}
            Warning
          </strong>

          <em />

          <strong>
            {SENSORS.length - 2} Normal
          </strong>
        </div>

        <span>Hover over a sensor to inspect</span>
      </div>
    </div>
  );
}

function TrendChart({ selected, history }) {
  if (!selected.length) {
    return (
      <div className="empty-chart">
        <Icon type="chart" size={22} />
        <span>Select parameters to display trends.</span>
      </div>
    );
  }

  const colors = {
    rpm: "#10b981",
    egt: "#ef4444",
    cht: "#f59e0b",
    oilPressure: "#3b82f6",
    oilTemp: "#a855f7",
    fuelFlow: "#10b981",
    vibration: "#06b6d4",
    engineLoad: "#10b981",
  };

  return (
    <div className="trend-chart aero-chart">
      <div className="chart-grid">
        {[1, 2, 3, 4, 5].map((item) => (
          <span key={item} />
        ))}
      </div>

      <div className="chart-lines">
        {selected.map((id) => {
          const values = history[id] || [];
          const min = Math.min(...values);
          const max = Math.max(...values);
          const range = max - min || 1;

          const points = values
            .map((value, index) => {
              const x =
                (index / Math.max(values.length - 1, 1)) * 100;
              const y =
                92 -
                ((value - min) / range) * 75;

              return `${x},${y}`;
            })
            .join(" ");

          return (
            <svg
              key={id}
              viewBox="0 0 100 100"
              preserveAspectRatio="none"
            >
              <polyline
                points={points}
                fill="none"
                stroke={colors[id]}
                strokeWidth="1.8"
                vectorEffect="non-scaling-stroke"
                strokeLinecap="round"
              />
            </svg>
          );
        })}
      </div>

      <div className="chart-axis">
        <span>21:00</span>
        <span>21:05</span>
        <span>21:10</span>
        <span>21:15</span>
        <span>21:20</span>
        <span>21:25</span>
      </div>
    </div>
  );
}

function ParameterSelection({ selected, setSelected }) {
  const [search, setSearch] = useState("");

  const filtered = PARAMETERS.filter((parameter) =>
    parameter.name.toLowerCase().includes(search.toLowerCase())
  );

  const toggle = (id) => {
    setSelected((current) =>
      current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id]
    );
  };

  return (
    <div className="panel selection-panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">
            <Icon type="chart" />
            Parameter Selection
          </div>

          <div className="panel-subtitle">
            Select parameters for trend analysis
          </div>
        </div>

        <strong className="selected-count">
          {selected.length} selected
        </strong>
      </div>

      <div className="search">
        <Icon type="search" size={14} />

        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search parameters..."
        />
      </div>

      <div className="selection-list">
        {filtered.map((parameter) => (
          <label key={parameter.id}>
            <input
              type="checkbox"
              checked={selected.includes(parameter.id)}
              onChange={() => toggle(parameter.id)}
            />

            <span className="custom-check">
              {selected.includes(parameter.id) && "✓"}
            </span>

            {parameter.name}
          </label>
        ))}
      </div>

      <button
        className="reset-button"
        onClick={() =>
          setSelected(PARAMETERS.map((parameter) => parameter.id))
        }
      >
        <Icon type="refresh" size={13} />
        Reset Selection
      </button>
    </div>
  );
}

function LiveDataTable({ values }) {
  const rows = [
    [
      new Date().toLocaleTimeString("en-GB", { hour12: false }),
      values.rpm,
      values.egt,
      values.cht,
      values.oilPressure,
      values.oilTemp,
      values.fuelFlow,
      values.vibration,
      values.engineLoad,
      values.altitude,
      values.ambientTemp,
      values.throttle,
    ],
  ];

  return (
    <div className="panel table-panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">
            <Icon type="database" />
            Live Data Table
          </div>

          <div className="panel-subtitle">
            Latest telemetry records received from the data source
          </div>
        </div>

        <div className="table-live">
          <span />
          LIVE
        </div>
      </div>

      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>TIME</th>
              <th>RPM</th>
              <th>EGT</th>
              <th>CHT</th>
              <th>OIL P</th>
              <th>OIL T</th>
              <th>FUEL FLOW</th>
              <th>VIBRATION</th>
              <th>LOAD</th>
              <th>ALTITUDE</th>
              <th>AMBIENT</th>
              <th>THROTTLE</th>
            </tr>
          </thead>

          <tbody>
            {rows.map((row, index) => (
              <tr key={index}>
                {row.map((cell, cellIndex) => (
                  <td
                    key={cellIndex}
                    className={
                      cellIndex === 3 && Number(cell) >= 180
                        ? "critical-cell"
                        : ""
                    }
                  >
                    {typeof cell === "number"
                      ? Number(cell).toFixed(
                          cellIndex === 4 ||
                            cellIndex === 5 ||
                            cellIndex === 6 ||
                            cellIndex === 7 ||
                            cellIndex === 10
                            ? 1
                            : 0
                        )
                      : cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function EventsPanel() {
  const events = [
    ["21:12:18", "CRITICAL", "Cylinder 3 CHT above threshold"],
    ["21:11:44", "WARNING", "Vibration slightly elevated"],
    ["21:10:52", "INFO", "CHT increase detected during high load"],
    ["21:09:31", "NORMAL", "Telemetry synchronization completed"],
  ];

  return (
    <div className="panel events-panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">
            <Icon type="alert" />
            Alarms & Events
          </div>

          <div className="panel-subtitle">
            Sensor-generated events and detections
          </div>
        </div>

        <span className="view-all">View All →</span>
      </div>

      <div className="events">
        {events.map(([time, type, message]) => (
          <div className="event" key={time}>
            <span className="event-time">{time}</span>

            <span
              className={`event-dot ${type.toLowerCase()}`}
            />

            <span className="event-message">
              {message}
            </span>

            <span className={`event-tag ${type.toLowerCase()}`}>
              {type}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function TelemetryView() {
  const [values, setValues] = useState({
    ...Object.fromEntries(
      PARAMETERS.map((parameter) => [
        parameter.id,
        parameter.value,
      ])
    ),
    altitude: 10500,
    ambientTemp: 30,
    throttle: 65,
  });

  const [history, setHistory] = useState(INITIAL_HISTORY);

  const [selected, setSelected] = useState(
    PARAMETERS.map((parameter) => parameter.id)
  );

  useEffect(() => {
    let socket = null;
    let cancelled = false;

    const loadLatestTelemetry = async () => {
      try {
        const response = await fetch(`/api/telemetry/latest?engine_id=${ENGINE_ID}`);
        if (!response.ok || cancelled) {
          return;
        }

        const latest = await response.json();
        setValues((current) => ({
          ...current,
          ...normalizeTelemetryFrame(latest),
        }));
      } catch (error) {
        // Ignore fetch failures while the backend socket is establishing.
      }
    };

    const applyIncomingTelemetry = (payload) => {
      const nextValues = normalizeTelemetryFrame(payload);
      setValues((current) => ({
        ...current,
        ...nextValues,
      }));
    };

    loadLatestTelemetry();

    try {
      socket = new WebSocket(`ws://localhost:8000/ws/telemetry/${ENGINE_ID}`);

      socket.onmessage = (event) => {
        if (cancelled) {
          return;
        }

        const payload = JSON.parse(event.data);
        applyIncomingTelemetry(payload);
      };
    } catch (error) {
      // WebSocket connections are optional if the backend is unavailable.
    }

    return () => {
      cancelled = true;
      if (socket) {
        socket.close();
      }
    };
  }, []);

  /*
   * IMPORTANT FIX:
   *
   * The previous code had invalid syntax around:
   *
   * next[parameter.id] = [
   *   ...
   * ].slice(-29),
   * currentValue,
   *
   * This version uses the functional state update below,
   * so there is no malformed assignment or stale values.
   */

  useEffect(() => {
    setHistory((currentHistory) => {
      const nextHistory = { ...currentHistory };

      PARAMETERS.forEach((parameter) => {
        const currentValue = values[parameter.id];

        const oldValues =
          nextHistory[parameter.id] || [];

        nextHistory[parameter.id] = [
          ...oldValues.slice(-29),
          currentValue,
        ];
      });

      return nextHistory;
    });
  }, [values]);

  return (
    <div className="telemetry-page">
      <style>{`
        * {
          box-sizing: border-box;
        }

        .telemetry-page {
          min-height: 100vh;
          width: 100%;
          padding: 24px;
          background: #f7f9fc;
          color: #132942;
          font-family: inherit;
          font-size: 14px;
        }

        .telemetry-container {
          width: 100%;
          max-width: 1600px;
          margin: 0 auto;
        }

        .telemetry-heading {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 20px;
          margin-bottom: 18px;
        }

        .telemetry-title {
          margin: 0;
          color: #0b1b34;
          font-size: 24px;
          line-height: 1.1;
          font-weight: 760;
          letter-spacing: -.5px;
        }

        .telemetry-description {
          margin: 5px 0 0;
          color: #718198;
          font-size: 13px;
        }

        .telemetry-controls {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .live-indicator {
          height: 34px;
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 0 11px;
          border: 1px solid #a8ead2;
          border-radius: 8px;
          background: #edfff8;
          color: #078f68;
          font-size: 11px;
          font-weight: 750;
        }

        .live-indicator span,
        .table-live span {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: #10b981;
        }

        .select-control {
          height: 34px;
          border: 1px solid #d8e1eb;
          border-radius: 8px;
          padding: 0 10px;
          background: white;
          color: #41546c;
          font-size: 11px;
        }

        .primary-button {
          height: 34px;
          display: flex;
          align-items: center;
          gap: 5px;
          padding: 0 12px;
          border: 0;
          border-radius: 8px;
          background: #1769ff;
          color: white;
          font-size: 10px;
          font-weight: 700;
        }

        .parameter-grid {
          display: grid;
          grid-template-columns: repeat(8, minmax(0, 1fr));
          gap: 10px;
          margin-bottom: 16px;
        }

        .parameter-card {
          height: 172px;
          min-width: 0;
          padding: 12px;
          border: 1px solid #dce4ee;
          border-radius: 10px;
          background: white;
        }

        .parameter-card.warning {
          border-color: #f3bf57;
          background: #fffdf8;
        }

        .parameter-header {
          min-height: 16px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          color: #64748a;
          font-size: 11px;
          font-weight: 600;
        }

        .parameter-header i {
          width: 6px;
          height: 6px;
          border-radius: 50%;
        }

        .parameter-value {
          min-height: 25px;
          margin-top: 8px;
          color: #122640;
          font-size: 20px;
          font-weight: 760;
        }

        .parameter-value small {
          margin-left: 4px;
          color: #78879a;
          font-size: 11px;
          font-weight: 500;
        }

        .parameter-range {
          min-height: 12px;
          margin-top: 4px;
          color: #98a5b5;
          font-size: 10px;
        }

        .instrument-strip {
          margin-top: 8px;
          height: 8px;
        }

        .instrument-readout {
          display: flex;
          justify-content: space-between;
          margin-top: 3px;
          color: #7d8ca0;
          font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
          font-size: 7px;
          letter-spacing: .08em;
        }

        .sparkline {
          height: 30px;
          margin-top: 6px;
        }

        .sparkline svg {
          width: 100%;
          height: 100%;
        }

        .trend-sensor-grid {
          display: grid;
          grid-template-columns: minmax(0, 1.7fr) minmax(460px, 1fr);
          gap: 16px;
          margin-bottom: 16px;
        }

        .panel {
          overflow: hidden;
          border: 1px solid #dce4ee;
          border-radius: 11px;
          background: white;
        }

        .panel-header {
          min-height: 58px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 15px;
          padding: 11px 14px;
          border-bottom: 1px solid #edf1f5;
        }

        .panel-title {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #172b46;
          font-size: 13px;
          font-weight: 730;
        }

        .panel-title svg {
          color: #1769ff;
        }

        .panel-subtitle {
          margin-top: 3px;
          color: #8997a9;
          font-size: 11px;
        }

        .trend-chart {
          position: relative;
          height: 342px;
          padding: 18px 20px 34px 45px;
        }

        .chart-grid {
          position: absolute;
          inset: 18px 20px 34px 45px;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
        }

        .chart-grid span {
          width: 100%;
          height: 1px;
          border-top: 1px dashed #e4eaf1;
        }

        .chart-lines {
          position: absolute;
          inset: 18px 20px 34px 45px;
        }

        .chart-lines svg {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
        }

        .chart-axis {
          position: absolute;
          left: 45px;
          right: 20px;
          bottom: 12px;
          display: flex;
          justify-content: space-between;
          color: #8997a9;
          font-size: 8px;
        }

        .empty-chart {
          height: 342px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 8px;
          color: #9aa8b9;
          font-size: 10px;
        }

        .live-label {
          display: flex;
          align-items: center;
          gap: 6px;
          color: #07966b;
          font-size: 8px;
          font-weight: 750;
        }

        .live-label span {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #10b981;
        }

        .sensor-map {
          position: relative;
          height: 342px;
          overflow: hidden;
          background: #031723;
        }

        .engine-map-image {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
          object-fit: contain;
          object-position: center;
          display: block;
        }

        .sensor-marker {
          position: absolute;
          z-index: 5;
          width: 22px;
          height: 22px;
          padding: 0;
          border: 0;
          background: transparent;
          transform: translate(-50%, -50%);
          cursor: pointer;
        }

        .marker-core {
          position: absolute;
          left: 6px;
          top: 6px;
          width: 10px;
          height: 10px;
          border: 2px solid white;
          border-radius: 50%;
          background: var(--sensor-color);
          box-shadow: 0 2px 7px rgba(0,0,0,.5);
        }

        .marker-ring {
          position: absolute;
          inset: 1px;
          border: 1px solid var(--sensor-color);
          border-radius: 50%;
        }

        .sensor-marker.selected .marker-ring {
          box-shadow:
            0 0 0 2px rgba(255,255,255,.75),
            0 0 12px var(--sensor-color);
        }

        .sensor-marker.critical .marker-core {
          background: #ef4444;
          box-shadow:
            0 0 0 3px rgba(239,68,68,.25),
            0 0 15px rgba(239,68,68,.8);
        }

        .sensor-marker.critical .marker-ring {
          border-color: #ef4444;
          animation: pulse 1s infinite;
        }

        .sensor-marker.warning .marker-core {
          background: #f59e0b;
        }

        .sensor-marker.warning .marker-ring {
          border-color: #f59e0b;
          animation: pulse 1.4s infinite;
        }

        .marker-pulse {
          position: absolute;
          inset: -3px;
          border: 2px solid #ef4444;
          border-radius: 50%;
          animation: pulse 1s infinite;
        }

        @keyframes pulse {
          0% {
            transform: scale(.7);
            opacity: .9;
          }

          100% {
            transform: scale(1.7);
            opacity: 0;
          }
        }

        .detection-card {
          position: absolute;
          z-index: 20;
          width: 295px;
          padding: 11px;
          border: 1px solid rgba(91,111,128,.8);
          border-radius: 9px;
          background: rgba(3,18,29,.96);
          color: white;
          box-shadow: 0 10px 25px rgba(0,0,0,.35);
          pointer-events: none;
          transform: translate(-14px, calc(-100% - 14px));
        }

        .detection-card-below {
          transform: translate(-14px, 14px);
        }

        .detection-card-left {
          transform: translate(calc(-100% + 14px), calc(-100% - 14px));
        }

        .detection-card-left.detection-card-below {
          transform: translate(calc(-100% + 14px), 14px);
        }

        .critical-card {
          border-color: rgba(239,68,68,.75);
        }

        .warning-card {
          border-color: rgba(245,158,11,.75);
        }

        .detection-title {
          display: flex;
          align-items: flex-start;
          gap: 8px;
        }

        .detection-icon {
          width: 26px;
          height: 26px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 6px;
          color: #10b981;
          background: rgba(16,185,129,.1);
        }

        .critical-card .detection-icon {
          color: #ef4444;
          background: rgba(239,68,68,.12);
        }

        .warning-card .detection-icon {
          color: #f59e0b;
          background: rgba(245,158,11,.12);
        }

        .detection-title div:last-child {
          min-width: 0;
          display: flex;
          flex-direction: column;
        }

        .detection-title strong {
          color: white;
          font-size: 10px;
          line-height: 1.35;
        }

        .detection-title span {
          margin-top: 2px;
          color: #8da1b6;
          font-size: 7px;
          font-weight: 750;
          letter-spacing: .3px;
        }

        .critical-card .detection-title span {
          color: #ff7777;
        }

        .warning-card .detection-title span {
          color: #fbbf24;
        }

        .detection-component {
          margin-top: 7px;
          color: #9fb0c1;
          font-size: 8px;
        }

        .detection-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 10px;
          margin-top: 6px;
          padding-top: 6px;
          border-top: 1px solid rgba(255,255,255,.08);
        }

        .detection-row span {
          color: #8194a8;
          font-size: 8px;
        }

        .detection-row strong {
          color: #dce6ef;
          font-size: 9px;
        }

        .critical-card .detection-row:first-of-type strong {
          color: #ff6b6b;
        }

        .problem-box {
          display: flex;
          gap: 6px;
          margin-top: 7px;
          padding: 7px;
          border: 1px solid rgba(239,68,68,.3);
          border-radius: 6px;
          background: rgba(239,68,68,.08);
          color: #ffaaaa;
          font-size: 8px;
          line-height: 1.4;
        }

        .problem-box strong {
          color: #ff7070;
        }

        .warning-problem {
          border-color: rgba(245,158,11,.3);
          background: rgba(245,158,11,.08);
          color: #f7c968;
        }

        .sensor-footer {
          min-height: 42px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 13px;
          border-top: 1px solid #edf1f5;
          color: #7d8ca0;
          font-size: 8px;
        }

        .sensor-footer > div {
          display: flex;
          align-items: center;
          gap: 7px;
        }

        .footer-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #10b981;
        }

        .sensor-footer strong {
          font-weight: 650;
        }

        .sensor-footer em {
          width: 1px;
          height: 11px;
          background: #dce4ec;
        }

        .lower-grid {
          display: grid;
          grid-template-columns:
            minmax(190px,.75fr)
            minmax(0,1.8fr)
            minmax(280px,1fr);
          gap: 16px;
          margin-bottom: 16px;
        }

        .selected-count {
          color: #1769ff;
          font-size: 8px;
        }

        .search {
          height: 32px;
          display: flex;
          align-items: center;
          gap: 6px;
          margin: 10px;
          padding: 0 8px;
          border: 1px solid #dbe3ed;
          border-radius: 7px;
          color: #8b98aa;
        }

        .search input {
          width: 100%;
          border: 0;
          outline: 0;
          background: transparent;
          font-size: 9px;
        }

        .selection-list {
          max-height: 220px;
          overflow-y: auto;
          padding: 0 10px;
        }

        .selection-list label {
          min-height: 30px;
          display: flex;
          align-items: center;
          gap: 8px;
          color: #40536b;
          font-size: 9px;
          cursor: pointer;
        }

        .selection-list input {
          display: none;
        }

        .custom-check {
          width: 14px;
          height: 14px;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 1px solid #bdc9d6;
          border-radius: 3px;
          color: white;
          background: white;
          font-size: 9px;
        }

        .selection-list input:checked + .custom-check {
          border-color: #1769ff;
          background: #1769ff;
        }

        .reset-button {
          width: calc(100% - 20px);
          height: 30px;
          margin: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 5px;
          border: 1px solid #dce4ee;
          border-radius: 7px;
          background: white;
          color: #63748b;
          font-size: 9px;
          cursor: pointer;
        }

        .table-panel {
          min-width: 0;
        }

        .table-live {
          display: flex;
          align-items: center;
          gap: 5px;
          color: #07966b;
          font-size: 8px;
          font-weight: 750;
        }

        .table-scroll {
          overflow-x: auto;
        }

        .table-panel table {
          width: 100%;
          border-collapse: collapse;
          table-layout: fixed;
        }

        .table-panel th {
          height: 34px;
          padding: 0 10px;
          border-bottom: 1px solid #e7ecf2;
          background: #fafbfd;
          color: #7d8ca0;
          text-align: left;
          font-size: 10px;
          font-weight: 700;
          letter-spacing: .04em;
        }

        .table-panel td {
          height: 35px;
          padding: 0 10px;
          border-bottom: 1px solid #edf1f5;
          color: #40536b;
          font-size: 11px;
          font-variant-numeric: tabular-nums;
        }

        .table-panel th:not(:first-child),
        .table-panel td:not(:first-child) {
          text-align: right;
        }

        .table-panel th:first-child,
        .table-panel td:first-child {
          width: 82px;
          text-align: left;
          font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        }

        .table-panel th:nth-child(2),
        .table-panel td:nth-child(2),
        .table-panel th:nth-child(3),
        .table-panel td:nth-child(3),
        .table-panel th:nth-child(4),
        .table-panel td:nth-child(4),
        .table-panel th:nth-child(5),
        .table-panel td:nth-child(5),
        .table-panel th:nth-child(6),
        .table-panel td:nth-child(6),
        .table-panel th:nth-child(7),
        .table-panel td:nth-child(7),
        .table-panel th:nth-child(8),
        .table-panel td:nth-child(8),
        .table-panel th:nth-child(9),
        .table-panel td:nth-child(9) {
          width: 11.1%;
        }

        .critical-cell {
          color: #ef4444 !important;
          font-weight: 750;
        }

        .quality-panel {
          padding: 14px;
        }

        .quality-title {
          color: #172b46;
          font-size: 11px;
          font-weight: 730;
        }

        .quality-subtitle {
          margin-top: 2px;
          color: #8997a9;
          font-size: 8px;
        }

        .quality-value {
          margin-top: 12px;
          color: #0aa678;
          font-size: 26px;
          font-weight: 760;
        }

        .quality-bar {
          height: 7px;
          margin-top: 10px;
          overflow: hidden;
          border-radius: 10px;
          background: #eaf0f5;
        }

        .quality-bar span {
          display: block;
          width: 94%;
          height: 100%;
          background: #10b981;
        }

        .quality-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 13px;
          margin-top: 15px;
        }

        .quality-grid span {
          display: block;
          color: #8795a7;
          font-size: 8px;
        }

        .quality-grid strong {
          display: block;
          margin-top: 2px;
          color: #293f5a;
          font-size: 10px;
        }

        .events-panel {
          margin-top: 0;
        }

        .view-all {
          color: #1769ff;
          font-size: 9px;
          font-weight: 700;
        }

        .events {
          padding: 0 14px;
        }

        .event {
          min-height: 45px;
          display: grid;
          grid-template-columns: 75px 8px minmax(0,1fr) 70px;
          align-items: center;
          gap: 9px;
          border-bottom: 1px solid #edf1f5;
        }

        .event:last-child {
          border-bottom: 0;
        }

        .event-time {
          color: #8290a2;
          font-size: 8px;
        }

        .event-dot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
        }

        .event-dot.critical {
          background: #ef4444;
        }

        .event-dot.warning {
          background: #f59e0b;
        }

        .event-dot.info {
          background: #3b82f6;
        }

        .event-dot.normal {
          background: #10b981;
        }

        .event-message {
          color: #354a64;
          font-size: 10px;
        }

        .event-tag {
          justify-self: end;
          padding: 3px 6px;
          border-radius: 4px;
          font-size: 7px;
          font-weight: 750;
        }

        .event-tag.critical {
          color: #dc2626;
          background: #fee2e2;
        }

        .event-tag.warning {
          color: #d97706;
          background: #fef3c7;
        }

        .event-tag.info {
          color: #2563eb;
          background: #dbeafe;
        }

        .event-tag.normal {
          color: #059669;
          background: #d1fae5;
        }

        @media (max-width: 1500px) {
          .parameter-grid {
            grid-template-columns: repeat(4, minmax(0,1fr));
          }

          .trend-sensor-grid {
            grid-template-columns:
              minmax(0,1.45fr)
              minmax(400px,1fr);
          }
        }

        @media (max-width: 1100px) {
          .parameter-grid {
            grid-template-columns: repeat(2, minmax(0,1fr));
          }

          .trend-sensor-grid {
            grid-template-columns: 1fr;
          }

          .lower-grid {
            grid-template-columns: 1fr;
          }

          .telemetry-heading {
            flex-direction: column;
          }

          .telemetry-controls {
            justify-content: flex-start;
            flex-wrap: wrap;
          }
        }

        @media (max-width: 650px) {
          .telemetry-page {
            padding: 16px 10px 30px;
          }

          .parameter-grid {
            grid-template-columns: 1fr;
          }

          .sensor-map {
            height: 300px;
          }

          .detection-card {
            width: 260px;
          }

          .sensor-footer > span {
            display: none;
          }
        }
      `}</style>

      <div className="telemetry-container">
        <header className="dashboard-header telemetry-heading">
          <div>
            <h1 className="telemetry-title">Telemetry</h1>

            <p className="telemetry-description">
              Live sensor data, trends and system performance.
            </p>
          </div>

          <div className="telemetry-controls">
            <div className="live-indicator">
              <span />
              LIVE
            </div>

            <select className="select-control" defaultValue="30">
              <option value="30">Last 30 minutes</option>
              <option value="60">Last 60 minutes</option>
              <option value="120">Last 2 hours</option>
            </select>

            <button className="select-control">
              <Icon type="refresh" size={12} />
              &nbsp; Refresh
            </button>

            <button className="primary-button">
              + Add Parameter
            </button>
          </div>
        </header>

        <section className="parameter-grid">
          {PARAMETERS.map((parameter) => (
            <ParameterCard
              key={parameter.id}
              parameter={parameter}
              value={values[parameter.id]}
              history={history[parameter.id]}
            />
          ))}
        </section>

        <section className="trend-sensor-grid">
          <div className="panel">
            <div className="panel-header">
              <div>
                <div className="panel-title">
                  <Icon type="chart" />
                  Parameter Trends
                </div>

                <div className="panel-subtitle">
                  Historical telemetry received from the data source
                </div>
              </div>

              <div>
                <select className="select-control" defaultValue="30">
                  <option value="30">Last 30 minutes</option>
                  <option value="60">Last 60 minutes</option>
                </select>
              </div>
            </div>

            <TrendChart
              selected={selected}
              history={history}
            />
          </div>

          <SensorLocations values={values} />
        </section>

        <section className="lower-grid">
          <ParameterSelection
            selected={selected}
            setSelected={setSelected}
          />

          <LiveDataTable values={values} />

          <div className="panel quality-panel">
            <div className="quality-title">
              Data Quality
            </div>

            <div className="quality-subtitle">
              Telemetry stream integrity
            </div>

            <div className="quality-value">94%</div>

            <div className="quality-bar">
              <span />
            </div>

            <div className="quality-grid">
              <div>
                <span>Packet Loss</span>
                <strong>1.2%</strong>
              </div>

              <div>
                <span>Sensor Coverage</span>
                <strong>98%</strong>
              </div>

              <div>
                <span>Timestamp Drift</span>
                <strong>12 ms</strong>
              </div>

              <div>
                <span>Noise Level</span>
                <strong>Low</strong>
              </div>
            </div>
          </div>
        </section>

        <EventsPanel />
      </div>
    </div>
  );
}