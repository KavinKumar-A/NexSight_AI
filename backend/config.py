"""
NexSight AI - Configuration Module
Centralized configuration for the entire platform.
"""

import os
from pathlib import Path

# ── Base Paths ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DEEPPCB_PATH = BASE_DIR / "DeepPCB-master" / "PCBData"
SYNTHETIC_DATA_PATH = BASE_DIR / "data" / "synthetic"
PROCESSED_DATA_PATH = BASE_DIR / "data" / "processed"
MODELS_PATH = BASE_DIR / "models" / "saved"

# ── Ensure directories exist ────────────────────────────────
for p in [SYNTHETIC_DATA_PATH, PROCESSED_DATA_PATH, MODELS_PATH]:
    p.mkdir(parents=True, exist_ok=True)

# ── Application Settings ────────────────────────────────────
APP_NAME = "NexSight AI"
APP_VERSION = "1.0.0"
DEBUG = True

# ── Server Settings ─────────────────────────────────────────
HOST = "0.0.0.0"
PORT = 8000

# ── CV Model Settings ───────────────────────────────────────
CV_IMAGE_SIZE = 256
CV_NUM_CLASSES = 6
CV_BATCH_SIZE = 32
CV_EPOCHS = 25
CV_LEARNING_RATE = 0.001

# ── Defect Class Mapping ────────────────────────────────────
DEFECT_CLASSES = {
    1: "open",
    2: "short",
    3: "mousebite",
    4: "spur",
    5: "pinhole",
    6: "spurious_copper"
}

DEFECT_COLORS = {
    "open": "#FF6B6B",
    "short": "#4ECDC4",
    "mousebite": "#45B7D1",
    "spur": "#96CEB4",
    "pinhole": "#FFEAA7",
    "spurious_copper": "#DDA0DD"
}

# ── Tabular Model Settings ──────────────────────────────────
TABULAR_N_ESTIMATORS = 200
TABULAR_MAX_DEPTH = 8
TABULAR_LEARNING_RATE = 0.05

# ── Synthetic Data Settings ─────────────────────────────────
SYNTHETIC_NUM_RECORDS = 10000
SYNTHETIC_NUM_MACHINES = 8
SYNTHETIC_SHIFTS = ["Morning", "Afternoon", "Night"]
SYNTHETIC_PRODUCT_LINES = ["PCB-Alpha", "PCB-Beta", "PCB-Gamma", "PCB-Delta"]

# ── Manufacturing Thresholds ────────────────────────────────
THRESHOLDS = {
    "temperature_high": 85.0,       # °C
    "temperature_low": 15.0,        # °C
    "vibration_high": 4.5,          # mm/s
    "humidity_high": 75.0,          # %
    "pressure_low": 0.8,            # bar
    "speed_high": 120.0,            # units/hr
    "calibration_drift_max": 0.15,  # tolerance
}

# ── Health Score Weights ────────────────────────────────────
HEALTH_WEIGHTS = {
    "defect_rate": 0.30,
    "machine_condition": 0.25,
    "environmental": 0.20,
    "throughput": 0.15,
    "calibration": 0.10,
}
