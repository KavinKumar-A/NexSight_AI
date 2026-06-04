"""
NexSight AI — Manufacturing Health Score Engine
Composite score (0-100) using relative-to-baseline scoring so that
a factory with synthetic embedded anomalies realistically scores B/C grade.
"""

import numpy as np
import pandas as pd
from typing import Dict, List
from datetime import datetime
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from backend.config import THRESHOLDS, HEALTH_WEIGHTS


def _relative_score(value: float, baseline: float,
                    at_zero: float = 100.0,
                    at_baseline: float = 80.0,
                    at_2x: float = 50.0) -> float:
    """
    Piecewise-linear relative scorer:
      value=0         → at_zero   (100)
      value=baseline  → at_baseline (80)
      value=2×baseline→ at_2x     (50)
      value>2×baseline→ continues linearly down, floor at 0
    Lower is worse (higher value = lower score).
    """
    if baseline <= 0:
        baseline = 1e-9
    if value <= 0:
        return at_zero
    if value <= baseline:
        t = value / baseline          # 0 → 1
        return at_zero + (at_baseline - at_zero) * t
    else:
        t = (value - baseline) / baseline   # 0 → 1 over [baseline, 2×baseline]
        return max(0.0, at_baseline + (at_2x - at_baseline) * t)


class HealthScoreEngine:
    """
    Composite Manufacturing Health Score (0-100).

    All components use *relative* scoring against the dataset-wide baseline
    so that a factory running at its own average performance scores ≈ 80 (Grade B).
    Unusual deterioration pushes the score toward C/D/F.

    Grade thresholds:
      A+ (95-100)  A (90-94)  B (80-89)  C (70-79)  D (60-69)  F (<60)
    """

    def __init__(self, data: pd.DataFrame):
        self.data = data
        # Compute dataset-wide baselines once
        self._base_defects  = float(data["defect_count"].mean())
        self._base_anomaly  = float(data["is_anomaly"].mean())
        self._base_cal      = float(data["calibration_offset"].mean())
        self._base_yield    = float(data["yield_rate_pct"].mean())
        self._base_downtime = float(data["downtime_minutes"].mean())

    # ─────────────────────────────────────────────────────────────
    def compute_health_score(self, window_hours: int = 24) -> Dict:
        recent = self._resolve_window(window_hours)

        components = []

        # ── 1. Defect Rate (weight 0.30) ──────────────────────
        avg_def   = float(recent["defect_count"].mean())
        def_score = _relative_score(avg_def, self._base_defects)
        def_score = float(np.clip(def_score, 0, 100))
        components.append({
            "component": "Defect Rate",
            "score":     round(def_score, 1),
            "weight":    HEALTH_WEIGHTS["defect_rate"],
            "status":    self._status(def_score),
            "details":   (f"Avg {avg_def:.2f} defects/reading "
                          f"(baseline {self._base_defects:.2f}). "
                          f"{'On target.' if def_score >= 75 else 'Action needed.'}"),
        })

        # ── 2. Machine Condition (weight 0.25) ─────────────────
        an_rate  = float(recent["is_anomaly"].mean())
        avg_vib  = float(recent["vibration_mm_s"].mean())
        an_score = _relative_score(an_rate, max(self._base_anomaly, 0.05))
        # Vibration penalty only above 80% of threshold
        vib_threshold = THRESHOLDS["vibration_high"]
        vib_ratio     = avg_vib / vib_threshold
        vib_penalty   = max(0.0, (vib_ratio - 0.80) * 30.0)
        mach_score    = float(np.clip(an_score - vib_penalty, 0, 100))
        components.append({
            "component": "Machine Condition",
            "score":     round(mach_score, 1),
            "weight":    HEALTH_WEIGHTS["machine_condition"],
            "status":    self._status(mach_score),
            "details":   (f"Anomaly rate {an_rate*100:.1f}% "
                          f"(baseline {self._base_anomaly*100:.1f}%). "
                          f"Avg vibration {avg_vib:.2f} mm/s."),
        })

        # ── 3. Environmental (weight 0.20) ─────────────────────
        temp_br  = float((recent["temperature_c"]  > THRESHOLDS["temperature_high"]).mean())
        humid_br = float((recent["humidity_pct"]   > THRESHOLDS["humidity_high"]).mean())
        # Gentle penalty: at 5% breach → ~95 pts; at 20% → ~80 pts; at 40% → ~60 pts
        env_score = float(np.clip(100 - temp_br * 100 - humid_br * 60, 0, 100))
        components.append({
            "component": "Environmental",
            "score":     round(env_score, 1),
            "weight":    HEALTH_WEIGHTS["environmental"],
            "status":    self._status(env_score),
            "details":   (f"Temp breaches {temp_br*100:.1f}%, "
                          f"humidity breaches {humid_br*100:.1f}%."),
        })

        # ── 4. Throughput / Yield (weight 0.15) ────────────────
        avg_yield = float(recent["yield_rate_pct"].mean())
        avg_down  = float(recent["downtime_minutes"].mean())
        # Yield: at baseline → 80, at 0 → 0, at 100 → 100
        # Downtime: small penalty above baseline
        yield_pts  = _relative_score(
            self._base_yield - avg_yield,   # invert: higher yield = lower "value"
            max(100 - self._base_yield, 1.0),
            at_zero=100, at_baseline=80, at_2x=60,
        )
        # Remap: yield ≥ target → 100; proportional below
        yield_pts = float(np.clip((avg_yield / max(self._base_yield, 1)) * 85, 0, 100))
        down_pts  = _relative_score(avg_down, max(self._base_downtime, 1.0))
        thru_score = float(np.clip((yield_pts * 0.7 + down_pts * 0.3), 0, 100))
        components.append({
            "component": "Throughput",
            "score":     round(thru_score, 1),
            "weight":    HEALTH_WEIGHTS["throughput"],
            "status":    self._status(thru_score),
            "details":   (f"Avg yield {avg_yield:.1f}% "
                          f"(baseline {self._base_yield:.1f}%). "
                          f"Avg downtime {avg_down:.1f} min/reading."),
        })

        # ── 5. Calibration (weight 0.10) ────────────────────────
        avg_cal  = float(recent["calibration_offset"].mean())
        cal_score = _relative_score(avg_cal, max(self._base_cal, 0.01))
        cal_score = float(np.clip(cal_score, 0, 100))
        components.append({
            "component": "Calibration",
            "score":     round(cal_score, 1),
            "weight":    HEALTH_WEIGHTS["calibration"],
            "status":    self._status(cal_score),
            "details":   (f"Avg drift {avg_cal:.4f} "
                          f"(baseline {self._base_cal:.4f}, "
                          f"tolerance {THRESHOLDS['calibration_drift_max']}). "
                          f"{'In spec.' if cal_score >= 70 else 'Recalibration needed.'}"),
        })

        # ── Weighted composite ─────────────────────────────────
        overall = round(float(np.clip(
            sum(c["score"] * c["weight"] for c in components), 0, 100
        )), 1)

        return {
            "overall_score": overall,
            "grade":         self._grade(overall),
            "components":    components,
            "trend":         self._trend(),
            "timestamp":     datetime.now().isoformat(),
            "data_window":   f"Last {window_hours}h ({len(recent)} readings)",
        }

    def compute_machine_health(self) -> List[Dict]:
        results = []
        for mid in self.data["machine_id"].unique():
            eng = HealthScoreEngine(self.data[self.data["machine_id"] == mid])
            s = eng.compute_health_score()
            s["machine_id"] = mid
            results.append(s)
        return sorted(results, key=lambda x: x["overall_score"])

    # ─────────────────────────────────────────────────────────────
    def _resolve_window(self, window_hours: int) -> pd.DataFrame:
        """Return a representative window; fall back to full dataset if too small."""
        if "timestamp" in self.data.columns:
            self.data["timestamp"] = pd.to_datetime(self.data["timestamp"])
            latest = self.data["timestamp"].max()
            cutoff = latest - pd.Timedelta(hours=window_hours)
            recent = self.data[self.data["timestamp"] >= cutoff]
        else:
            recent = self.data.tail(min(500, len(self.data)))

        # Too few samples → use full dataset for a stable representative score
        if len(recent) < 200:
            return self.data
        return recent

    def _trend(self) -> str:
        if "week_number" not in self.data.columns or len(self.data) < 100:
            return "stable"
        wy = self.data.groupby("week_number")["yield_rate_pct"].mean()
        if len(wy) < 3:
            return "stable"
        recent_avg = wy.tail(3).mean()
        old_avg    = wy.head(max(3, len(wy) // 2)).mean()
        if recent_avg > old_avg + 0.5:
            return "improving"
        if recent_avg < old_avg - 0.5:
            return "declining"
        return "stable"

    @staticmethod
    def _status(score: float) -> str:
        if score >= 80: return "healthy"
        if score >= 60: return "warning"
        return "critical"

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 95: return "A+"
        if score >= 90: return "A"
        if score >= 80: return "B"
        if score >= 70: return "C"
        if score >= 60: return "D"
        return "F"
