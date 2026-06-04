"""
NexSight AI - Dashboard API Routes
Aggregated endpoints for the frontend dashboard.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from backend.config import SYNTHETIC_DATA_PATH, DEEPPCB_PATH

router = APIRouter()

# Simple TTL cache
from datetime import timedelta
_cache: dict = {}
_CACHE_TTL = timedelta(minutes=10)

def _cached(key):
    e = _cache.get(key)
    if e and datetime.now() < e["expires"]:
        return e["data"]
    return None

def _store(key, data):
    _cache[key] = {"data": data, "expires": datetime.now() + _CACHE_TTL}
    return data

_data_df = None
def _load_data() -> pd.DataFrame:
    global _data_df
    if _data_df is None:
        path = SYNTHETIC_DATA_PATH / "manufacturing_telemetry.csv"
        if path.exists():
            _data_df = pd.read_csv(path, parse_dates=["timestamp"])
        else:
            raise HTTPException(status_code=404, detail="No data available. Generate synthetic data first.")
    return _data_df

@router.get("/summary")
async def dashboard_summary():
    """Get complete dashboard summary with all key metrics."""
    cached = _cached("dashboard_summary")
    if cached:
        return cached
    data = _load_data()

    # Health Score
    from backend.services.health_score import HealthScoreEngine
    health_engine = HealthScoreEngine(data)
    health = health_engine.compute_health_score()

    # Defect distribution
    from backend.services.data_pipeline import DataPipeline
    pipeline = DataPipeline()
    defect_dist = pipeline.get_defect_distribution()
    machine_summary = pipeline.get_machine_summary()
    hourly_trends = pipeline.get_hourly_trends()
    shift_analysis = pipeline.get_shift_analysis()

    # Top patterns (limited)
    from backend.services.pattern_discovery import PatternDiscoveryEngine
    pattern_engine = PatternDiscoveryEngine(data)
    patterns = pattern_engine.discover_all_patterns()[:5]

    # Top recommendations (limited)
    from backend.services.recommendation import RecommendationEngine
    rec_engine = RecommendationEngine(data)
    recs = rec_engine.generate_all_recommendations(patterns)[:5]

    # Anomaly summary
    from backend.services.anomaly_detector import AnomalyDetector
    anomaly_det = AnomalyDetector(data)
    anomaly_sum = anomaly_det.get_anomaly_summary()

    # PCB Statistics
    pcb_stats = {}
    if len(pipeline.pcb_annotations) > 0:
        pcb_stats = {
            "total_annotations": len(pipeline.pcb_annotations),
            "defect_types": pipeline.pcb_annotations["defect_type"].value_counts().to_dict(),
            "avg_bbox_area": round(float(pipeline.pcb_annotations["bbox_area"].mean()), 1),
        }

    result = {
        "health_score": health,
        "total_inspections": len(data),
        "total_defects": int(data["defect_count"].sum()),
        "defect_rate": round(float(data[data["defect_count"] > 0].shape[0] / len(data) * 100), 1),
        "avg_yield": round(float(data["yield_rate_pct"].mean()), 1),
        "avg_defects_per_reading": round(float(data["defect_count"].mean()), 2),
        "active_alerts": anomaly_sum["flagged_anomalies"],
        "top_patterns": patterns,
        "top_recommendations": recs,
        "defect_distribution": defect_dist.get("combined", {}),
        "hourly_trends": hourly_trends,
        "shift_analysis": shift_analysis,
        "machine_status": machine_summary,
        "anomaly_summary": anomaly_sum,
        "pcb_statistics": pcb_stats,
        "timestamp": datetime.now().isoformat(),
    }
    return _store("dashboard_summary", result)


@router.get("/kpis")
async def dashboard_kpis():
    """Get key performance indicators."""
    data = _load_data()

    return {
        "total_records": len(data),
        "date_range": {
            "start": str(data["timestamp"].min()),
            "end": str(data["timestamp"].max()),
        },
        "machines": int(data["machine_id"].nunique()),
        "avg_defect_count": round(float(data["defect_count"].mean()), 2),
        "max_defect_count": int(data["defect_count"].max()),
        "avg_yield": round(float(data["yield_rate_pct"].mean()), 1),
        "min_yield": round(float(data["yield_rate_pct"].min()), 1),
        "total_downtime_hours": round(float(data["downtime_minutes"].sum() / 60), 1),
        "anomaly_rate": round(float(data["is_anomaly"].mean() * 100), 1),
        "defect_types": data[data["primary_defect_type"] != "none"]["primary_defect_type"].value_counts().to_dict(),
    }


@router.get("/timeline")
async def defect_timeline():
    """Get defect timeline data for charts."""
    data = _load_data()

    # Daily aggregation
    data["date"] = data["timestamp"].dt.date
    daily = data.groupby("date").agg({
        "defect_count": ["mean", "sum"],
        "yield_rate_pct": "mean",
        "vibration_mm_s": "mean",
        "temperature_c": "mean",
        "is_anomaly": "sum",
    }).round(2)

    daily.columns = [
        "avg_defects", "total_defects",
        "avg_yield", "avg_vibration",
        "avg_temperature", "anomaly_count",
    ]

    daily = daily.reset_index()
    daily["date"] = daily["date"].astype(str)

    return daily.to_dict(orient="records")
