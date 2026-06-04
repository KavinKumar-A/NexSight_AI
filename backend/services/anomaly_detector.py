"""
NexSight AI - Real-Time Anomaly Detection Engine (UNIQUE FEATURE)
Uses Isolation Forest and statistical methods to detect unusual patterns
in manufacturing data streams in real-time.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from backend.config import THRESHOLDS

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import DBSCAN
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class AnomalyDetector:
    """
    Multi-method anomaly detection system:
    1. Isolation Forest for multivariate anomalies
    2. Statistical Z-score for univariate outliers
    3. DBSCAN for cluster-based anomalies
    4. Rate-of-change detection for sudden shifts
    """

    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.sensor_cols = [
            "temperature_c", "vibration_mm_s", "humidity_pct",
            "pressure_bar", "speed_units_hr", "calibration_offset",
            "power_consumption_kw"
        ]
        self.iso_forest = None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None

    def detect_all_anomalies(self) -> Dict:
        """Run all anomaly detection methods and combine results."""
        results = {
            "isolation_forest": self._isolation_forest_detection(),
            "statistical": self._statistical_detection(),
            "rate_of_change": self._rate_of_change_detection(),
            "summary": {},
        }

        # Combine anomaly flags
        total_anomalies = 0
        anomaly_details = []

        for method, detections in results.items():
            if method == "summary":
                continue
            if isinstance(detections, dict) and "anomalies" in detections:
                total_anomalies += detections.get("count", 0)
                anomaly_details.extend(detections.get("anomalies", []))

        results["summary"] = {
            "total_anomalies_detected": total_anomalies,
            "anomaly_rate_pct": round(total_anomalies / max(len(self.data), 1) * 100, 2),
            "timestamp": datetime.now().isoformat(),
            "methods_used": ["Isolation Forest", "Statistical Z-Score", "Rate-of-Change"],
            "top_anomalies": sorted(anomaly_details, key=lambda x: x.get("severity_score", 0), reverse=True)[:10],
        }

        return results

    def _isolation_forest_detection(self) -> Dict:
        """Detect multivariate anomalies using Isolation Forest."""
        if not SKLEARN_AVAILABLE:
            return {"count": 0, "anomalies": [], "error": "sklearn not available"}

        available_cols = [c for c in self.sensor_cols if c in self.data.columns]
        X = self.data[available_cols].fillna(0)
        X_scaled = self.scaler.fit_transform(X)

        self.iso_forest = IsolationForest(
            contamination=0.05,  # expect ~5% anomalies
            random_state=42,
            n_estimators=100,
        )
        predictions = self.iso_forest.fit_predict(X_scaled)
        scores = self.iso_forest.decision_function(X_scaled)

        anomaly_mask = predictions == -1
        anomaly_indices = np.where(anomaly_mask)[0]

        anomalies = []
        for idx in anomaly_indices[:50]:  # limit output
            row = self.data.iloc[idx]
            anomalies.append({
                "index": int(idx),
                "timestamp": str(row.get("timestamp", "")),
                "machine_id": str(row.get("machine_id", "")),
                "anomaly_score": round(float(-scores[idx]), 4),
                "severity_score": round(float(-scores[idx]) * 100, 1),
                "type": "multivariate",
                "description": self._describe_anomaly(row, available_cols, X),
            })

        return {
            "count": int(anomaly_mask.sum()),
            "anomaly_rate": round(float(anomaly_mask.mean()) * 100, 2),
            "anomalies": anomalies,
        }

    def _statistical_detection(self) -> Dict:
        """Detect univariate outliers using Z-score method."""
        anomalies = []
        total_count = 0

        available_cols = [c for c in self.sensor_cols if c in self.data.columns]

        for col in available_cols:
            mean = self.data[col].mean()
            std = self.data[col].std()

            if std == 0:
                continue

            z_scores = np.abs((self.data[col] - mean) / std)
            outlier_mask = z_scores > 3.0
            outlier_indices = np.where(outlier_mask)[0]
            total_count += len(outlier_indices)

            for idx in outlier_indices[:10]:
                row = self.data.iloc[idx]
                anomalies.append({
                    "index": int(idx),
                    "timestamp": str(row.get("timestamp", "")),
                    "machine_id": str(row.get("machine_id", "")),
                    "anomaly_score": round(float(z_scores.iloc[idx]), 3),
                    "severity_score": round(float(z_scores.iloc[idx]) * 25, 1),
                    "type": "univariate",
                    "description": f"{col}: {row[col]:.2f} (z-score: {z_scores.iloc[idx]:.2f}, "
                                   f"mean: {mean:.2f}, std: {std:.2f})",
                })

        return {
            "count": total_count,
            "anomalies": anomalies,
        }

    def _rate_of_change_detection(self) -> Dict:
        """Detect sudden changes in sensor readings."""
        anomalies = []
        total_count = 0

        available_cols = [c for c in self.sensor_cols if c in self.data.columns]

        for machine_id in self.data["machine_id"].unique():
            machine_data = self.data[self.data["machine_id"] == machine_id].copy()

            for col in available_cols:
                if col not in machine_data.columns:
                    continue

                # Calculate rate of change
                diff = machine_data[col].diff().abs()
                threshold = diff.mean() + 3 * diff.std()

                if threshold == 0:
                    continue

                spikes = machine_data[diff > threshold]
                total_count += len(spikes)

                for idx in spikes.index[:5]:
                    row = self.data.loc[idx]
                    anomalies.append({
                        "index": int(idx),
                        "timestamp": str(row.get("timestamp", "")),
                        "machine_id": machine_id,
                        "anomaly_score": round(float(diff.loc[idx] / max(threshold, 0.01)), 3),
                        "severity_score": round(float(diff.loc[idx] / max(threshold, 0.01)) * 30, 1),
                        "type": "rate_of_change",
                        "description": f"Sudden change in {col} on {machine_id}: "
                                       f"Δ={diff.loc[idx]:.2f} (threshold: {threshold:.2f})",
                    })

        return {
            "count": total_count,
            "anomalies": anomalies,
        }

    def _describe_anomaly(self, row: pd.Series, cols: List[str], X: pd.DataFrame) -> str:
        """Generate human-readable description of an anomaly."""
        deviations = []
        for col in cols:
            if col in row.index:
                mean = X[col].mean()
                std = X[col].std()
                if std > 0:
                    z = abs((row[col] - mean) / std)
                    if z > 2:
                        direction = "high" if row[col] > mean else "low"
                        deviations.append(f"{col}={row[col]:.2f} ({direction}, z={z:.1f})")

        if deviations:
            return f"Unusual combination: {', '.join(deviations[:3])}"
        return "Multi-dimensional outlier detected"

    def get_anomaly_summary(self) -> Dict:
        """Quick anomaly summary for dashboard."""
        available_cols = [c for c in self.sensor_cols if c in self.data.columns]

        summary = {
            "total_records": len(self.data),
            "flagged_anomalies": int(self.data.get("is_anomaly", pd.Series([0])).sum()),
            "anomaly_rate_pct": round(
                float(self.data.get("is_anomaly", pd.Series([0])).mean()) * 100, 2
            ),
            "per_machine": {},
            "per_sensor_breaches": {},
        }

        # Per machine
        for machine_id in self.data["machine_id"].unique():
            m_data = self.data[self.data["machine_id"] == machine_id]
            summary["per_machine"][machine_id] = {
                "anomaly_count": int(m_data.get("is_anomaly", pd.Series([0])).sum()),
                "anomaly_rate": round(float(m_data.get("is_anomaly", pd.Series([0])).mean()) * 100, 1),
            }

        # Per sensor threshold breaches
        breach_checks = {
            "temperature_c": ("Temperature", THRESHOLDS["temperature_high"]),
            "vibration_mm_s": ("Vibration", THRESHOLDS["vibration_high"]),
            "humidity_pct": ("Humidity", THRESHOLDS["humidity_high"]),
        }
        for col, (name, thresh) in breach_checks.items():
            if col in self.data.columns:
                count = int((self.data[col] > thresh).sum())
                summary["per_sensor_breaches"][name] = {
                    "count": count,
                    "rate_pct": round(count / len(self.data) * 100, 2),
                    "threshold": thresh,
                }

        return summary
