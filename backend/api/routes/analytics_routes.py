"""
NexSight AI - Analytics API Routes
All heavy ML results are cached for 10 minutes so pages load instantly after first call.
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
import pandas as pd, os, sys, json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from backend.config import SYNTHETIC_DATA_PATH, BASE_DIR

router = APIRouter()

# ── Persistent + In-Memory TTL Cache ─────────────────────────
_cache: dict = {}
CACHE_TTL = timedelta(minutes=10)
_CACHE_DIR = BASE_DIR / "data" / "cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _cache_file(key: str) -> Path:
    return _CACHE_DIR / f"{key.replace('/', '_')}.json"

def _cached(key: str):
    # 1. In-memory check
    entry = _cache.get(key)
    if entry and datetime.now() < entry["expires"]:
        return entry["data"]
    # 2. Disk check (for persistence across restarts)
    cf = _cache_file(key)
    if cf.exists():
        try:
            disk = json.loads(cf.read_text(encoding="utf-8"))
            expires = datetime.fromisoformat(disk["expires"])
            if datetime.now() < expires:
                _cache[key] = {"data": disk["data"], "expires": expires}
                return disk["data"]
        except Exception:
            pass
    return None

def _store(key: str, data):
    expires = datetime.now() + CACHE_TTL
    _cache[key] = {"data": data, "expires": expires}
    # Persist to disk (fire-and-forget, ignore errors)
    try:
        cf = _cache_file(key)
        cf.write_text(json.dumps({"data": data, "expires": expires.isoformat()}, default=str), encoding="utf-8")
    except Exception:
        pass
    return data

# ── Data loader (cached in memory) ───────────────────────────
_data = None

def _get_data() -> pd.DataFrame:
    global _data
    if _data is None:
        path = SYNTHETIC_DATA_PATH / "manufacturing_telemetry.csv"
        if path.exists():
            _data = pd.read_csv(path, parse_dates=["timestamp"])
        else:
            raise HTTPException(404, "No telemetry data. Run POST /api/data/generate-synthetic first.")
    return _data

# ── Pattern Discovery ─────────────────────────────────────────
@router.get("/patterns")
async def discover_patterns():
    cached = _cached("patterns")
    if cached:
        return cached
    data = _get_data()
    from backend.services.pattern_discovery import PatternDiscoveryEngine
    patterns = PatternDiscoveryEngine(data).discover_all_patterns()
    return _store("patterns", {
        "total_patterns": len(patterns),
        "patterns": patterns,
        "analysis_timestamp": datetime.now().isoformat(),
        "cached": False,
    })

# ── Root Cause Analysis ───────────────────────────────────────
@router.get("/root-cause")
async def analyze_root_causes(target: str = Query(default="defect_count")):
    key = f"rootcause_{target}"
    cached = _cached(key)
    if cached:
        return cached
    data = _get_data()
    from backend.services.data_pipeline import DataPipeline
    from backend.services.root_cause import RootCauseEngine
    enriched = DataPipeline().clean_telemetry()
    if len(enriched) == 0:
        enriched = data
    result = RootCauseEngine(enriched).analyze_root_causes(target)
    return _store(key, result)

@router.get("/root-cause/{defect_type}")
async def analyze_defect_root_cause(defect_type: str):
    key = f"rootcause_type_{defect_type}"
    cached = _cached(key)
    if cached:
        return cached
    data = _get_data()
    from backend.services.root_cause import RootCauseEngine
    return _store(key, RootCauseEngine(data).analyze_specific_defect_type(defect_type))

# ── Predictive Analytics ──────────────────────────────────────
@router.get("/predictions")
async def get_predictions():
    cached = _cached("predictions")
    if cached:
        return cached
    data = _get_data()
    data_copy = data.copy()
    if "shift_encoded" not in data_copy.columns:
        data_copy["shift_encoded"] = data_copy["shift"].map(
            {"Morning": 0, "Afternoon": 1, "Night": 2}).fillna(0)
    if "hour" not in data_copy.columns:
        data_copy["hour"] = pd.to_datetime(data_copy["timestamp"]).dt.hour
    if "day_of_week" not in data_copy.columns:
        data_copy["day_of_week"] = pd.to_datetime(data_copy["timestamp"]).dt.dayofweek
    from backend.services.predictive_analytics import PredictiveEngine
    engine = PredictiveEngine(data_copy)
    result = {"training": engine.train_models(), "forecast": engine.get_forecast_summary()}
    return _store("predictions", result)

@router.post("/predict-defects")
async def predict_defects(conditions: dict):
    data = _get_data()
    data_copy = data.copy()
    if "shift_encoded" not in data_copy.columns:
        data_copy["shift_encoded"] = data_copy["shift"].map(
            {"Morning": 0, "Afternoon": 1, "Night": 2}).fillna(0)
    if "hour" not in data_copy.columns:
        data_copy["hour"] = pd.to_datetime(data_copy["timestamp"]).dt.hour
    if "day_of_week" not in data_copy.columns:
        data_copy["day_of_week"] = pd.to_datetime(data_copy["timestamp"]).dt.dayofweek
    from backend.services.predictive_analytics import PredictiveEngine
    return PredictiveEngine(data_copy).predict_defects(conditions)

# ── Recommendations ───────────────────────────────────────────
@router.get("/recommendations")
async def get_recommendations():
    cached = _cached("recommendations")
    if cached:
        return cached
    data = _get_data()
    from backend.services.pattern_discovery import PatternDiscoveryEngine
    from backend.services.root_cause import RootCauseEngine
    from backend.services.recommendation import RecommendationEngine
    patterns    = PatternDiscoveryEngine(data).discover_all_patterns()
    root_causes = RootCauseEngine(data).analyze_root_causes()
    recs        = RecommendationEngine(data).generate_all_recommendations(patterns, root_causes)
    return _store("recommendations", {
        "total_recommendations": len(recs),
        "recommendations": recs,
        "generated_at": datetime.now().isoformat(),
    })

# ── Health Score ──────────────────────────────────────────────
@router.get("/health-score")
async def get_health_score(window_hours: int = Query(default=24, ge=1, le=720)):
    key = f"health_{window_hours}"
    cached = _cached(key)
    if cached:
        return cached
    data = _get_data()
    from backend.services.health_score import HealthScoreEngine
    return _store(key, HealthScoreEngine(data).compute_health_score(window_hours))

@router.get("/health-score/machines")
async def get_machine_health():
    cached = _cached("health_machines")
    if cached:
        return cached
    data = _get_data()
    from backend.services.health_score import HealthScoreEngine
    return _store("health_machines", HealthScoreEngine(data).compute_machine_health())

# ── Anomaly Detection ─────────────────────────────────────────
@router.get("/anomalies")
async def detect_anomalies():
    cached = _cached("anomalies_full")
    if cached:
        return cached
    data = _get_data()
    from backend.services.anomaly_detector import AnomalyDetector
    return _store("anomalies_full", AnomalyDetector(data).detect_all_anomalies())

@router.get("/anomalies/summary")
async def anomaly_summary():
    cached = _cached("anomalies_summary")
    if cached:
        return cached
    data = _get_data()
    from backend.services.anomaly_detector import AnomalyDetector
    return _store("anomalies_summary", AnomalyDetector(data).get_anomaly_summary())
