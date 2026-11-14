#!/usr/bin/env python3
"""Streaming anomaly detector for ALBANIA — Arată a anomalie! (Sigmoid Academy)."""
from __future__ import annotations

import math
from collections import defaultdict, deque

import numpy as np

SENSORS = (
    "temperature_c",
    "humidity_pct",
    "vibration_g",
    "acoustic_db",
    "air_pressure_kpa",
    "co2_ppm",
)


class Detector:
    def __init__(self) -> None:
        self.hist: dict[str, deque[np.ndarray]] = defaultdict(lambda: deque(maxlen=360))
        self.recent_z: dict[str, deque[np.ndarray]] = defaultdict(lambda: deque(maxlen=6))
        self.cached_stats: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        self.steps: dict[str, int] = defaultdict(int)

    def _get_stats(self, zone: str) -> tuple[np.ndarray, np.ndarray]:
        arr = np.array(self.hist[zone], dtype=np.float64)
        med = np.median(arr, axis=0)
        mad = np.median(np.abs(arr - med), axis=0) * 1.4826
        std = np.std(arr, axis=0)
        sd = np.maximum(np.maximum(mad, std * 0.75), 1e-4)
        return med, sd

    def update(self, reading: dict) -> float:
        zone = str(reading.get("bunker_zone", "default"))
        vals = []
        for s in SENSORS:
            v = reading.get(s)
            if v is None or (isinstance(v, float) and math.isnan(v)):
                vals.append(float("nan"))
            else:
                vals.append(float(v))
        x = np.array(vals, dtype=np.float64)

        self.steps[zone] += 1

        # Handle NaNs safely if any sensor reading is missing
        if np.isnan(x).any():
            if zone in self.cached_stats:
                med, _ = self.cached_stats[zone]
                x = np.where(np.isnan(x), med, x)
            else:
                x = np.where(np.isnan(x), 0.0, x)

        if len(self.hist[zone]) < 20:
            self.hist[zone].append(x)
            return 0.0

        if zone not in self.cached_stats or self.steps[zone] % 10 == 0:
            self.cached_stats[zone] = self._get_stats(zone)
        med, sd = self.cached_stats[zone]

        z = np.abs(x - med) / sd
        max_z = float(np.max(z))
        l2_z = float(np.sqrt(np.sum(np.minimum(z, 8.0) ** 2)))

        self.recent_z[zone].append(z)
        rz = np.mean(self.recent_z[zone], axis=0)
        max_rz = float(np.max(rz))
        l2_rz = float(np.sqrt(np.sum(np.minimum(rz, 8.0) ** 2)))

        # 1. Point anomaly (sudden isolated spike)
        s_point = max(0.0, (max_z - 3.6) / 2.8)
        # 2. Instantaneous multi-sensor shift
        s_coll = max(0.0, (l2_z - 4.3) / 3.0)
        # 3. Gradual drift or persistent collective anomaly
        if max_z >= 2.2 or l2_z >= 3.3:
            s_drift = max((max_rz - 2.3) / 1.8, (l2_rz - 3.3) / 2.2)
        else:
            s_drift = 0.0

        score = float(np.clip(max(s_point, s_coll, s_drift), 0.0, 1.0))

        # Update normal history only with non-anomalous points so drifts cannot poison baseline
        if score < 0.42:
            self.hist[zone].append(x)

        return score