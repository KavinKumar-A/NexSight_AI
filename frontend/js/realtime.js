/**
 * NexSight AI — Real-Time Data Module v2
 * WebSocket + SSE + Live Metrics polling
 * Drives cross-page live updates with real + synthetic + dummy improvement data
 */

const liveData = (() => {
  let ws          = null;
  let sseSource   = null;
  // metricsTimer kept so callers can clearInterval if needed
  let metricsTimer;
  let readingCount = 0;
  let anomalyCount = 0;
  let notifCount   = 0;
  let _lastMetrics = null;
  const MAX_ROWS   = 50;
  const rows       = [];

  // Rolling aggregates for cross-page KPI updates
  const rolling = { temps: [], vibs: [], yields: [], defects: [] };
  const ROLL_SIZE = 30;

  // ── WebSocket ─────────────────────────────────────────────────
  function connect() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    ws = new WebSocket(`${proto}://${location.host}/ws/live`);
    updateWsStatus('connecting');
    ws.onopen    = () => updateWsStatus('connected');
    ws.onerror   = () => updateWsStatus('error');
    ws.onclose   = () => { updateWsStatus('disconnected'); setTimeout(connect, 3000); };
    ws.onmessage = (e) => { try { handleReading(JSON.parse(e.data)); } catch {} };
  }

  function updateWsStatus(state) {
    const map = {
      connecting:   { text: 'Connecting...', color: '#FFB900', pill: 'Connecting…' },
      connected:    { text: 'Live Feed Active', color: '#00C878', pill: 'WebSocket Live' },
      error:        { text: 'Connection Error', color: '#D13438', pill: 'Error' },
      disconnected: { text: 'Reconnecting...', color: '#FFB900', pill: 'Reconnecting…' },
    };
    const s = map[state] || map.disconnected;
    _set('ws-status-text', s.text);
    const txt = document.getElementById('ws-status-text');
    if (txt) txt.style.color = s.color;
    _set('ws-label', s.pill);
  }

  function handleReading(r) {
    readingCount++;
    if (r.is_anomaly) anomalyCount++;

    // Push to rolling buffers
    _push(rolling.temps,   r.temperature);
    _push(rolling.vibs,    r.vibration);
    _push(rolling.yields,  r.yield_pct);
    _push(rolling.defects, r.defect_count);

    // Update live monitor KPIs
    _set('live-temp',          `${r.temperature}°C`);
    _set('live-temp-machine',  r.machine);
    _set('live-vib',           `${r.vibration} mm/s`);
    _set('live-vib-machine',   r.machine);
    _set('live-yield',         `${r.yield_pct}%`);
    _set('live-yield-machine', r.machine);
    _set('live-anomaly-count', anomalyCount.toString());
    _set('live-counter',       `${readingCount} readings`);

    // Color live KPI cards
    const tempEl = document.querySelector('.glass-blue .kpi-value');
    if (tempEl) tempEl.style.color = r.temperature > 85 ? '#EF4444' : r.temperature > 75 ? '#FFB900' : '#50E6FF';

    // Update overview KPIs if on that page (live patching)
    if (_currentPage === 'overview' || _currentPage === 'anomalies') {
      _flashUpdate('v-yield',  `${_avg(rolling.yields).toFixed(1)}%`);
      _flashUpdate('v-alerts', anomalyCount.toString());
    }

    // Push to streaming charts
    if (typeof charts !== 'undefined') charts.pushRealtimePoint(r);

    // Add row to live table
    prependRow(r);
  }

  function prependRow(r) {
    rows.unshift(r);
    if (rows.length > MAX_ROWS) rows.pop();
    const tbody = document.getElementById('live-tbody');
    if (!tbody) return;

    const time = new Date(r.ts).toLocaleTimeString('en-US', { hour12: false });
    const defColor = r.defect_count > 5 ? '#EF4444' : r.defect_count > 2 ? '#FFB900' : '#00C878';

    const tr = document.createElement('tr');
    if (r.is_anomaly) tr.style.background = 'rgba(209,52,56,0.06)';
    tr.innerHTML = `
      <td class="mono">${time}</td>
      <td><strong>${r.machine}</strong></td>
      <td>${r.shift}</td>
      <td>${r.product}</td>
      <td class="mono" style="color:${r.temperature>85?'#EF4444':r.temperature>75?'#FFB900':'#50E6FF'}">${r.temperature}</td>
      <td class="mono" style="color:${r.vibration>4.5?'#EF4444':r.vibration>3?'#FFB900':'#8CA0BC'}">${r.vibration}</td>
      <td class="mono" style="color:${r.yield_pct<85?'#EF4444':r.yield_pct<90?'#FFB900':'#00C878'}">${r.yield_pct}</td>
      <td class="mono" style="color:${defColor}">${r.defect_count}</td>
      <td>${r.is_anomaly
        ? '<span class="badge badge-danger">Anomaly</span>'
        : '<span class="badge badge-success">Normal</span>'}</td>`;
    tr.style.opacity = '0';
    tbody.insertBefore(tr, tbody.firstChild);
    requestAnimationFrame(() => { tr.style.transition = 'opacity 0.3s ease'; tr.style.opacity = '1'; });
    while (tbody.children.length > MAX_ROWS) tbody.removeChild(tbody.lastChild);
  }

  function clear() {
    rows.length = 0; readingCount = 0; anomalyCount = 0;
    const tbody = document.getElementById('live-tbody');
    if (tbody) tbody.innerHTML = '';
    _set('live-counter', '0 readings');
    _set('live-anomaly-count', '0');
    if (typeof charts !== 'undefined') charts.clearRealtime();
  }

  // ── SSE Alerts ────────────────────────────────────────────────
  function connectAlerts() {
    if (sseSource) sseSource.close();
    sseSource = new EventSource('/api/stream/alerts');
    sseSource.onmessage = (e) => { try { addNotification(JSON.parse(e.data)); } catch {} };
    sseSource.onerror = () => { sseSource.close(); setTimeout(connectAlerts, 5000); };
  }

  function addNotification(alert) {
    notifCount++;
    const badge = document.getElementById('notif-badge');
    if (badge) { badge.textContent = notifCount; badge.style.display = ''; }

    const list = document.getElementById('notif-list');
    if (!list) return;
    const ts = new Date(alert.ts).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    const el = document.createElement('div');
    el.className = `notif-item ${alert.severity}`;
    el.innerHTML = `
      <div class="notif-machine">${alert.machine} — <span style="text-transform:capitalize;">${alert.severity}</span></div>
      <div class="notif-msg">${alert.message}</div>
      <div class="notif-ts">${ts}</div>`;
    list.insertBefore(el, list.firstChild);
    while (list.children.length > 20) list.removeChild(list.lastChild);
    if (alert.severity === 'critical') showToast(`${alert.machine}: ${alert.message}`, 'error');
  }

  // ── Live Mixed Metrics Polling ────────────────────────────────
  // Polls /api/live/metrics every 20 seconds and updates ALL pages
  function startMetricsPolling() {
    pollMetrics(); // immediate first call
    metricsTimer = setInterval(pollMetrics, 20000);
  }

  async function pollMetrics() {
    try {
      const data = await fetch('/api/live/metrics').then(r => r.json());
      _lastMetrics = data;
      applyLiveMetrics(data);
      updateImprovementBanners(data);
      updateLiveUpdateBars(data);
    } catch (e) { /* silent */ }
  }

  function applyLiveMetrics(data) {
    const k = data.kpis;

    // Overview KPI live patch
    _flashUpdate('v-yield',   `${k.yield_pct}%`);
    _flashUpdate('v-defects',  k.defect_count.toLocaleString());
    _flashUpdate('v-alerts',   Math.round(k.anomaly_pct).toString());

    // Defect inspector page KPIs (if elements exist)
    const defImpEl = document.getElementById('defect-live-improvement');
    if (defImpEl) defImpEl.textContent = `${data.improvement_summary.improvement_pct || 0}% reduction vs baseline`;

    // Anomaly page live update
    const anomLiveEl = document.getElementById('anomaly-live-rate');
    if (anomLiveEl) anomLiveEl.textContent = `${k.anomaly_pct}%`;

    // Update live machine table if visible
    if (data.machines && document.getElementById('live-machine-stats')) {
      renderLiveMachineStats(data.machines);
    }
  }

  function updateImprovementBanners(data) {
    const imp = data.improvement_summary;
    document.querySelectorAll('[data-imp-yield]').forEach(el => {
      el.textContent = `+${imp.yield_gained}%`;
    });
    document.querySelectorAll('[data-imp-defects]').forEach(el => {
      el.textContent = `-${imp.defects_reduced}`;
    });
    document.querySelectorAll('[data-imp-anomalies]').forEach(el => {
      el.textContent = `-${imp.anomalies_reduced}%`;
    });
    document.querySelectorAll('[data-imp-savings]').forEach(el => {
      el.textContent = `$${imp.est_cost_saved.toLocaleString()}`;
    });
  }

  function updateLiveUpdateBars(data) {
    const now = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
    document.querySelectorAll('.lub-ts').forEach(el => { el.textContent = now; });
    document.querySelectorAll('.lub-readings').forEach(el => { el.textContent = `${readingCount} WS readings`; });
    document.querySelectorAll('.lub-improvement').forEach(el => {
      el.textContent = data.improvement_summary.status === 'improving' ? 'Improving' : 'Baseline';
      el.style.color = data.improvement_summary.status === 'improving' ? '#00C878' : '#8CA0BC';
    });
  }

  function renderLiveMachineStats(machines) {
    const el = document.getElementById('live-machine-stats');
    if (!el) return;
    el.innerHTML = machines.map(m => `
      <div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid var(--border-base);">
        <strong style="width:28px;">${m.machine_id}</strong>
        <span class="badge ${m.status==='healthy'?'badge-success':m.status==='warning'?'badge-warning':'badge-danger'}">${m.status}</span>
        <span style="font-size:0.78rem;color:var(--text-muted);flex:1;">
          Yield: <strong style="color:${m.yield_pct>95?'#00C878':m.yield_pct>90?'#FFB900':'#EF4444'}">${m.yield_pct}%</strong>
          &nbsp;|&nbsp; Risk: <strong style="color:${m.risk_pct>30?'#EF4444':m.risk_pct>15?'#FFB900':'#00C878'}">${m.risk_pct}%</strong>
        </span>
        ${m.status === 'critical' ? '<span class="delta-chip delta-down">!</span>' :
          m.status === 'warning'  ? '<span class="delta-chip delta-flat">~</span>' :
                                    '<span class="delta-chip delta-up">OK</span>'}
      </div>`).join('');
  }

  // ── Auto-Refresh Countdown ────────────────────────────────────
  function startCountdowns() {
    let countdowns = {};
    setInterval(() => {
      document.querySelectorAll('.lub-countdown[data-seconds]').forEach(el => {
        const id = el.dataset.id || (el.dataset.id = Math.random().toString(36).slice(2));
        if (!countdowns[id] || countdowns[id] <= 0) countdowns[id] = parseInt(el.dataset.seconds) || 20;
        countdowns[id]--;
        el.textContent = countdowns[id] + 's';
      });
    }, 1000);
  }

  // ── Helpers ───────────────────────────────────────────────────
  function _set(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }

  function _flashUpdate(id, val) {
    const el = document.getElementById(id);
    if (!el || el.textContent === val) return;
    el.textContent = val;
    el.classList.remove('flash-update');
    void el.offsetWidth; // force reflow
    el.classList.add('flash-update');
  }

  function _push(arr, val) { arr.push(val); if (arr.length > ROLL_SIZE) arr.shift(); }
  function _avg(arr) { return arr.length ? arr.reduce((a,b) => a+b, 0) / arr.length : 0; }

  function getLastMetrics() { return _lastMetrics; }
  function getReadingCount() { return readingCount; }
  function getAnomalyCount() { return anomalyCount; }
  function getRollingAvg()   { return { temp: _avg(rolling.temps), vib: _avg(rolling.vibs), yield: _avg(rolling.yields), defects: _avg(rolling.defects) }; }

  // ── Init ──────────────────────────────────────────────────────
  function init() {
    connect();
    connectAlerts();
    startMetricsPolling();
    startCountdowns();
    if (typeof charts !== 'undefined') charts.initRealtimeCharts();
  }

  return { init, connect, clear, connectAlerts, pollMetrics, getLastMetrics, getReadingCount, getAnomalyCount, getRollingAvg };
})();

window.liveData = liveData;

// _currentPage is declared and owned by app.js — do NOT redeclare here
