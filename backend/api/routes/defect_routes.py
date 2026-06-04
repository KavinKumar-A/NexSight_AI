"""
NexSight AI - Defect Analysis API Routes
Endpoints for CV-based PCB defect detection and analysis.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from backend.config import DEEPPCB_PATH

router = APIRouter()

_cv_engine = None


def _get_cv_engine():
    global _cv_engine
    if _cv_engine is None:
        from backend.services.cv_engine import CVEngine
        _cv_engine = CVEngine()
    return _cv_engine


@router.get("/analyze")
async def analyze_image(image_path: Optional[str] = None):
    """Analyze a single PCB image for defects."""
    engine = _get_cv_engine()

    if image_path is None:
        # Use a sample image
        sample_images = engine._get_image_files(str(DEEPPCB_PATH), 1)
        if not sample_images:
            raise HTTPException(status_code=404, detail="No images found in DeepPCB dataset")
        image_path = str(sample_images[0])

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail=f"Image not found: {image_path}")

    return engine.analyze_image(image_path)


@router.get("/batch-analyze")
async def batch_analyze(max_images: int = Query(default=50, le=500)):
    """Analyze a batch of PCB images."""
    engine = _get_cv_engine()
    results = engine.analyze_batch(max_images=max_images)
    return {
        "total_analyzed": len(results),
        "results": results,
    }


@router.get("/statistics")
async def defect_statistics():
    """Get comprehensive defect detection statistics."""
    engine = _get_cv_engine()
    return engine.get_defect_statistics()


@router.get("/gradcam")
async def gradcam_visualization(
    image_path: Optional[str] = None,
    target_class: Optional[int] = None
):
    """Generate Grad-CAM visualization for an image."""
    engine = _get_cv_engine()

    if image_path is None:
        sample_images = engine._get_image_files(str(DEEPPCB_PATH), 1)
        if not sample_images:
            raise HTTPException(status_code=404, detail="No images found")
        image_path = str(sample_images[0])

    return engine.generate_gradcam(image_path, target_class)


@router.get("/sample-images")
async def get_sample_images(count: int = Query(default=10, le=50)):
    """Get paths to sample images for analysis."""
    engine = _get_cv_engine()
    images = engine._get_image_files(str(DEEPPCB_PATH), count)
    return {
        "count": len(images),
        "images": [str(p) for p in images],
    }
