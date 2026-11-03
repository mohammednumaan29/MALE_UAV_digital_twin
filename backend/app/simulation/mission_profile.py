"""
Mission Flight Profile Generator.
Generates continuous flight operating conditions (throttle, altitude, ambient temperature)
over time using smooth spline/linear keyframe interpolation.
"""

from typing import List, Tuple, Dict, Any


class MissionProfile:
    """
    Configurable UAV mission trajectory defining operating conditions over flight time.
    """

    # Default profile keyframes: (time_s, throttle_pct, altitude_ft, ambient_temp_c)
    DEFAULT_KEYFRAMES: List[Tuple[float, float, float, float]] = [
        # Segment 1: Ground Idle / Warmup (0 - 30s)
        (0.0, 15.0, 0.0, 15.0),
        (30.0, 15.0, 0.0, 15.0),

        # Segment 2: Takeoff Roll & Initial Climb (30 - 90s)
        (35.0, 100.0, 0.0, 15.0),       # Full throttle takeoff roll
        (50.0, 100.0, 300.0, 14.5),     # Liftoff & initial climb
        (90.0, 90.0, 2000.0, 11.0),     # Transition to enroute climb

        # Segment 3: High-Power Enroute Climb (90 - 150s)
        (120.0, 90.0, 6000.0, 3.0),
        (150.0, 85.0, 9500.0, -4.0),

        # Segment 4: Level Cruise (150s onwards)
        (160.0, 65.0, 10000.0, -4.8),
        (600.0, 65.0, 10000.0, -4.8),   # Sustained cruise
    ]

    def __init__(self, keyframes: List[Tuple[float, float, float, float]] | None = None):
        """
        Initialize mission profile with keyframe schedule.
        Each keyframe is (time_sec, throttle_pct, altitude_ft, ambient_temp_c).
        """
        self.keyframes = sorted(keyframes or self.DEFAULT_KEYFRAMES, key=lambda k: k[0])

    def get_flight_condition(self, time_s: float) -> Dict[str, float]:
        """
        Evaluate throttle, altitude, and ambient temperature at elapsed time t (seconds)
        using piecewise linear interpolation between adjacent keyframes.

        Args:
            time_s: Elapsed simulation time in seconds.

        Returns:
            Dict containing:
                - throttle: Throttle percentage (0% to 100%)
                - altitude_ft: Altitude in feet
                - ambient_temperature_c: Outside ambient temperature (°C)
                - phase_name: Current mission flight phase
        """
        t = max(0.0, float(time_s))

        # Before first keyframe
        if t <= self.keyframes[0][0]:
            _, th, alt, tamb = self.keyframes[0]
            phase = "IDLE"
            return {"throttle": th, "altitude_ft": alt, "ambient_temperature_c": tamb, "phase": phase}

        # After last keyframe
        if t >= self.keyframes[-1][0]:
            _, th, alt, tamb = self.keyframes[-1]
            phase = "CRUISE"
            return {"throttle": th, "altitude_ft": alt, "ambient_temperature_c": tamb, "phase": phase}

        # Find enclosing interval [k_i, k_{i+1}]
        for i in range(len(self.keyframes) - 1):
            t0, th0, alt0, tamb0 = self.keyframes[i]
            t1, th1, alt1, tamb1 = self.keyframes[i + 1]

            if t0 <= t <= t1:
                dt = t1 - t0
                frac = (t - t0) / dt if dt > 0 else 0.0

                th = th0 + frac * (th1 - th0)
                alt = alt0 + frac * (alt1 - alt0)
                tamb = tamb0 + frac * (tamb1 - tamb0)

                # Identify phase name
                if t < 30.0:
                    phase = "IDLE"
                elif t < 60.0:
                    phase = "TAKEOFF"
                elif t < 150.0:
                    phase = "CLIMB"
                else:
                    phase = "CRUISE"

                return {
                    "throttle": round(th, 2),
                    "altitude_ft": round(alt, 1),
                    "ambient_temperature_c": round(tamb, 2),
                    "phase": phase
                }

        # Fallback
        _, th, alt, tamb = self.keyframes[-1]
        return {"throttle": th, "altitude_ft": alt, "ambient_temperature_c": tamb, "phase": "CRUISE"}
