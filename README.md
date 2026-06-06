# NexSight AI — Manufacturing Intelligence Platform

**Microsoft Build AI Hackathon 2025 — "AI Meets Data: From Noise to Insight"**

NexSight AI turns raw PCB manufacturing telemetry and inspection imagery into
actionable insight: it discovers hidden quality patterns, explains root causes,
forecasts failures, detects defects with computer vision, and streams live
shop-floor metrics — all behind a single FastAPI service with a zero-build
vanilla-JS dashboard.

---

## Features

| Module | What it does |
| --- | --- |
| **Real-time streaming** | WebSocket (`/ws/live`) sensor feed + SSE alert stream (`/api/stream/alerts`) |
| **Pattern discovery** | Surfaces hidden statistical correlations across shifts, machines, and products |
| **Root-cause intelligence** | Feature-importance / SHAP decomposition of quality drivers |
| **Predictive analytics** | XGBoost models for defect, yield, and failure forecasting |
| **Computer vision** | PCB defect detection over the DeepPCB dataset with Grad-CAM explainability |
| **Health score** | Composite manufacturing KPI with grade and component breakdown |
| **Anomaly detection** | Isolation Forest + threshold rules |
| **AI recommendations** | Prioritized, ROI-ranked corrective actions |
| **AI assistant** | Natural-language Q&A over the analytics context (`/api/ai/query`) |

## Tech Stack

- **Backend:** FastAPI + Python 3.12
- **ML:** scikit-learn, XGBoost, LightGBM (SHAP optional)
- **CV:** OpenCV + Pillow (Grad-CAM)
- **Frontend:** Vanilla JS + Plotly.js + Canvas API (no build step)
- **Data:** ~10K synthetic telemetry records + the real DeepPCB dataset (1,500 image pairs, 10,013 annotations)

## Quick Start

```bash
# 1. Install dependencies (Python 3.11+ recommended)
pip install -r requirements.txt

# 2. Launch the server
python run.py            # default port 8000
python run.py --reload   # dev mode with auto-reload
python run.py --port 8080
```

Then open:

- **Dashboard:** http://localhost:8000
- **API docs:** http://localhost:8000/api/docs
- **WebSocket:** ws://localhost:8000/ws/live
- **Alert stream (SSE):** http://localhost:8000/api/stream/alerts

> Synthetic data and trained models are committed under `data/` and `models/`.
> On first launch the server pre-warms the analytics caches in the background.
> To regenerate synthetic data: `POST /api/data/generate-synthetic`.

## Project Layout

```
backend/
  main.py              FastAPI app: routers, WebSocket, SSE, AI assistant, live metrics
  config.py            Central configuration & thresholds
  api/routes/          REST endpoints (data, defects, analytics, dashboard)
  services/            ML/analytics engines (CV, anomaly, patterns, prediction, ...)
  models/schemas.py    Pydantic response models
frontend/              Vanilla-JS single-page dashboard (index.html, js/, css/)
data/                  Synthetic telemetry + cached analytics results
models/saved/          Trained tabular models (joblib)
DeepPCB-master/        Real PCB inspection dataset (images + annotations)
run.py                 Launch script
```

## Key API Endpoints

```
GET  /api/health                       Service health
GET  /api/info                         Capabilities & tech stack
GET  /api/data/status                  Dataset load status
GET  /api/data/machine-summary         Per-machine rollups
GET  /api/defects/statistics           CV defect statistics (DeepPCB)
GET  /api/defects/analyze              Analyze a single PCB image
GET  /api/defects/gradcam             Grad-CAM explanation
GET  /api/analytics/patterns           Discovered quality patterns
GET  /api/analytics/root-cause         Root-cause factors
GET  /api/analytics/predictions        Forecasts & model training results
GET  /api/analytics/recommendations    Prioritized actions
GET  /api/analytics/health-score       Composite health KPI
GET  /api/analytics/anomalies          Anomaly detection results
GET  /api/dashboard/summary            Dashboard rollup
GET  /api/live/metrics                 Live mixed (real+synthetic+session) metrics
POST /api/ai/query                     Natural-language assistant
```
