"""
NexSight AI - Root Cause Intelligence Engine
Identifies underlying factors contributing to quality issues using
feature importance decomposition, SHAP values, and statistical methods.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import uuid
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from backend.config import THRESHOLDS, MODELS_PATH

try:
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestRegressor
    from sklearn.inspection import permutation_importance
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False


class RootCauseEngine:
    """
    Identifies root causes of quality issues by decomposing
    contributing factors using ML feature importance and SHAP.
    """

    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.feature_cols = [
            "temperature_c", "vibration_mm_s", "humidity_pct",
            "pressure_bar", "speed_units_hr", "calibration_offset",
            "power_consumption_kw", "shift_encoded",
        ]
        self.model = None
        self.shap_values = None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None

    def analyze_root_causes(self, target: str = "defect_count") -> Dict:
        """
        Perform root cause analysis for the specified target variable.
        Returns decomposed factors with contribution percentages.
        """
        if not SKLEARN_AVAILABLE:
            return self._fallback_analysis()

        # Prepare features
        available_cols = [c for c in self.feature_cols if c in self.data.columns]
        X = self.data[available_cols].fillna(0)
        y = self.data[target]

        # Scale features
        X_scaled = pd.DataFrame(
            self.scaler.fit_transform(X),
            columns=available_cols
        )

        # Train a GBM to find feature importances
        if target == "defect_count":
            # Binarize: high defect vs normal
            y_binary = (y > y.quantile(0.75)).astype(int)
            self.model = GradientBoostingClassifier(
                n_estimators=100, max_depth=5, random_state=42
            )
            self.model.fit(X_scaled, y_binary)
        else:
            self.model = RandomForestRegressor(
                n_estimators=100, max_depth=8, random_state=42
            )
            self.model.fit(X_scaled, y)

        # Get feature importances
        importances = self.model.feature_importances_
        importance_pct = (importances / importances.sum()) * 100

        # Build root cause factors
        factors = []
        for col, pct in sorted(zip(available_cols, importance_pct),
                                key=lambda x: x[1], reverse=True):
            if pct < 2:
                continue

            factors.append({
                "factor": self._humanize_factor(col),
                "contribution_pct": round(float(pct), 1),
                "description": self._generate_factor_description(col, pct),
                "actionable": col not in ["shift_encoded"],
            })

        # SHAP analysis for detailed explanations
        shap_explanations = self._compute_shap(X_scaled, available_cols)

        overall_confidence = min(0.95, 0.5 + len(self.data) / 20000)

        return {
            "issue": f"Root causes for high {target.replace('_', ' ')}",
            "total_factors": len(factors),
            "factors": factors,
            "confidence": round(overall_confidence, 2),
            "methodology": "Gradient Boosting Feature Importance + SHAP Decomposition",
            "shap_explanations": shap_explanations,
            "model_accuracy": self._get_model_score(X_scaled, y if target != "defect_count" else (y > y.quantile(0.75)).astype(int)),
        }

    def _compute_shap(self, X: pd.DataFrame, feature_names: List[str]) -> List[Dict]:
        """Compute SHAP values for feature explanations."""
        if not SHAP_AVAILABLE or self.model is None:
            return []

        try:
            # Use a sample for speed
            sample = X.sample(min(500, len(X)), random_state=42)
            explainer = shap.TreeExplainer(self.model)
            shap_values = explainer.shap_values(sample)

            # Handle multi-output
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # positive class

            mean_abs_shap = np.abs(shap_values).mean(axis=0)

            explanations = []
            for i, col in enumerate(feature_names):
                mean_val = float(sample[col].mean())
                shap_val = float(mean_abs_shap[i])
                direction = "increases" if np.mean(shap_values[:, i]) > 0 else "decreases"

                explanations.append({
                    "feature_name": self._humanize_factor(col),
                    "shap_value": round(shap_val, 4),
                    "feature_value": round(mean_val, 3),
                    "direction": direction,
                })

            explanations.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
            return explanations

        except Exception as e:
            print(f"[WARN] SHAP computation error: {e}")
            return []

    def analyze_specific_defect_type(self, defect_type: str) -> Dict:
        """Analyze root causes for a specific defect type."""
        df = self.data.copy()
        df["target"] = (df["primary_defect_type"] == defect_type).astype(int)

        available_cols = [c for c in self.feature_cols if c in df.columns]
        X = df[available_cols].fillna(0)
        y = df["target"]

        if not SKLEARN_AVAILABLE or y.sum() < 10:
            return {
                "issue": f"Root causes for {defect_type} defects",
                "total_factors": 0,
                "factors": [],
                "confidence": 0,
                "methodology": "Insufficient data",
            }

        model = GradientBoostingClassifier(
            n_estimators=80, max_depth=4, random_state=42
        )
        X_scaled = pd.DataFrame(self.scaler.fit_transform(X), columns=available_cols)
        model.fit(X_scaled, y)

        importances = model.feature_importances_
        importance_pct = (importances / importances.sum()) * 100

        factors = []
        for col, pct in sorted(zip(available_cols, importance_pct),
                                key=lambda x: x[1], reverse=True):
            if pct < 3:
                continue
            factors.append({
                "factor": self._humanize_factor(col),
                "contribution_pct": round(float(pct), 1),
                "description": f"Contributes {pct:.1f}% to '{defect_type}' occurrence",
                "actionable": col not in ["shift_encoded"],
            })

        return {
            "issue": f"Root causes for '{defect_type}' defects",
            "total_factors": len(factors),
            "factors": factors,
            "confidence": round(min(0.90, model.score(X_scaled, y)), 2),
            "methodology": "GBM Feature Importance (type-specific)",
        }

    def _get_model_score(self, X, y) -> float:
        """Get model accuracy score."""
        try:
            return round(float(self.model.score(X, y)), 3)
        except Exception:
            return 0.0

    def _fallback_analysis(self) -> Dict:
        """Statistical fallback when sklearn is not available."""
        factors = []
        for col in self.feature_cols:
            if col in self.data.columns:
                corr = abs(self.data[col].corr(self.data["defect_count"]))
                if corr > 0.1:
                    factors.append({
                        "factor": self._humanize_factor(col),
                        "contribution_pct": round(corr * 100, 1),
                        "description": f"Correlation: {corr:.3f}",
                        "actionable": True,
                    })

        total = sum(f["contribution_pct"] for f in factors)
        for f in factors:
            f["contribution_pct"] = round(f["contribution_pct"] / max(total, 1) * 100, 1)

        return {
            "issue": "Root causes for high defect count",
            "total_factors": len(factors),
            "factors": sorted(factors, key=lambda x: x["contribution_pct"], reverse=True),
            "confidence": 0.65,
            "methodology": "Statistical Correlation Analysis (fallback)",
        }

    @staticmethod
    def _humanize_factor(col: str) -> str:
        """Convert column name to human-readable label."""
        mapping = {
            "temperature_c": "Temperature (°C)",
            "vibration_mm_s": "Vibration (mm/s)",
            "humidity_pct": "Humidity (%)",
            "pressure_bar": "Pressure (bar)",
            "speed_units_hr": "Production Speed (units/hr)",
            "calibration_offset": "Calibration Drift",
            "power_consumption_kw": "Power Consumption (kW)",
            "shift_encoded": "Work Shift",
        }
        return mapping.get(col, col.replace("_", " ").title())

    @staticmethod
    def _generate_factor_description(col: str, pct: float) -> str:
        """Generate a human-readable description for a factor."""
        descriptions = {
            "vibration_mm_s": f"Machine vibration contributes {pct:.1f}% to defect occurrence. High vibration causes mechanical misalignment during soldering.",
            "temperature_c": f"Temperature accounts for {pct:.1f}% of quality variation. Excursions beyond 85°C degrade solder joint quality.",
            "calibration_offset": f"Calibration drift explains {pct:.1f}% of defects. Progressive drift leads to placement errors and dimensional defects.",
            "humidity_pct": f"Humidity contributes {pct:.1f}% to defect rate. High moisture causes oxidation and poor solder wetting.",
            "speed_units_hr": f"Production speed accounts for {pct:.1f}% of quality issues. Excessive speed reduces inspection accuracy.",
            "pressure_bar": f"Pressure variation contributes {pct:.1f}%. Unstable pressure affects component placement force.",
            "power_consumption_kw": f"Power consumption pattern explains {pct:.1f}%. Anomalous power draw indicates equipment issues.",
            "shift_encoded": f"Shift timing accounts for {pct:.1f}%. Night shifts show elevated defect rates.",
        }
        return descriptions.get(col, f"Contributes {pct:.1f}% to the target metric.")
