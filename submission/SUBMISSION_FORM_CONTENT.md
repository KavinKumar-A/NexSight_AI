# NexSight AI — Hackathon Submission Form Content

Copy-paste the sections below into the matching fields.

---

## Project title
```
NexSight AI
```

## Theme
```
AI Meets Data: From Noise to Insight
```

---

## Project description
*(Paste the whole block below.)*

```
PROBLEM STATEMENT
Modern PCB and electronics manufacturing lines generate a continuous flood of noisy
telemetry — temperature, vibration, humidity, conveyor speed, power draw — alongside
thousands of visual inspection images. The vast majority of this data is never analysed.
Defects (opens, shorts, mousebites, spurs, pinholes, spurious copper) are caught late or
missed entirely, their root causes stay buried in the data, and operators are left staring
at dashboards full of raw numbers instead of clear answers. The result is lost yield,
unplanned downtime, and reactive rather than preventive quality management.

OBJECTIVE
NexSight AI converts raw, noisy shop-floor data into clear, explainable, and actionable
manufacturing intelligence — directly addressing the hackathon theme "AI Meets Data: From
Noise to Insight." It unifies sensor telemetry and real PCB inspection imagery into a single
platform that discovers hidden quality patterns, explains root causes, predicts failures
before they happen, detects defects with computer vision, and streams live insight to the
shop floor.

METHODOLOGY
- Data: We combine ~10,000 engineered synthetic telemetry records (with deliberately
  embedded quality patterns) and the real DeepPCB dataset (1,500 image pairs, 10,013
  defect annotations across 6 classes). Real data grounds the computer vision; synthetic
  data lets us demonstrate that the pattern-discovery engine genuinely recovers signal.
- Pattern Discovery: correlation mining + statistical significance testing surfaces hidden
  relationships across shifts, machines and product lines.
- Root-Cause Intelligence: model feature-importance and SHAP attribute each quality issue
  to concrete physical drivers, with a confidence score and an explanation.
- Predictive Analytics: XGBoost models forecast defect counts, yield and machine-failure
  risk so maintenance can be scheduled 48-72 hours ahead.
- Computer Vision: PCB defect detection over DeepPCB with Grad-CAM heatmaps that show what
  the model focused on; the engine runs with or without a GPU/PyTorch.
- Anomaly Detection: Isolation Forest plus domain thresholds flag excursions in real time.
- Real-Time Layer: a FastAPI backend streams sensor data over WebSocket and alerts over
  Server-Sent Events, and an AI assistant answers natural-language questions about the data.

SCOPE OF THE SOLUTION
A complete, runnable platform: a FastAPI service exposing REST + WebSocket + SSE APIs, a
zero-build vanilla-JS dashboard (executive overview, defect intelligence, patterns,
predictions, recommendations and an AI assistant), trained models and cached analytics that
pre-warm on startup. The whole system runs locally with two commands:
`pip install -r requirements.txt` then `python run.py` (http://localhost:8000).

KEY RESULTS
- 1,535 defects detected across 200 PCB inspection images with full type and severity breakdown.
- 7+ hidden quality patterns surfaced and validated at p<0.01.
- Failure-risk forecasting that flags high-risk machines 48-72 hours in advance.
- Sub-2-second real-time alerts on threshold breaches.
- ROI-ranked recommendations projecting measurable yield gain and cost reduction.

ADDITIONAL DETAILS
Every insight is explainable — it ships with a confidence score and the "why" behind it —
so operators can trust and act on it. The architecture is Azure-ready: it can be deployed
on Azure App Service with Azure OpenAI powering the assistant and Azure IoT Hub feeding
real sensor streams in place of the simulator.
```

---

## Built with
*(Add these as tags — type each and press enter.)*

```
python
fastapi
scikit-learn
xgboost
lightgbm
shap
opencv
pillow
grad-cam
plotly
javascript
websocket
server-sent-events
pandas
numpy
uvicorn
deeppcb
```

---

## Video link
*(You are handling this — host on YouTube/Vimeo and paste the URL.)*

Suggested 2-3 minute flow:
1. The problem (noisy manufacturing data, hidden defects).
2. Open the dashboard — executive health score + live machine status.
3. Defect intelligence page — CV results + severity breakdown.
4. Patterns & predictions pages.
5. Ask the AI assistant a question live.
6. Close on impact numbers + the "From Noise to Insight" tagline.

---

## Presentation
Upload one of:
- `submission/NexSight_AI_Presentation.pptx`  (editable PowerPoint)
- `submission/NexSight_AI_Presentation.pdf`   (ready-to-upload PDF)

---

## Demo link
*(You are handling this.)* If running locally for the judges:
```
http://localhost:8000
```
For a public demo, deploy to Azure App Service / Render / Railway and paste that URL.

---

## Repository link
```
https://github.com/KavinKumar-A/NexSight_AI
```

---

## Source code
Upload a ZIP of the project (exclude `venv/`, `__pycache__/`, and `.git/`).

PowerShell one-liner to create a clean zip on the Desktop:
```powershell
Compress-Archive -Path "Z:\MS Build AI\*" -DestinationPath "$env:USERPROFILE\Desktop\NexSight_AI_source.zip" -Force
```
Then in the zip, delete the `venv` folder if it got included (it is large and unnecessary).
```

---

### One-line elevator pitch (handy for any "short description" field)
```
NexSight AI turns noisy PCB-manufacturing telemetry and inspection imagery into explainable,
real-time insight — discovering hidden quality patterns, root causes, failure forecasts and
defect detections, all behind one FastAPI service and a live dashboard.
```
