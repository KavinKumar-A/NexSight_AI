"""
NexSight AI - Data Pipeline Service
Handles data cleaning, enrichment, and preprocessing for both
real (DeepPCB) and synthetic (telemetry) data streams.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from backend.config import (
    DEEPPCB_PATH, SYNTHETIC_DATA_PATH,
    PROCESSED_DATA_PATH, DEFECT_CLASSES, THRESHOLDS
)


class DataPipeline:
    """Unified data pipeline for ingestion, cleaning, and enrichment."""

    def __init__(self):
        self.telemetry_data: Optional[pd.DataFrame] = None
        self.pcb_annotations: Optional[pd.DataFrame] = None
        self._load_data()

    def _load_data(self):
        """Load all available data sources."""
        # Load synthetic telemetry
        telemetry_path = SYNTHETIC_DATA_PATH / "manufacturing_telemetry.csv"
        if telemetry_path.exists():
            self.telemetry_data = pd.read_csv(telemetry_path, parse_dates=["timestamp"])
            print(f"[OK] Loaded {len(self.telemetry_data)} telemetry records")
        else:
            print("[WARN] No telemetry data found. Run synthetic_generator first.")

        # Load DeepPCB annotations
        self.pcb_annotations = self._parse_deeppcb_annotations()

    def _parse_deeppcb_annotations(self) -> pd.DataFrame:
        """Parse all DeepPCB annotation files into a structured DataFrame."""
        records = []

        if not DEEPPCB_PATH.exists():
            print("[WARN] DeepPCB dataset not found.")
            return pd.DataFrame()

        # Parse trainval.txt and test.txt
        for split_file in ["trainval.txt", "test.txt"]:
            split_path = DEEPPCB_PATH / split_file
            if not split_path.exists():
                continue

            split_name = "train" if "train" in split_file else "test"

            with open(split_path, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) != 2:
                        continue
                    img_path, annot_path = parts

                    full_annot = DEEPPCB_PATH / annot_path
                    if not full_annot.exists():
                        continue

                    with open(full_annot, "r") as af:
                        for annot_line in af:
                            vals = annot_line.strip().split()
                            if len(vals) == 5:
                                x1, y1, x2, y2, cls_id = map(int, vals)
                                records.append({
                                    "image_path": str(DEEPPCB_PATH / img_path),
                                    "annotation_path": str(full_annot),
                                    "split": split_name,
                                    "x1": x1, "y1": y1,
                                    "x2": x2, "y2": y2,
                                    "class_id": cls_id,
                                    "defect_type": DEFECT_CLASSES.get(cls_id, "unknown"),
                                    "bbox_width": x2 - x1,
                                    "bbox_height": y2 - y1,
                                    "bbox_area": (x2 - x1) * (y2 - y1),
                                })

        df = pd.DataFrame(records)
        if len(df) > 0:
            print(f"[OK] Parsed {len(df)} defect annotations from DeepPCB")
        return df

    # ── Data Cleaning ──────────────────────────────────────────

    def clean_telemetry(self) -> pd.DataFrame:
        """Clean and preprocess telemetry data."""
        if self.telemetry_data is None:
            return pd.DataFrame()

        df = self.telemetry_data.copy()

        # Handle missing values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())

        # Remove extreme outliers (beyond 4 sigma)
        for col in ["temperature_c", "vibration_mm_s", "humidity_pct",
                     "pressure_bar", "speed_units_hr"]:
            if col in df.columns:
                mean = df[col].mean()
                std = df[col].std()
                df = df[(df[col] >= mean - 4 * std) & (df[col] <= mean + 4 * std)]

        # Categorical encoding
        df["shift_encoded"] = df["shift"].map(
            {"Morning": 0, "Afternoon": 1, "Night": 2}
        )
        df["product_encoded"] = df["product_line"].astype("category").cat.codes

        return df

    def enrich_telemetry(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features for better pattern discovery."""
        # Rolling averages (per machine)
        df = df.sort_values(["machine_id", "timestamp"])

        for col in ["temperature_c", "vibration_mm_s", "defect_count"]:
            df[f"{col}_rolling_24h"] = (
                df.groupby("machine_id")[col]
                .transform(lambda x: x.rolling(48, min_periods=1).mean())
            )

        # Threshold breach flags
        df["temp_breach"] = (df["temperature_c"] > THRESHOLDS["temperature_high"]).astype(int)
        df["vib_breach"] = (df["vibration_mm_s"] > THRESHOLDS["vibration_high"]).astype(int)
        df["humid_breach"] = (df["humidity_pct"] > THRESHOLDS["humidity_high"]).astype(int)
        df["speed_breach"] = (df["speed_units_hr"] > THRESHOLDS["speed_high"]).astype(int)
        df["cal_breach"] = (df["calibration_offset"] > THRESHOLDS["calibration_drift_max"]).astype(int)

        # Total breach count
        breach_cols = ["temp_breach", "vib_breach", "humid_breach", "speed_breach", "cal_breach"]
        df["total_breaches"] = df[breach_cols].sum(axis=1)

        # Interaction features
        df["temp_vib_interaction"] = df["temperature_c"] * df["vibration_mm_s"]
        df["humid_temp_interaction"] = df["humidity_pct"] * df["temperature_c"]

        return df

    # ── Aggregation ────────────────────────────────────────────

    def get_defect_distribution(self) -> Dict:
        """Get distribution of defect types from both data sources."""
        result = {}

        # From telemetry
        if self.telemetry_data is not None:
            tel_dist = self.telemetry_data[
                self.telemetry_data["primary_defect_type"] != "none"
            ]["primary_defect_type"].value_counts().to_dict()
            result["telemetry"] = tel_dist

        # From DeepPCB
        if len(self.pcb_annotations) > 0:
            pcb_dist = self.pcb_annotations["defect_type"].value_counts().to_dict()
            result["deeppcb"] = pcb_dist

        # Combined
        combined = {}
        for source in result.values():
            for k, v in source.items():
                combined[k] = combined.get(k, 0) + v
        result["combined"] = combined

        return result

    def get_machine_summary(self) -> List[Dict]:
        """Get per-machine performance summary."""
        if self.telemetry_data is None:
            return []

        summary = self.telemetry_data.groupby("machine_id").agg({
            "defect_count": ["mean", "sum", "max"],
            "yield_rate_pct": "mean",
            "vibration_mm_s": "mean",
            "temperature_c": "mean",
            "downtime_minutes": "sum",
            "is_anomaly": "mean",
        }).round(2)

        summary.columns = [
            "avg_defects", "total_defects", "max_defects",
            "avg_yield", "avg_vibration", "avg_temperature",
            "total_downtime", "anomaly_rate"
        ]

        result = []
        for machine_id, row in summary.iterrows():
            status = "healthy"
            if row["anomaly_rate"] > 0.3:
                status = "critical"
            elif row["anomaly_rate"] > 0.15:
                status = "warning"

            result.append({
                "machine_id": machine_id,
                "status": status,
                **row.to_dict()
            })

        return result

    def get_hourly_trends(self) -> List[Dict]:
        """Get hourly defect trends."""
        if self.telemetry_data is None:
            return []

        hourly = self.telemetry_data.groupby("hour").agg({
            "defect_count": "mean",
            "yield_rate_pct": "mean",
            "vibration_mm_s": "mean",
            "temperature_c": "mean",
        }).round(2).reset_index()

        return hourly.to_dict(orient="records")

    def get_shift_analysis(self) -> List[Dict]:
        """Get per-shift performance analysis."""
        if self.telemetry_data is None:
            return []

        shift_data = self.telemetry_data.groupby("shift").agg({
            "defect_count": ["mean", "sum"],
            "yield_rate_pct": "mean",
            "downtime_minutes": "sum",
            "is_anomaly": "mean",
        }).round(2)

        shift_data.columns = [
            "avg_defects", "total_defects",
            "avg_yield", "total_downtime", "anomaly_rate"
        ]

        return shift_data.reset_index().to_dict(orient="records")

    def process_all(self) -> pd.DataFrame:
        """Full pipeline: clean → enrich → save."""
        df = self.clean_telemetry()
        if len(df) == 0:
            return df
        df = self.enrich_telemetry(df)

        # Save processed data
        output_path = PROCESSED_DATA_PATH / "enriched_telemetry.csv"
        df.to_csv(output_path, index=False)
        print(f"[OK] Processed data saved: {len(df)} records to {output_path}")

        return df
