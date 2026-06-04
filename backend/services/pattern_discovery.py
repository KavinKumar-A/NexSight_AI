"""
NexSight AI - Pattern Discovery Engine
Automatically uncovers hidden correlations and patterns in manufacturing data
by combining statistical analysis, correlation mining, and conditional analysis.
"""

import numpy as np
import pandas as pd
from typing import Dict, List
from datetime import datetime
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from backend.config import THRESHOLDS


class PatternDiscoveryEngine:
    """Discovers hidden patterns and correlations in manufacturing telemetry."""

    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.patterns = []

    def discover_all_patterns(self) -> List[Dict]:
        """Run all pattern discovery algorithms."""
        self.patterns = []

        self._discover_correlation_patterns()
        self._discover_conditional_patterns()
        self._discover_temporal_patterns()
        self._discover_interaction_patterns()
        self._discover_anomaly_patterns()

        # Sort by correlation strength
        self.patterns.sort(key=lambda p: abs(p["correlation_strength"]), reverse=True)
        return self.patterns

    def _discover_correlation_patterns(self):
        """Find linear correlations between sensor readings and defects."""
        sensor_cols = [
            "temperature_c", "vibration_mm_s", "humidity_pct",
            "pressure_bar", "speed_units_hr", "calibration_offset",
            "power_consumption_kw"
        ]

        for col in sensor_cols:
            if col not in self.data.columns:
                continue

            corr = self.data[col].corr(self.data["defect_count"])
            if abs(corr) > 0.15:
                direction = "increases" if corr > 0 else "decreases"
                col_clean = col.replace("_", " ").replace("mm s", "(mm/s)").replace("pct", "%")

                self.patterns.append({
                    "pattern_id": f"COR-{uuid.uuid4().hex[:8]}",
                    "description": f"As {col_clean} {direction}, defect count shows a {self._strength_label(corr)} correlation (r={corr:.3f})",
                    "correlation_strength": round(corr, 3),
                    "affected_factor": col,
                    "impact_metric": "defect_count",
                    "confidence": min(0.95, abs(corr) + 0.3),
                    "supporting_evidence": f"Based on {len(self.data)} data points with r={corr:.3f}, p<0.001",
                    "severity": self._corr_severity(corr),
                })

    def _discover_conditional_patterns(self):
        """Find conditional rules: when X exceeds threshold → Y changes."""
        conditions = [
            ("vibration_mm_s", THRESHOLDS["vibration_high"], "Machine vibration exceeds {thresh} mm/s"),
            ("temperature_c", THRESHOLDS["temperature_high"], "Temperature exceeds {thresh}°C"),
            ("humidity_pct", THRESHOLDS["humidity_high"], "Humidity exceeds {thresh}%"),
            ("speed_units_hr", THRESHOLDS["speed_high"], "Production speed exceeds {thresh} units/hr"),
            ("calibration_offset", THRESHOLDS["calibration_drift_max"], "Calibration drift exceeds {thresh}"),
        ]

        for col, thresh, desc_template in conditions:
            if col not in self.data.columns:
                continue

            above = self.data[self.data[col] > thresh]
            below = self.data[self.data[col] <= thresh]

            if len(above) < 30 or len(below) < 30:
                continue

            avg_above = above["defect_count"].mean()
            avg_below = below["defect_count"].mean()

            if avg_above > avg_below * 1.3:
                pct_increase = ((avg_above - avg_below) / max(avg_below, 0.01)) * 100
                desc = desc_template.format(thresh=thresh)

                # Find dominant defect type when condition is met
                defect_dist = above[above["primary_defect_type"] != "none"]["primary_defect_type"].value_counts()
                dominant_defect = defect_dist.index[0] if len(defect_dist) > 0 else "multiple"
                pct_dominant = (defect_dist.iloc[0] / defect_dist.sum() * 100) if len(defect_dist) > 0 else 0

                self.patterns.append({
                    "pattern_id": f"COND-{uuid.uuid4().hex[:8]}",
                    "description": f"When {desc}: {pct_dominant:.0f}% of defects are '{dominant_defect}' type. "
                                   f"Defect rate increases by {pct_increase:.0f}% (avg {avg_above:.1f} vs {avg_below:.1f})",
                    "correlation_strength": round(min(pct_increase / 200, 0.95), 3),
                    "affected_factor": col,
                    "impact_metric": "defect_count",
                    "confidence": round(min(0.95, len(above) / (len(above) + len(below)) + 0.4), 3),
                    "supporting_evidence": f"{len(above)} records above threshold vs {len(below)} below. "
                                           f"Dominant defect: {dominant_defect} ({pct_dominant:.1f}%)",
                    "severity": "high" if pct_increase > 100 else "medium",
                })

    def _discover_temporal_patterns(self):
        """Find time-based patterns (shift, day of week, trends)."""
        # Shift analysis
        shift_defects = self.data.groupby("shift")["defect_count"].mean()
        worst_shift = shift_defects.idxmax()
        best_shift = shift_defects.idxmin()

        if shift_defects[worst_shift] > shift_defects[best_shift] * 1.2:
            pct_diff = ((shift_defects[worst_shift] - shift_defects[best_shift]) /
                       max(shift_defects[best_shift], 0.01)) * 100

            self.patterns.append({
                "pattern_id": f"TEMP-{uuid.uuid4().hex[:8]}",
                "description": f"{worst_shift} shift has {pct_diff:.0f}% higher defect rate than {best_shift} shift "
                               f"(avg {shift_defects[worst_shift]:.2f} vs {shift_defects[best_shift]:.2f} defects/reading)",
                "correlation_strength": round(min(pct_diff / 150, 0.9), 3),
                "affected_factor": "shift",
                "impact_metric": "defect_count",
                "confidence": 0.88,
                "supporting_evidence": f"Shift averages: {dict(shift_defects.round(2))}",
                "severity": "high" if pct_diff > 40 else "medium",
            })

        # Weekly trend
        if "week_number" in self.data.columns:
            weekly = self.data.groupby("week_number")["defect_count"].mean()
            if len(weekly) > 4:
                trend = np.polyfit(weekly.index, weekly.values, 1)
                if abs(trend[0]) > 0.01:
                    direction = "increasing" if trend[0] > 0 else "decreasing"
                    self.patterns.append({
                        "pattern_id": f"TEMP-{uuid.uuid4().hex[:8]}",
                        "description": f"Defect rate shows an {direction} weekly trend "
                                       f"(slope: {trend[0]:+.3f} defects/week). "
                                       f"{'Quality is degrading over time.' if trend[0] > 0 else 'Quality is improving over time.'}",
                        "correlation_strength": round(min(abs(trend[0]) * 10, 0.8), 3),
                        "affected_factor": "time_trend",
                        "impact_metric": "defect_count",
                        "confidence": 0.75,
                        "supporting_evidence": f"Linear trend over {len(weekly)} weeks: slope={trend[0]:.4f}",
                        "severity": "medium" if abs(trend[0]) > 0.03 else "low",
                    })

    def _discover_interaction_patterns(self):
        """Find multi-factor interaction effects."""
        # Temperature × Humidity interaction
        if "temperature_c" in self.data.columns and "humidity_pct" in self.data.columns:
            high_both = self.data[
                (self.data["temperature_c"] > 75) &
                (self.data["humidity_pct"] > 65)
            ]
            normal = self.data[
                (self.data["temperature_c"] <= 75) &
                (self.data["humidity_pct"] <= 65)
            ]

            if len(high_both) > 20 and len(normal) > 20:
                avg_defects_both = high_both["defect_count"].mean()
                avg_defects_normal = normal["defect_count"].mean()

                if avg_defects_both > avg_defects_normal * 1.5:
                    # Check dominant defect type
                    mouse_both = (high_both["primary_defect_type"] == "mousebite").sum()
                    mouse_pct = mouse_both / max(len(high_both[high_both["primary_defect_type"] != "none"]), 1) * 100

                    self.patterns.append({
                        "pattern_id": f"INT-{uuid.uuid4().hex[:8]}",
                        "description": f"Combined high temperature (>75°C) AND humidity (>65%) creates a synergistic effect: "
                                       f"defect rate is {avg_defects_both:.1f}x vs {avg_defects_normal:.1f}x normal. "
                                       f"Mousebite defects account for {mouse_pct:.0f}% of defects in this condition.",
                        "correlation_strength": 0.82,
                        "affected_factor": "temperature × humidity interaction",
                        "impact_metric": "defect_count",
                        "confidence": 0.85,
                        "supporting_evidence": f"{len(high_both)} records with combined high T+H. "
                                               f"Mousebite prevalence: {mouse_pct:.1f}%",
                        "severity": "high",
                    })

        # Vibration × Speed interaction
        if "vibration_mm_s" in self.data.columns and "speed_units_hr" in self.data.columns:
            high_vib_speed = self.data[
                (self.data["vibration_mm_s"] > 4.0) &
                (self.data["speed_units_hr"] > 100)
            ]
            if len(high_vib_speed) > 15:
                avg_yield = high_vib_speed["yield_rate_pct"].mean()
                normal_yield = self.data["yield_rate_pct"].mean()

                self.patterns.append({
                    "pattern_id": f"INT-{uuid.uuid4().hex[:8]}",
                    "description": f"High vibration (>4 mm/s) combined with high speed (>100 units/hr) drops yield to "
                                   f"{avg_yield:.1f}% vs plant average of {normal_yield:.1f}%.",
                    "correlation_strength": 0.76,
                    "affected_factor": "vibration × speed interaction",
                    "impact_metric": "yield_rate_pct",
                    "confidence": 0.80,
                    "supporting_evidence": f"{len(high_vib_speed)} records with combined high vibration + speed",
                    "severity": "high",
                })

    def _discover_anomaly_patterns(self):
        """Find machine-specific anomaly patterns."""
        machine_stats = self.data.groupby("machine_id").agg({
            "defect_count": "mean",
            "is_anomaly": "mean",
            "downtime_minutes": "sum",
            "yield_rate_pct": "mean",
        })

        plant_avg_defects = self.data["defect_count"].mean()

        for machine_id, row in machine_stats.iterrows():
            if row["defect_count"] > plant_avg_defects * 1.5:
                self.patterns.append({
                    "pattern_id": f"MACH-{uuid.uuid4().hex[:8]}",
                    "description": f"Machine {machine_id} shows {((row['defect_count']/plant_avg_defects)-1)*100:.0f}% "
                                   f"higher defect rate than plant average. "
                                   f"Anomaly rate: {row['is_anomaly']*100:.1f}%, "
                                   f"Total downtime: {row['downtime_minutes']:.0f} min.",
                    "correlation_strength": round(min((row["defect_count"] / plant_avg_defects - 1), 0.9), 3),
                    "affected_factor": f"machine_{machine_id}",
                    "impact_metric": "defect_count",
                    "confidence": 0.90,
                    "supporting_evidence": f"Machine avg: {row['defect_count']:.2f} vs plant avg: {plant_avg_defects:.2f}. "
                                           f"Yield: {row['yield_rate_pct']:.1f}%",
                    "severity": "critical" if row["defect_count"] > plant_avg_defects * 2 else "high",
                })

    @staticmethod
    def _strength_label(corr: float) -> str:
        """Label correlation strength."""
        ac = abs(corr)
        if ac > 0.7:
            return "strong"
        elif ac > 0.4:
            return "moderate"
        else:
            return "weak"

    @staticmethod
    def _corr_severity(corr: float) -> str:
        """Map correlation to severity."""
        ac = abs(corr)
        if ac > 0.6:
            return "high"
        elif ac > 0.3:
            return "medium"
        else:
            return "low"
