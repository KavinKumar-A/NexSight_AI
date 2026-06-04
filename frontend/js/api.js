/**
 * NexSight AI — API Client
 * REST + WebSocket + SSE communication layer
 */

const API = (() => {
  const BASE = '/api';

  async function get(path) {
    const r = await fetch(BASE + path);
    if (!r.ok) throw new Error(`API ${r.status}: ${r.statusText}`);
    return r.json();
  }

  async function post(path, body = {}) {
    const r = await fetch(BASE + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(`API ${r.status}: ${r.statusText}`);
    return r.json();
  }

  return {
    // ── Data Pipeline ─────────────────────────────
    dataStatus:        () => get('/data/status'),
    generateSynthetic: () => post('/data/generate-synthetic'),
    defectDistribution:() => get('/data/defect-distribution'),
    machineSummary:    () => get('/data/machine-summary'),
    hourlyTrends:      () => get('/data/hourly-trends'),
    shiftAnalysis:     () => get('/data/shift-analysis'),

    // ── Defect Analysis ───────────────────────────
    defectStats:       () => get('/defects/statistics'),
    analyzeImage:      (p) => get(`/defects/analyze${p ? '?image_path=' + encodeURIComponent(p) : ''}`),

    // ── Analytics ─────────────────────────────────
    patterns:          () => get('/analytics/patterns'),
    rootCause:         (t = 'defect_count') => get(`/analytics/root-cause?target=${t}`),
    predictions:       () => get('/analytics/predictions'),
    recommendations:   () => get('/analytics/recommendations'),
    healthScore:       (h = 24) => get(`/analytics/health-score?window_hours=${h}`),
    anomalies:         () => get('/analytics/anomalies'),
    anomalySummary:    () => get('/analytics/anomalies/summary'),

    // ── Dashboard ─────────────────────────────────
    dashboardSummary:  () => get('/dashboard/summary'),
    kpis:              () => get('/dashboard/kpis'),
    timeline:          () => get('/dashboard/timeline'),

    // ── AI Assistant ──────────────────────────────
    aiQuery: (question) => post('/ai/query', { question }),
  };
})();

// Expose globally
window.api = API;
