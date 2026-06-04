"""
NexSight AI - Automated Recommendation Engine
Translates discovered patterns and root causes into actionable
corrective actions with priority ranking and impact estimation.
"""

import numpy as np
import pandas as pd
from typing import Dict, List
from datetime import datetime
import uuid
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from backend.config import THRESHOLDS


class RecommendationEngine:
    """
    Generates intelligent, context-aware recommendations based on:
    - Pattern discovery findings
    - Root cause analysis results
    - Current machine conditions
    - Historical performance data
    """

    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.recommendations = []

    def generate_all_recommendations(
        self,
        patterns: List[Dict] = None,
        root_causes: Dict = None,
    ) -> List[Dict]:
        """Generate comprehensive recommendations from all sources."""
        self.recommendations = []

        self._generate_threshold_recommendations()
        self._generate_machine_recommendations()
        self._generate_shift_recommendations()
        self._generate_calibration_recommendations()
        self._generate_environmental_recommendations()

        if patterns:
            self._generate_pattern_recommendations(patterns)
        if root_causes:
            self._generate_root_cause_recommendations(root_causes)

        # Deduplicate and sort by priority
        seen = set()
        unique = []
        for rec in self.recommendations:
            key = rec["title"]
            if key not in seen:
                seen.add(key)
                unique.append(rec)

        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        unique.sort(key=lambda r: priority_order.get(r["priority"], 3))

        return unique

    def _generate_threshold_recommendations(self):
        """Recommendations based on current threshold breaches."""
        # Vibration
        high_vib = self.data[self.data["vibration_mm_s"] > THRESHOLDS["vibration_high"]]
        if len(high_vib) > 0:
            affected_machines = high_vib["machine_id"].value_counts()
            worst_machine = affected_machines.index[0]
            self.recommendations.append({
                "rec_id": f"REC-{uuid.uuid4().hex[:8]}",
                "title": f"Reduce Vibration on Machine {worst_machine}",
                "description": f"Machine {worst_machine} has {affected_machines.iloc[0]} readings exceeding "
                               f"the {THRESHOLDS['vibration_high']} mm/s vibration threshold. "
                               f"Excessive vibration is the leading cause of soldering defects. "
                               f"Inspect bearings, check belt tension, and verify mounting bolts.",
                "priority": "critical",
                "category": "maintenance",
                "estimated_impact": "Reduce soldering defects by ~35-40%",
                "machine_id": worst_machine,
                "auto_applicable": False,
            })

        # Temperature
        high_temp = self.data[self.data["temperature_c"] > THRESHOLDS["temperature_high"]]
        if len(high_temp) > 0:
            pct_affected = len(high_temp) / len(self.data) * 100
            self.recommendations.append({
                "rec_id": f"REC-{uuid.uuid4().hex[:8]}",
                "title": "Improve Thermal Management System",
                "description": f"{pct_affected:.1f}% of readings show temperature above "
                               f"{THRESHOLDS['temperature_high']}°C. "
                               f"Check cooling system capacity, clean heat exchangers, "
                               f"and verify HVAC setpoints in production area.",
                "priority": "high",
                "category": "environment",
                "estimated_impact": "Reduce temperature-related defects by ~25-30%",
                "machine_id": None,
                "auto_applicable": False,
            })

    def _generate_machine_recommendations(self):
        """Machine-specific recommendations."""
        machine_stats = self.data.groupby("machine_id").agg({
            "defect_count": "mean",
            "yield_rate_pct": "mean",
            "downtime_minutes": "sum",
            "is_anomaly": "mean",
        })

        plant_avg = self.data["defect_count"].mean()

        for machine_id, stats in machine_stats.iterrows():
            if stats["defect_count"] > plant_avg * 1.8:
                self.recommendations.append({
                    "rec_id": f"REC-{uuid.uuid4().hex[:8]}",
                    "title": f"Schedule Deep Maintenance for Machine {machine_id}",
                    "description": f"Machine {machine_id} averages {stats['defect_count']:.1f} defects/reading "
                                   f"({((stats['defect_count']/plant_avg)-1)*100:.0f}% above plant average). "
                                   f"Yield: {stats['yield_rate_pct']:.1f}%. "
                                   f"Total downtime: {stats['downtime_minutes']:.0f} min. "
                                   f"A comprehensive overhaul is recommended.",
                    "priority": "critical" if stats["defect_count"] > plant_avg * 2.5 else "high",
                    "category": "maintenance",
                    "estimated_impact": f"Potential yield improvement of {(stats['yield_rate_pct'] - self.data['yield_rate_pct'].mean()) * -1:.1f}%",
                    "machine_id": machine_id,
                    "auto_applicable": False,
                })

            if stats["is_anomaly"] > 0.25:
                self.recommendations.append({
                    "rec_id": f"REC-{uuid.uuid4().hex[:8]}",
                    "title": f"Investigate Anomaly Patterns on Machine {machine_id}",
                    "description": f"Machine {machine_id} shows {stats['is_anomaly']*100:.1f}% anomaly rate. "
                                   f"This indicates potential systematic issues. "
                                   f"Review sensor calibration, inspect wear components, "
                                   f"and check control system parameters.",
                    "priority": "high",
                    "category": "maintenance",
                    "estimated_impact": "Reduce anomaly incidents by ~50%",
                    "machine_id": machine_id,
                    "auto_applicable": False,
                })

    def _generate_shift_recommendations(self):
        """Shift-based recommendations."""
        shift_stats = self.data.groupby("shift")["defect_count"].mean()

        if "Night" in shift_stats.index:
            night_avg = shift_stats["Night"]
            day_avg = shift_stats.drop("Night").mean()

            if night_avg > day_avg * 1.3:
                self.recommendations.append({
                    "rec_id": f"REC-{uuid.uuid4().hex[:8]}",
                    "title": "Enhance Night Shift Quality Controls",
                    "description": f"Night shift has {((night_avg/day_avg)-1)*100:.0f}% higher defect rate "
                                   f"(avg {night_avg:.2f} vs {day_avg:.2f}). "
                                   f"Consider: adding a quality inspector, "
                                   f"implementing more frequent inline checks, "
                                   f"reducing production speed by 10-15%, "
                                   f"and improving lighting conditions.",
                    "priority": "high",
                    "category": "process",
                    "estimated_impact": "Reduce night shift defect gap by ~40%",
                    "machine_id": None,
                    "auto_applicable": True,
                })

    def _generate_calibration_recommendations(self):
        """Calibration drift recommendations."""
        high_cal = self.data[
            self.data["calibration_offset"] > THRESHOLDS["calibration_drift_max"]
        ]

        if len(high_cal) > 0:
            affected_machines = high_cal["machine_id"].unique()
            self.recommendations.append({
                "rec_id": f"REC-{uuid.uuid4().hex[:8]}",
                "title": f"Recalibrate Machines: {', '.join(affected_machines[:4])}",
                "description": f"{len(affected_machines)} machines show calibration drift beyond "
                               f"{THRESHOLDS['calibration_drift_max']} tolerance. "
                               f"Calibration drift progressively degrades placement accuracy. "
                               f"Schedule immediate recalibration for all affected machines.",
                "priority": "critical",
                "category": "calibration",
                "estimated_impact": "Prevent ~20% of pinhole and placement defects",
                "machine_id": affected_machines[0] if len(affected_machines) == 1 else None,
                "auto_applicable": False,
            })

    def _generate_environmental_recommendations(self):
        """Environmental factor recommendations."""
        high_humid = self.data[self.data["humidity_pct"] > THRESHOLDS["humidity_high"]]

        if len(high_humid) > len(self.data) * 0.1:
            self.recommendations.append({
                "rec_id": f"REC-{uuid.uuid4().hex[:8]}",
                "title": "Install Dehumidification System",
                "description": f"{len(high_humid)/len(self.data)*100:.1f}% of readings exceed "
                               f"the {THRESHOLDS['humidity_high']}% humidity threshold. "
                               f"High humidity causes oxidation and poor solder wetting, "
                               f"especially in combination with high temperatures. "
                               f"Consider industrial dehumidifiers or improved HVAC controls.",
                "priority": "medium",
                "category": "environment",
                "estimated_impact": "Reduce mousebite defects by ~30%",
                "machine_id": None,
                "auto_applicable": False,
            })

    def _generate_pattern_recommendations(self, patterns: List[Dict]):
        """Generate recommendations based on discovered patterns."""
        for pattern in patterns[:5]:
            if pattern.get("severity") in ["high", "critical"]:
                factor = pattern.get("affected_factor", "unknown")
                self.recommendations.append({
                    "rec_id": f"REC-{uuid.uuid4().hex[:8]}",
                    "title": f"Address Pattern: {factor.replace('_', ' ').title()}",
                    "description": f"Pattern discovered: {pattern['description'][:200]}. "
                                   f"Correlation strength: {pattern['correlation_strength']:.3f}. "
                                   f"Investigate and implement targeted countermeasures.",
                    "priority": pattern["severity"],
                    "category": "process",
                    "estimated_impact": f"Potential {abs(pattern['correlation_strength'])*30:.0f}% improvement",
                    "machine_id": None,
                    "auto_applicable": False,
                })

    def _generate_root_cause_recommendations(self, root_causes: Dict):
        """Generate recommendations based on root cause analysis."""
        factors = root_causes.get("factors", [])

        for factor in factors[:3]:
            if factor["contribution_pct"] > 15:
                self.recommendations.append({
                    "rec_id": f"REC-{uuid.uuid4().hex[:8]}",
                    "title": f"Mitigate Root Cause: {factor['factor']}",
                    "description": f"{factor['factor']} contributes {factor['contribution_pct']:.1f}% "
                                   f"to the quality issue. {factor['description']} "
                                   f"Prioritize actions targeting this factor for maximum impact.",
                    "priority": "high" if factor["contribution_pct"] > 25 else "medium",
                    "category": "process",
                    "estimated_impact": f"~{factor['contribution_pct']:.0f}% reduction in target metric",
                    "machine_id": None,
                    "auto_applicable": factor.get("actionable", True),
                })
