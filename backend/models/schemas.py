"""
NexSight AI - Pydantic Data Models / Schemas
Defines all request/response models for the API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ── Enums ───────────────────────────────────────────────────
class DefectType(str, Enum):
    OPEN = "open"
    SHORT = "short"
    MOUSEBITE = "mousebite"
    SPUR = "spur"
    PINHOLE = "pinhole"
    SPURIOUS_COPPER = "spurious_copper"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Shift(str, Enum):
    MORNING = "Morning"
    AFTERNOON = "Afternoon"
    NIGHT = "Night"


# ── Defect Detection ───────────────────────────────────────
class BoundingBox(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int


class DetectedDefect(BaseModel):
    defect_type: DefectType
    confidence: float = Field(ge=0.0, le=1.0)
    bounding_box: BoundingBox
    severity: Severity


class DefectAnalysisResponse(BaseModel):
    image_id: str
    total_defects: int
    defects: List[DetectedDefect]
    analysis_time_ms: float
    quality_score: float = Field(ge=0.0, le=100.0)


# ── Sensor / Telemetry Data ────────────────────────────────
class SensorReading(BaseModel):
    timestamp: datetime
    machine_id: str
    temperature: float
    vibration: float
    humidity: float
    pressure: float
    speed: float
    calibration_offset: float
    shift: Shift
    product_line: str
    defect_count: int
    yield_rate: float


# ── Pattern Discovery ──────────────────────────────────────
class DiscoveredPattern(BaseModel):
    pattern_id: str
    description: str
    correlation_strength: float = Field(ge=-1.0, le=1.0)
    affected_factor: str
    impact_metric: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence: str
    severity: Severity


class PatternDiscoveryResponse(BaseModel):
    total_patterns: int
    patterns: List[DiscoveredPattern]
    analysis_timestamp: datetime


# ── Root Cause Analysis ────────────────────────────────────
class RootCauseFactor(BaseModel):
    factor: str
    contribution_pct: float = Field(ge=0.0, le=100.0)
    description: str
    actionable: bool = True


class RootCauseResponse(BaseModel):
    issue: str
    total_factors: int
    factors: List[RootCauseFactor]
    confidence: float = Field(ge=0.0, le=1.0)
    methodology: str = "SHAP + Statistical Decomposition"


# ── Predictive Analytics ───────────────────────────────────
class PredictionResult(BaseModel):
    prediction_type: str
    predicted_value: float
    confidence_interval: Dict[str, float]
    risk_level: Severity
    time_horizon: str
    contributing_features: List[Dict[str, Any]]


class PredictiveResponse(BaseModel):
    predictions: List[PredictionResult]
    model_accuracy: float
    last_trained: datetime


# ── Explainability ─────────────────────────────────────────
class SHAPExplanation(BaseModel):
    feature_name: str
    shap_value: float
    feature_value: float
    direction: str  # "increases" or "decreases"


class GradCAMResult(BaseModel):
    image_id: str
    heatmap_base64: str
    focus_regions: List[BoundingBox]
    explanation: str


class ExplainabilityResponse(BaseModel):
    shap_explanations: Optional[List[SHAPExplanation]] = None
    grad_cam_result: Optional[GradCAMResult] = None
    model_type: str
    explanation_summary: str


# ── Recommendations ────────────────────────────────────────
class Recommendation(BaseModel):
    rec_id: str
    title: str
    description: str
    priority: Severity
    category: str  # "maintenance", "process", "environment", "calibration"
    estimated_impact: str
    machine_id: Optional[str] = None
    auto_applicable: bool = False


class RecommendationResponse(BaseModel):
    total_recommendations: int
    recommendations: List[Recommendation]
    generated_at: datetime


# ── Health Score (Unique Feature) ──────────────────────────
class HealthComponent(BaseModel):
    component: str
    score: float = Field(ge=0.0, le=100.0)
    weight: float
    status: str  # "healthy", "warning", "critical"
    details: str


class ManufacturingHealthScore(BaseModel):
    overall_score: float = Field(ge=0.0, le=100.0)
    grade: str  # A+, A, B, C, D, F
    components: List[HealthComponent]
    trend: str  # "improving", "stable", "declining"
    timestamp: datetime


# ── Dashboard Summary ──────────────────────────────────────
class DashboardSummary(BaseModel):
    health_score: ManufacturingHealthScore
    total_inspections: int
    total_defects: int
    defect_rate: float
    active_alerts: int
    top_patterns: List[DiscoveredPattern]
    top_recommendations: List[Recommendation]
    defect_distribution: Dict[str, int]
    hourly_trend: List[Dict[str, Any]]
    machine_status: List[Dict[str, Any]]
