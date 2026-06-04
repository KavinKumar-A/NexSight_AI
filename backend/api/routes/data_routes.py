"""
NexSight AI - Data Pipeline API Routes
Endpoints for data ingestion, synthetic generation, and pipeline management.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

router = APIRouter()

# Lazy-loaded services
_pipeline = None
_generator = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        from backend.services.data_pipeline import DataPipeline
        _pipeline = DataPipeline()
    return _pipeline


def _get_generator():
    global _generator
    if _generator is None:
        from backend.services.synthetic_generator import generate_all_synthetic_data
        _generator = generate_all_synthetic_data
    return _generator


@router.get("/status")
async def data_status():
    """Get current data pipeline status."""
    pipeline = _get_pipeline()
    return {
        "telemetry_loaded": pipeline.telemetry_data is not None,
        "telemetry_records": len(pipeline.telemetry_data) if pipeline.telemetry_data is not None else 0,
        "pcb_annotations": len(pipeline.pcb_annotations) if pipeline.pcb_annotations is not None else 0,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/generate-synthetic")
async def generate_synthetic():
    """Generate synthetic manufacturing data."""
    try:
        gen_func = _get_generator()
        df = gen_func()
        # Reset pipeline to load new data
        global _pipeline
        _pipeline = None

        return {
            "status": "success",
            "records_generated": len(df),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/defect-distribution")
async def defect_distribution():
    """Get defect type distribution across all data sources."""
    pipeline = _get_pipeline()
    return pipeline.get_defect_distribution()


@router.get("/machine-summary")
async def machine_summary():
    """Get per-machine performance summary."""
    pipeline = _get_pipeline()
    return pipeline.get_machine_summary()


@router.get("/hourly-trends")
async def hourly_trends():
    """Get hourly defect and quality trends."""
    pipeline = _get_pipeline()
    return pipeline.get_hourly_trends()


@router.get("/shift-analysis")
async def shift_analysis():
    """Get per-shift performance analysis."""
    pipeline = _get_pipeline()
    return pipeline.get_shift_analysis()


@router.post("/process")
async def process_pipeline():
    """Run the full data processing pipeline."""
    try:
        pipeline = _get_pipeline()
        df = pipeline.process_all()
        return {
            "status": "success",
            "records_processed": len(df),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import random

@router.get("/live")
async def get_live_data():
    """Simulate a live data stream for the monitoring dashboard."""
    machine_id = f"M{random.randint(1, 8)}"
    temperature = round(random.uniform(70.0, 95.0), 2)
    vibration = round(random.uniform(1.5, 6.0), 2)
    humidity = round(random.uniform(40.0, 75.0), 2)
    yield_rate = round(random.uniform(85.0, 99.5), 2)
    
    # Calculate anomaly status (simple heuristic)
    is_anomaly = temperature > 85.0 or vibration > 4.5 or humidity > 70.0
    
    return {
        "timestamp": datetime.now().isoformat(),
        "machine_id": machine_id,
        "temperature_c": temperature,
        "vibration_mm_s": vibration,
        "humidity_pct": humidity,
        "yield_rate_pct": yield_rate,
        "is_anomaly": is_anomaly,
        "status": "Critical" if is_anomaly else ("Warning" if yield_rate < 90 else "Healthy")
    }
