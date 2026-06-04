/**
 * NexSight AI — Main Application Controller
 * Microsoft Build AI Hackathon 2025
 */

// ── State ─────────────────────────────────────────────────────
let _currentPage = 'overview';
let _dashData    = null;
let _autoRefreshTimer = null;

// ── Auth ─────────────────────────────────────────────────────
const VALID_USERS = { admin: 'nexsight2025', demo: 'demo', nexsight: 'ai2025' };

function checkAuth() {
  const token = localStorage.getItem('nx_auth');
  if (token === 'authenticated') {
    document.getElementById('login-screen')?.classList.add('hidden');
    return true;
  }
  return false;
}

function doLogin(e) {
  e.preventDefault();
  const user = document.getElementById('login-user')?.value.trim();
  const pass = document.getElementById('login-pass')?.value;
  const btn    = document.getElementById('login-btn');
  const btnTxt = document.getElementById('login-btn-text');

  if (!user || !pass) { showLoginError('Please enter username and password.'); return; }

  btn.disabled = true;
  btnTxt.textContent = 'Signing in...';

  // Simulate brief auth delay
  setTimeout(() => {
    if (VALID_USERS[user.toLowerCase()] === pass) {
      localStorage.setItem('nx_auth', 'authenticated');
      localStorage.setItem('nx_user', user);
      // Update avatar
      const av = document.querySelector('.topbar-avatar');
      if (av) av.textContent = user.slice(0, 2).toUpperCase();
      // Hide login screen
      const ls = document.getElementById('login-screen');
      if (ls) { ls.style.opacity = '0'; setTimeout(() => ls.classList.add('hidden'), 500); }
    } else {
      showLoginError('Invalid username or password. Try: admin / nexsight2025');
      btn.disabled = false;
      btnTxt.textContent = 'Sign In';
    }
  }, 600);
}

function showLoginError(msg) {
  const el = document.getElementById('login-error');
  if (el) { el.textContent = msg; el.style.display = 'block'; }
}

function togglePassVis() {
  const inp  = document.getElementById('login-pass');
  const icon = document.getElementById('eye-icon');
  if (inp.type === 'password') {
    inp.type = 'text';
    icon.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>';
  } else {
    inp.type = 'password';
    icon.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>';
  }
}

function logout() {
  localStorage.removeItem('nx_auth');
  localStorage.removeItem('nx_user');
  location.reload();
}

window.doLogin = doLogin;
window.togglePassVis = togglePassVis;
window.logout = logout;

// ── Navigation ─────────────────────────────────────────────────
function navigateTo(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.sb-link').forEach(l => l.classList.remove('active'));

  const section = document.getElementById(`page-${page}`);
  const navLink = document.querySelector(`[data-page="${page}"]`);
  if (section) section.classList.add('active');
  if (navLink) navLink.classList.add('active');

  _currentPage = page;
  const labels = {
    overview:'Overview', live:'Live Monitor', defects:'Defect Inspector',
    patterns:'Pattern Discovery', rootcause:'Root Cause (SHAP)', predictions:'Predictive Analytics',
    anomalies:'Anomaly Detection', recommendations:'AI Recommendations', assistant:'AI Assistant',
  };
  const lbl = document.getElementById('current-page-label');
  if (lbl) lbl.textContent = labels[page] || page;

  // For AI Assistant: content-area must not scroll (chat manages its own scroll)
  const ca = document.getElementById('content-area');
  if (ca) {
    if (page === 'assistant') {
      ca.classList.add('no-scroll');
    } else {
      ca.classList.remove('no-scroll');
    }
  }
  // Auto-close notification & settings panels when navigating
  document.getElementById('notif-panel')?.classList.add('hidden');
  document.getElementById('settings-panel')?.classList.add('hidden');

  const loaders = {
    overview: loadOverview, live: () => {},
    defects: loadDefects, patterns: loadPatterns, rootcause: loadRootCause,
    predictions: loadPredictions, anomalies: loadAnomalies,
    recommendations: loadRecommendations,
  };
  if (loaders[page]) loaders[page]();
}

function refreshCurrentPage() { navigateTo(_currentPage); }

function toggleSidebar() {
  const sb = document.getElementById('sidebar');
  sb.classList.toggle('collapsed');
  const compact = document.getElementById('set-compact');
  if (compact) compact.checked = sb.classList.contains('collapsed');
}

function toggleSettings() {
  const panel = document.getElementById('settings-panel');
  if (panel) panel.classList.toggle('hidden');
  // Close notifications if open
  const notifPanel = document.getElementById('notif-panel');
  if (notifPanel && !notifPanel.classList.contains('hidden') && !document.getElementById('settings-panel').classList.contains('hidden')) {
    notifPanel.classList.add('hidden');
  }
}
window.toggleSettings = toggleSettings;

function setAccent(color, el) {
  document.documentElement.style.setProperty('--az-blue', color);
  // Derive a lighter version for az-blue-lt
  document.querySelectorAll('.color-swatches .swatch').forEach(s => s.classList.remove('active'));
  if (el) el.classList.add('active');
}
window.setAccent = setAccent;

function settingChanged(key, val) {
  if (key === 'refresh') {
    clearInterval(_autoRefreshTimer);
    const secs = parseInt(val);
    if (secs > 0) {
      _autoRefreshTimer = setInterval(() => { if (_currentPage === 'overview') loadOverview(); }, secs * 1000);
    }
  }
}
window.settingChanged = settingChanged;

function toggleNotifPanel() {
  const panel = document.getElementById('notif-panel');
  panel.classList.toggle('hidden');
  // Reset badge when opening
  if (!panel.classList.contains('hidden')) {
    const badge = document.getElementById('notif-badge');
    if (badge) { badge.textContent = '0'; badge.dataset.count = '0'; }
  }
}

// ── Loading Screen ──────────────────────────────────────────────
let _loadProgress = 0;
function setLoadProgress(pct, msg) {
  _loadProgress = pct;
  const bar = document.getElementById('loader-bar');
  const txt = document.getElementById('loader-msg');
  if (bar) bar.style.width = `${pct}%`;
  if (txt) txt.textContent = msg;
}

function hideLoadingScreen() {
  const ls = document.getElementById('loading-screen');
  if (ls) {
    ls.style.opacity = '0';
    setTimeout(() => ls.classList.add('hidden'), 600);
  }
}

// ── Toast ────────────────────────────────────────────────────────
function showToast(msg, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.innerHTML = `<span>${icons[type] || 'ℹ️'}</span> ${msg}`;
  container.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 300); }, duration);
}
window.showToast = showToast;

// ── Clock ────────────────────────────────────────────────────────
function updateClock() {
  const el = document.getElementById('topbar-clock');
  if (el) {
    const now = new Date();
    el.textContent = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  }
}

// ── Particle Canvas (landing background) ────────────────────────
function initParticles() {
  const canvas = document.getElementById('particle-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let W, H, particles = [];

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  class Particle {
    constructor() { this.reset(); }
    reset() {
      this.x  = Math.random() * W;
      this.y  = Math.random() * H;
      this.vx = (Math.random() - 0.5) * 0.4;
      this.vy = (Math.random() - 0.5) * 0.4;
      this.r  = Math.random() * 1.5 + 0.5;
      this.a  = Math.random() * 0.5 + 0.1;
    }
    update() {
      this.x += this.vx; this.y += this.vy;
      if (this.x < 0 || this.x > W || this.y < 0 || this.y > H) this.reset();
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(0, 120, 212, ${this.a})`;
      ctx.fill();
    }
  }

  for (let i = 0; i < 80; i++) particles.push(new Particle());

  function draw() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => { p.update(); p.draw(); });

    // Draw connections
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(0, 120, 212, ${0.15 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.8;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(draw);
  }
  draw();
}

// ── Live UI Helpers ───────────────────────────────────────────────

/** Returns HTML for the data-source legend row */
function srcLegend(sources = ['real','synth','live']) {
  const defs = {
    real:  { color: '#F87171', label: 'Real (DeepPCB)' },
    synth: { color: '#50E6FF', label: 'Synthetic (10K)' },
    live:  { color: '#00C878', label: 'Live (WebSocket)' },
  };
  return `<div class="data-legend">${sources.map(s => `
    <div class="data-legend-item">
      <div class="dl-dot" style="background:${defs[s].color};"></div>
      <span>${defs[s].label}</span>
    </div>`).join('')}</div>`;
}

/** Returns HTML for the improvement banner, filled from live metrics */
function improvementBannerHTML() {
  return `
  <div class="improvement-banner" id="imp-banner">
    <div class="imp-item">
      <div class="imp-label">Yield Gained</div>
      <div class="imp-val" data-imp-yield>+0.00%</div>
    </div>
    <div class="imp-divider"></div>
    <div class="imp-item">
      <div class="imp-label">Defects Reduced</div>
      <div class="imp-val" data-imp-defects>-0.000</div>
    </div>
    <div class="imp-divider"></div>
    <div class="imp-item">
      <div class="imp-label">Anomalies Down</div>
      <div class="imp-val" data-imp-anomalies>-0.0%</div>
    </div>
    <div class="imp-divider"></div>
    <div class="imp-item">
      <div class="imp-label">Est. Cost Saved</div>
      <div class="imp-val" data-imp-savings>$0</div>
    </div>
    <div style="margin-left:auto;font-size:0.72rem;color:var(--text-muted);">
      AI recommendations applied — live improvement tracking
    </div>
  </div>`;
}

/** Returns HTML for the live-update footer bar */
function liveUpdateBarHTML(sources = ['real','synth','live'], intervalSec = 20) {
  return `
  <div class="live-update-bar">
    <div class="lub-sources">
      ${srcLegend(sources)}
    </div>
    <div class="lub-refresh">
      <div class="page-refresh-ring spinning"></div>
      <span>Auto-refresh in <span class="lub-countdown" data-seconds="${intervalSec}">20s</span></span>
      &nbsp;|&nbsp;
      Updated: <span class="lub-ts">--:--:--</span>
      &nbsp;|&nbsp;
      <span class="lub-readings">0 WS readings</span>
      &nbsp;|&nbsp;
      Status: <span class="lub-improvement">Baseline</span>
    </div>
  </div>`;
}

/** Inject improvement banner + live bar into a page section */
function injectLiveUI(pageId, sources, intervalSec = 20, showImprovementBanner = false) {
  const page = document.getElementById(pageId);
  if (!page) return;
  // Remove old ones first
  page.querySelectorAll('.imp-banner-wrap,.live-update-bar').forEach(el => el.remove());

  const wrap = document.createElement('div');
  wrap.className = 'imp-banner-wrap';
  wrap.innerHTML = (showImprovementBanner ? improvementBannerHTML() : '') +
                   liveUpdateBarHTML(sources, intervalSec);
  page.appendChild(wrap);

  // Immediately sync with last known metrics
  if (typeof liveData !== 'undefined') {
    const m = liveData.getLastMetrics?.();
    if (m) {
      if (showImprovementBanner) {
        wrap.querySelector('[data-imp-yield]')?.setAttribute('data-imp-yield', '');
        wrap.querySelector('[data-imp-yield]').textContent = `+${m.improvement_summary.yield_gained}%`;
        wrap.querySelector('[data-imp-defects]').textContent = `-${m.improvement_summary.defects_reduced}`;
        wrap.querySelector('[data-imp-anomalies]').textContent = `-${m.improvement_summary.anomalies_reduced}%`;
        wrap.querySelector('[data-imp-savings]').textContent = `$${m.improvement_summary.est_cost_saved.toLocaleString()}`;
      }
    }
    wrap.querySelector('.lub-readings').textContent = `${liveData.getReadingCount()} WS readings`;
    wrap.querySelector('.lub-ts').textContent = new Date().toLocaleTimeString('en-US', { hour12: false });
  }
}

// ── Counter Animation ─────────────────────────────────────────────
function animateCounter(el, target, suffix = '', duration = 800) {
  if (!el) return;
  const start = parseFloat(el.textContent.replace(/[^\d.]/g, '')) || 0;
  const range = target - start;
  const steps = 30;
  let step = 0;
  const timer = setInterval(() => {
    step++;
    const progress = step / steps;
    const ease = 1 - Math.pow(1 - progress, 3);
    const val = start + range * ease;
    el.textContent = (Number.isInteger(target) ? Math.round(val).toLocaleString() : val.toFixed(1)) + suffix;
    if (step >= steps) clearInterval(timer);
  }, duration / steps);
}

// ═══════════════════════════════════════════════════════════════
// PAGE: OVERVIEW
// ═══════════════════════════════════════════════════════════════
async function loadOverview() {
  ['v-health','v-defects','v-yield','v-alerts','v-records'].forEach(id => {
    const el = document.getElementById(id);
    if (el && (el.textContent === '--' || el.textContent === '…')) el.textContent = '…';
  });
  // Inject live UI immediately (doesn't wait for slow API)
  injectLiveUI('page-overview', ['real','synth','live'], 30, true);
  try {
    _dashData = await api.dashboardSummary();
    const d   = _dashData;

    // KPIs with counter animation
    const healthEl   = document.getElementById('v-health');
    const defectsEl  = document.getElementById('v-defects');
    const yieldEl    = document.getElementById('v-yield');
    const alertsEl   = document.getElementById('v-alerts');
    const recordsEl  = document.getElementById('v-records');

    if (healthEl)  animateCounter(healthEl,  d.health_score.overall_score, '');
    if (defectsEl) animateCounter(defectsEl, d.total_defects);
    if (yieldEl)   animateCounter(yieldEl,   d.avg_yield, '%');
    if (alertsEl)  animateCounter(alertsEl,  d.active_alerts);
    if (recordsEl) animateCounter(recordsEl, d.total_inspections);

    // Delta labels
    _set('d-health', `Grade: ${d.health_score.grade} · ${d.health_score.trend === 'improving' ? '↑ Improving' : d.health_score.trend === 'declining' ? '↓ Declining' : '→ Stable'}`);
    _set('d-defects', `Defect rate: ${d.defect_rate}%`);
    _set('d-yield', `${d.avg_yield >= 90 ? '↑ Above target' : '↓ Below 90% target'}`);
    _set('d-alerts', `${d.anomaly_summary?.anomaly_rate_pct || 0}% anomaly rate`);
    _set('d-records', `10K synthetic + DeepPCB`);

    // Health badge
    const grade = d.health_score.grade;
    const gradeBadge = document.getElementById('health-grade-badge');
    if (gradeBadge) {
      gradeBadge.textContent = `Grade ${grade}`;
      gradeBadge.className = `badge ${grade === 'A' ? 'badge-success' : grade === 'B' ? 'badge-info' : grade === 'C' ? 'badge-warning' : 'badge-danger'}`;
    }

    // Health score display
    renderHealthScore(d.health_score);

    // Charts
    const timeline = await api.timeline();
    if (timeline.length) charts.timeline('chart-timeline', timeline);
    if (d.defect_distribution) charts.defectDonut('chart-defect-dist', d.defect_distribution);
    if (d.hourly_trends) charts.hourlyTrend('chart-hourly', d.hourly_trends);
    if (d.machine_status) charts.machineBars('chart-machines', d.machine_status);
    if (d.shift_analysis) charts.shiftComparison('chart-shifts', d.shift_analysis);

    // Machine table
    renderMachineTable(d.machine_status);

    // Patterns preview
    renderPatternCards('overview-patterns', d.top_patterns, 3);

    // Recs preview
    renderRecCards('overview-recs', d.top_recommendations, 3, true);

  } catch (err) {
    console.error('Overview error:', err);
    showToast('Failed to load dashboard data — is the server running?', 'error');
  }
}

function renderHealthScore(health) {
  const el = document.getElementById('health-display');
  if (!el) return;

  const score = health.overall_score;
  const color = score >= 80 ? '#00C878' : score >= 60 ? '#FFB900' : '#D13438';
  const r = 60, circumference = 2 * Math.PI * r;
  const dashOffset = circumference - (circumference * score / 100);

  el.innerHTML = `
    <div class="health-wrap">
      <div class="health-ring">
        <svg width="140" height="140" viewBox="0 0 140 140">
          <circle class="health-ring-bg" cx="70" cy="70" r="${r}"/>
          <circle class="health-ring-fill"
            cx="70" cy="70" r="${r}"
            stroke="${color}"
            stroke-dasharray="${circumference}"
            stroke-dashoffset="${dashOffset}"/>
        </svg>
        <div class="health-center">
          <div class="health-score-val" style="color:${color}">${score}</div>
          <div class="health-grade" style="color:${color}">${health.grade}</div>
          <div class="health-label">Health</div>
        </div>
      </div>
      <div class="health-components">
        ${(health.components || []).map(c => {
          const cc = c.score >= 80 ? '#00C878' : c.score >= 60 ? '#FFB900' : '#D13438';
          return `<div class="health-comp">
            <span class="hc-name">${c.component}</span>
            <div class="hc-bar"><div class="hc-fill" style="width:${c.score}%;background:${cc};"></div></div>
            <span class="hc-score" style="color:${cc}">${c.score}</span>
          </div>`;
        }).join('')}
      </div>
    </div>`;
}

function renderMachineTable(machines) {
  const el = document.getElementById('machine-table');
  if (!el || !machines) return;
  el.innerHTML = `
    <table class="data-table">
      <thead><tr><th>Machine</th><th>Status</th><th>Avg Defects</th><th>Yield</th><th>Downtime</th></tr></thead>
      <tbody>
        ${machines.map(m => `
          <tr>
            <td><strong>${m.machine_id}</strong></td>
            <td>
              <span class="status-dot s-${m.status === 'healthy' ? 'healthy' : m.status === 'warning' ? 'warning' : 'critical'}"></span>
              ${m.status}
            </td>
            <td class="mono">${m.avg_defects}</td>
            <td class="mono">${m.avg_yield}%</td>
            <td class="mono">${m.total_downtime} min</td>
          </tr>`).join('')}
      </tbody>
    </table>`;
}

// ═══════════════════════════════════════════════════════════════
// PAGE: DEFECTS
// ═══════════════════════════════════════════════════════════════
async function loadDefects() {
  injectLiveUI('page-defects', ['real','synth','live'], 25, true);
  try {
    // Fetch both base stats AND live mixed defect data in parallel
    const [stats, liveDefects] = await Promise.all([
      api.defectStats(),
      fetch('/api/live/defects').then(r => r.json()).catch(() => null),
    ]);

    // KPIs
    const kpis = [
      { label: 'Images Analyzed',      val: stats.total_images_analyzed,  color: '#0078D4', icon: '🔬' },
      { label: 'Defects Found',         val: stats.total_defects_found,    color: '#EF4444', icon: '⚠️' },
      { label: 'Avg Defects/Image',     val: stats.avg_defects_per_image,  color: '#FFB900', icon: '📊' },
      { label: 'Avg Analysis Time (ms)',val: stats.avg_analysis_time_ms,   color: '#00C878', icon: '⚡' },
    ];
    document.getElementById('defect-kpis').innerHTML = kpis.map(k => `
      <div class="kpi-card">
        <div class="kpi-icon" style="background:${k.color}18;font-size:1.4rem;">${k.icon}</div>
        <div class="kpi-body">
          <div class="kpi-label">${k.label}</div>
          <div class="kpi-value">${typeof k.val === 'number' ? k.val.toLocaleString() : k.val}</div>
        </div>
      </div>`).join('');

    // Use live combined counts if available, fallback to static stats
    const liveDist = liveDefects?.combined || stats.defect_type_distribution;
    if (liveDist) charts.defectDonut('chart-cv-defects', liveDist);

    // Source breakdown KPI (real vs synthetic vs live)
    const totalReal  = liveDefects ? Object.values(liveDefects.real_data || []).reduce((a,b) => a + (b.count||0), 0) : 10013;
    const totalSynth = liveDefects ? Object.values(liveDefects.synthetic_data || []).reduce((a,b) => a + (b.count||0), 0) : 9580;
    const totalLive  = liveDefects ? Object.values(liveDefects.live_data || []).reduce((a,b) => a + (b.count||0), 0) : 0;
    const totalAll   = totalReal + totalSynth + totalLive;
    document.getElementById('defect-kpis').innerHTML = [
      { label: 'Images Analyzed',      val: stats.total_images_analyzed,  color: '#0078D4',  src: 'real',  icon: '&#128302;' },
      { label: 'Defects Found',         val: totalAll,                     color: '#EF4444',  src: 'mixed', icon: '&#9888;' },
      { label: 'Real (DeepPCB)',        val: totalReal,                    color: '#F87171',  src: 'real',  icon: '&#128247;' },
      { label: 'Synthetic',            val: totalSynth,                    color: '#50E6FF',  src: 'synth', icon: '&#129302;' },
    ].map(k => `
      <div class="kpi-card">
        <div class="kpi-icon" style="background:${k.color}18;font-size:1.3rem;">${k.icon}</div>
        <div class="kpi-body">
          <div class="kpi-label" style="display:flex;align-items:center;gap:6px;">
            ${k.label} <span class="src-badge src-${k.src}">${k.src}</span>
          </div>
          <div class="kpi-value">${typeof k.val === 'number' ? k.val.toLocaleString() : k.val}</div>
        </div>
      </div>`).join('');

    // Severity bars
    const sev = stats.severity_distribution || {};
    const maxSev = Math.max(...Object.values(sev), 1);
    document.getElementById('severity-display').innerHTML = `
      <h4 style="font-size:0.88rem;margin-bottom:1rem;color:var(--text-secondary);">Severity Breakdown</h4>
      ${['critical','high','medium','low'].map(s => {
        const cnt = sev[s] || 0;
        const colors = { critical: '#D13438', high: '#FFB900', medium: '#0078D4', low: '#00C878' };
        return `
        <div style="margin-bottom:14px;">
          <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
            <span style="font-size:0.82rem;font-weight:500;color:${colors[s]};text-transform:capitalize;">${s}</span>
            <span class="mono" style="font-size:0.8rem;">${cnt.toLocaleString()}</span>
          </div>
          <div class="prog-bar"><div class="prog-fill" style="width:${(cnt/maxSev)*100}%;background:${colors[s]};"></div></div>
        </div>`;
      }).join('')}`;

    // Defect type encyclopedia with live counts
    const defectInfo = {
      open:            { icon: '&#128275;', desc: 'Missing copper causing open circuit. Often linked to high vibration during soldering.' },
      short:           { icon: '&#9889;',  desc: 'Unintended copper bridge between tracks. Common during high-speed PCB production.' },
      mousebite:       { icon: '&#129405;',desc: 'Small notch defect at PCB edge. Correlated with high humidity + temperature.' },
      spur:            { icon: '&#128204;',desc: 'Unwanted protrusion of copper. Caused by temperature excursions in solder mask.' },
      pinhole:         { icon: '&#127919;',desc: 'Tiny void in copper layer. Linked to calibration drift over time.' },
      spurious_copper: { icon: '&#129693;',desc: 'Unintended copper deposit. Occurs at high conveyor speeds on PCB-Gamma line.' },
    };
    document.getElementById('defect-type-grid').innerHTML = Object.entries(defectInfo).map(([type, info]) => {
      const liveCount  = liveDefects?.live_data?.find(d => d.type === type)?.count || 0;
      const realCount  = liveDefects?.real_data?.find(d => d.type === type)?.count || stats.defect_type_distribution?.[type] || 0;
      return `
      <div class="defect-type-card">
        <div class="dt-icon">${info.icon}</div>
        <div class="dt-name" style="color:${charts.DEFECT_COLORS[type]}">${type.replace('_',' ')}</div>
        <div class="dt-desc">${info.desc}</div>
        <div style="display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;">
          <span class="src-badge src-real">${realCount.toLocaleString()} real</span>
          ${liveCount > 0 ? `<span class="src-badge src-live">${liveCount} live</span>` : ''}
        </div>
      </div>`;
    }).join('');

  } catch (err) {
    console.error('Defects error:', err);
    showToast('Failed to load defect data', 'error');
  }
}

// ═══════════════════════════════════════════════════════════════
// PAGE: PATTERNS
// ═══════════════════════════════════════════════════════════════
async function loadPatterns() {
  injectLiveUI('page-patterns', ['synth','live'], 60);
  try {
    const result = await api.patterns();
    _set('pattern-count', result.total_patterns);
    renderPatternCards('patterns-container', result.patterns, 50);
  } catch (err) {
    console.error('Patterns error:', err);
    showToast('Failed to load patterns', 'error');
  }
}

function renderPatternCards(containerId, patterns, limit) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const items = (patterns || []).slice(0, limit);
  if (!items.length) { el.innerHTML = '<p style="color:var(--text-muted);padding:1rem;">No patterns discovered yet. Generate data first.</p>'; return; }

  el.innerHTML = items.map(p => {
    const severity = p.severity || 'medium';
    const badgeClass = severity === 'critical' ? 'badge-danger' : severity === 'high' ? 'badge-warning' : 'badge-info';
    const conf = ((p.confidence || 0) * 100).toFixed(0);
    return `
    <div class="insight-card">
      <div class="insight-header">
        <span class="insight-title">${(p.affected_factor || '').replace(/_/g,' ').replace(/\b\w/g,l=>l.toUpperCase())}</span>
        <span class="badge ${badgeClass}">${severity}</span>
      </div>
      <div class="insight-desc">${p.description || ''}</div>
      <div class="insight-meta">
        <span>Correlation: ${p.correlation_strength || '--'}</span>
        <span>Confidence: ${conf}%</span>
        ${p.pattern_type ? `<span>Type: ${p.pattern_type}</span>` : ''}
      </div>
      <div class="prog-bar" style="margin-top:8px;">
        <div class="prog-fill" style="width:${conf}%;"></div>
      </div>
    </div>`;
  }).join('');
}

// ═══════════════════════════════════════════════════════════════
// PAGE: ROOT CAUSE
// ═══════════════════════════════════════════════════════════════
async function loadRootCause() {
  injectLiveUI('page-rootcause', ['synth','live'], 45);
  try {
    const rc = await api.rootCause();
    _set('rc-confidence', `${((rc.confidence || 0) * 100).toFixed(0)}%`);
    const methodBadge = document.getElementById('rc-method-badge');
    if (methodBadge) { methodBadge.textContent = rc.methodology || '--'; }

    if (rc.factors?.length) charts.rootCausePie('chart-rootcause', rc.factors);

    document.getElementById('rc-factors').innerHTML = (rc.factors || []).map(f => `
      <div class="insight-card">
        <div class="insight-header">
          <span class="insight-title">${f.factor}</span>
          <span class="badge ${f.contribution_pct > 25 ? 'badge-danger' : f.contribution_pct > 15 ? 'badge-warning' : 'badge-info'}">${f.contribution_pct}%</span>
        </div>
        <div class="insight-desc">${f.description || ''}</div>
        <div class="prog-bar"><div class="prog-fill" style="width:${f.contribution_pct}%;"></div></div>
      </div>`).join('');

    // SHAP table
    if (rc.shap_explanations?.length) {
      document.getElementById('shap-table').innerHTML = `
        <table class="data-table">
          <thead><tr><th>Feature</th><th>SHAP Value</th><th>Direction</th><th>Impact</th></tr></thead>
          <tbody>
            ${rc.shap_explanations.slice(0, 10).map(s => {
              const pct = Math.min(Math.abs(s.shap_value) * 30, 100);
              return `<tr>
                <td>${s.feature_name}</td>
                <td class="mono">${s.shap_value.toFixed(4)}</td>
                <td style="color:${s.direction==='increases'?'#EF4444':'#00C878'}">
                  ${s.direction === 'increases' ? '↑ Increases' : '↓ Decreases'} defects
                </td>
                <td style="width:120px;">
                  <div class="prog-bar"><div class="prog-fill" style="width:${pct}%;background:${s.direction==='increases'?'#EF4444':'#00C878'};"></div></div>
                </td>
              </tr>`;
            }).join('')}
          </tbody>
        </table>`;
    }
  } catch (err) {
    console.error('Root cause error:', err);
    showToast('Failed to load root cause analysis', 'error');
  }
}

// ═══════════════════════════════════════════════════════════════
// PAGE: PREDICTIONS
// ═══════════════════════════════════════════════════════════════
async function loadPredictions() {
  injectLiveUI('page-predictions', ['synth','live'], 45, true);
  // Show inline spinner while XGBoost trains (first-load can take ~60s)
  const kpiEl = document.getElementById('pred-kpis');
  if (kpiEl && (!kpiEl.innerHTML || kpiEl.innerHTML.trim() === '')) {
    kpiEl.innerHTML = `
      <div style="display:flex;align-items:center;gap:1rem;padding:1.5rem;color:var(--text-2);">
        <div class="loader-ring" style="width:28px;height:28px;border-width:3px;"></div>
        <div>
          <div style="font-weight:600;color:var(--text);">Training XGBoost model…</div>
          <div style="font-size:0.8rem;margin-top:2px;">First load trains on 10K records — takes ~30s, then cached for 10 min</div>
        </div>
      </div>`;
  }
  try {
    const pred = await api.predictions();
    const f    = pred.forecast;
    if (!f) return;

    // KPIs
    document.getElementById('pred-kpis').innerHTML = [
      { label: 'Machines at Risk', val: f.machines_at_risk, color: '#D13438', icon: '⚠️' },
      { label: 'Predicted Avg Yield', val: `${f.avg_predicted_yield?.toFixed(1)}%`, color: '#00C878', icon: '📈' },
      { label: 'Highest Risk Machine', val: f.highest_risk_machine || 'N/A', color: '#FFB900', icon: '🎯' },
    ].map(k => `
      <div class="kpi-card">
        <div class="kpi-icon" style="background:${k.color}18;font-size:1.4rem;">${k.icon}</div>
        <div class="kpi-body">
          <div class="kpi-label">${k.label}</div>
          <div class="kpi-value">${k.val}</div>
        </div>
      </div>`).join('');

    // Machine table
    if (f.machine_forecasts) {
      document.getElementById('pred-machine-table').innerHTML = `
        <table class="data-table">
          <thead><tr><th>Machine</th><th>Pred. Defects</th><th>Pred. Yield</th><th>Failure Risk</th><th>Risk Level</th></tr></thead>
          <tbody>
            ${f.machine_forecasts.map(m => {
              const risk = m.overall_risk || 'low';
              return `<tr>
                <td><strong>${m.machine_id}</strong></td>
                <td class="mono">${m.predicted_defects.toFixed(1)}</td>
                <td class="mono">${m.predicted_yield.toFixed(1)}%</td>
                <td>
                  <div class="prog-bar" style="width:80px;display:inline-block;">
                    <div class="prog-fill" style="width:${m.failure_risk_pct}%;background:${m.failure_risk_pct>60?'#D13438':m.failure_risk_pct>30?'#FFB900':'#00C878'};"></div>
                  </div>
                  <span class="mono" style="font-size:0.78rem;"> ${m.failure_risk_pct.toFixed(0)}%</span>
                </td>
                <td>
                  <span class="badge ${risk==='critical'||risk==='high'?'badge-danger':risk==='medium'?'badge-warning':'badge-success'}">
                    ${risk}
                  </span>
                </td>
              </tr>`;
            }).join('')}
          </tbody>
        </table>`;

      // Predictions chart
      charts.predictions('chart-predictions', f.machine_forecasts);
    }

    // Model metrics
    if (pred.training?.results) {
      document.getElementById('model-metrics').innerHTML = Object.entries(pred.training.results).map(([name, metrics]) => `
        <div class="insight-card" style="margin-bottom:0.5rem;">
          <div class="insight-header">
            <span class="insight-title">${name.replace(/_/g,' ').replace(/\b\w/g,l=>l.toUpperCase())}</span>
            <span class="badge badge-success">Trained</span>
          </div>
          <div style="font-size:1.8rem;font-weight:800;font-family:var(--font-mono);color:var(--az-blue-light);margin:4px 0;">
            ${Object.values(metrics)[0].toFixed(3)}
          </div>
          <div class="insight-meta">
            ${Object.entries(metrics).map(([k,v]) => `<span>${k.toUpperCase()}: ${v.toFixed(3)}</span>`).join('')}
          </div>
        </div>`).join('');
    }
  } catch (err) {
    console.error('Predictions error:', err);
    showToast('Failed to load predictions', 'error');
  }
}

// ═══════════════════════════════════════════════════════════════
// PAGE: ANOMALIES
// ═══════════════════════════════════════════════════════════════
async function loadAnomalies() {
  injectLiveUI('page-anomalies', ['synth','live'], 20, false);
  try {
    // Fetch base + live metrics together
    const [summary, liveM] = await Promise.all([
      api.anomalySummary(),
      fetch('/api/live/metrics').then(r => r.json()).catch(() => null),
    ]);
    // Patch live anomaly rate if available
    if (liveM) summary.anomaly_rate_pct = liveM.kpis.anomaly_pct;

    document.getElementById('anomaly-kpis').innerHTML = [
      { label: 'Flagged Anomalies', val: summary.flagged_anomalies, color: '#D13438', icon: '🚨' },
      { label: 'Anomaly Rate',      val: `${summary.anomaly_rate_pct}%`, color: '#FFB900', icon: '📊' },
      { label: 'Total Records',     val: summary.total_records?.toLocaleString(), color: '#0078D4', icon: '📋' },
    ].map(k => `
      <div class="kpi-card">
        <div class="kpi-icon" style="background:${k.color}18;font-size:1.4rem;">${k.icon}</div>
        <div class="kpi-body">
          <div class="kpi-label">${k.label}</div>
          <div class="kpi-value">${k.val}</div>
        </div>
      </div>`).join('');

    if (summary.per_machine) charts.anomalyMachines('chart-anomaly-machines', summary.per_machine);

    // Sensor breaches
    const breaches = summary.per_sensor_breaches || {};
    document.getElementById('sensor-breaches').innerHTML = Object.entries(breaches).map(([sensor, v]) => `
      <div class="insight-card">
        <div class="insight-header">
          <span class="insight-title">${sensor} Threshold Breaches</span>
          <span class="badge ${v.rate_pct > 15 ? 'badge-danger' : v.rate_pct > 5 ? 'badge-warning' : 'badge-success'}">${v.count}</span>
        </div>
        <div class="insight-desc">Threshold: <strong>${v.threshold}</strong> · Breach rate: <strong>${v.rate_pct}%</strong></div>
        <div class="prog-bar">
          <div class="prog-fill" style="width:${Math.min(v.rate_pct * 3, 100)}%;background:${v.rate_pct > 15 ? '#D13438' : '#FFB900'};"></div>
        </div>
      </div>`).join('');

    // Machine anomaly table
    const tbody = document.getElementById('anomaly-tbody');
    if (tbody && summary.per_machine) {
      tbody.innerHTML = Object.entries(summary.per_machine).map(([id, v]) => `
        <tr>
          <td><strong>${id}</strong></td>
          <td class="mono">${v.anomaly_count}</td>
          <td class="mono">${v.anomaly_rate}%</td>
          <td>${v.top_sensor || '--'}</td>
          <td>
            <span class="badge ${parseFloat(v.anomaly_rate) > 25 ? 'badge-danger' : parseFloat(v.anomaly_rate) > 15 ? 'badge-warning' : 'badge-success'}">
              ${parseFloat(v.anomaly_rate) > 25 ? 'Critical' : parseFloat(v.anomaly_rate) > 15 ? 'Warning' : 'Normal'}
            </span>
          </td>
        </tr>`).join('');
    }
  } catch (err) {
    console.error('Anomalies error:', err);
    showToast('Failed to load anomaly data', 'error');
  }
}

// ═══════════════════════════════════════════════════════════════
// PAGE: RECOMMENDATIONS
// ═══════════════════════════════════════════════════════════════
async function loadRecommendations() {
  injectLiveUI('page-recommendations', ['synth','live'], 30, true);
  try {
    const result = await api.recommendations();
    _set('rec-count', result.total_recommendations);
    renderRecCards('recs-container', result.recommendations, 50);
  } catch (err) {
    console.error('Recommendations error:', err);
    showToast('Failed to load recommendations', 'error');
  }
}

function renderRecCards(containerId, recs, limit, compact = false) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const items = (recs || []).slice(0, limit);
  if (!items.length) { el.innerHTML = '<p style="color:var(--text-muted);padding:1rem;">No recommendations yet.</p>'; return; }

  if (compact) {
    el.innerHTML = items.map(r => `
      <div class="rec-card priority-${r.priority}">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.5rem;">
          <div class="rec-title">${r.title}</div>
          <span class="badge ${r.priority==='critical'?'badge-danger':r.priority==='high'?'badge-warning':'badge-info'}">${r.priority}</span>
        </div>
        <div class="rec-impact">💡 ${r.estimated_impact}</div>
      </div>`).join('');
  } else {
    el.innerHTML = items.map(r => `
      <div class="rec-card priority-${r.priority}">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.5rem;margin-bottom:0.5rem;">
          <div class="rec-title">${r.title}</div>
          <span class="badge ${r.priority==='critical'?'badge-danger':r.priority==='high'?'badge-warning':'badge-info'}">${r.priority}</span>
        </div>
        <div class="rec-desc">${r.description}</div>
        <div class="rec-impact">💡 ${r.estimated_impact}${r.machine_id ? ` · Machine: <strong>${r.machine_id}</strong>` : ''}</div>
      </div>`).join('');
  }
}

// ═══════════════════════════════════════════════════════════════
// AI ASSISTANT
// ═══════════════════════════════════════════════════════════════
async function sendChat() {
  const input   = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send-btn');
  const messages = document.getElementById('chat-messages');
  const question = (input?.value || '').trim();
  if (!question) return;

  // User message
  appendChatMsg(question, 'user');
  input.value = '';
  if (sendBtn) sendBtn.disabled = true;

  // Typing indicator
  const typingId = 'typing-' + Date.now();
  const typingEl = document.createElement('div');
  typingEl.id = typingId;
  typingEl.className = 'chat-msg ai-msg';
  typingEl.innerHTML = `
    <div class="ai-avatar">AI</div>
    <div class="chat-bubble ai-bubble">
      <div class="typing-indicator">
        <div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>
      </div>
    </div>`;
  messages.appendChild(typingEl);
  messages.scrollTop = messages.scrollHeight;

  try {
    const res = await api.aiQuery(question);

    // Remove typing indicator
    typingEl.remove();

    // Build AI response
    const actionsHtml = res.recommended_actions?.length
      ? `<div class="ai-actions">${res.recommended_actions.map(a => `<div class="ai-action-item">${a}</div>`).join('')}</div>`
      : '';

    const confPct = Math.round((res.confidence || 0) * 100);
    const confHtml = `
      <div class="ai-confidence">
        <span>AI Confidence: ${confPct}%</span>
        <div class="confidence-bar"><div class="confidence-fill" style="width:${confPct}%;"></div></div>
      </div>`;

    appendChatMsg(res.answer + actionsHtml + confHtml, 'ai');

    // Update context panel
    _set('ai-last-conf', `${confPct}%`);
    _set('ai-last-time', new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }));

  } catch (err) {
    typingEl.remove();
    appendChatMsg('Sorry, I encountered an error. Please check that the backend is running.', 'ai');
  }

  if (sendBtn) sendBtn.disabled = false;
}

function appendChatMsg(content, role) {
  const messages = document.getElementById('chat-messages');
  if (!messages) return;

  const el = document.createElement('div');
  el.className = `chat-msg ${role}-msg`;
  el.innerHTML = role === 'user'
    ? `<div class="chat-bubble user-bubble">${content}</div><div class="ai-avatar" style="background:rgba(0,120,212,0.3);">You</div>`
    : `<div class="ai-avatar">AI</div><div class="chat-bubble ai-bubble">${content}</div>`;

  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
}

function askQuestion(q) {
  const input = document.getElementById('chat-input');
  if (input) input.value = q;
  sendChat();
}
window.askQuestion = askQuestion;

// ── Utility ─────────────────────────────────────────────────────
function _set(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

// ═══════════════════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════════════════
async function initApp() {
  initParticles();
  updateClock();
  setInterval(updateClock, 1000);

  document.querySelectorAll('.sb-link[data-page]').forEach(link => {
    link.addEventListener('click', () => navigateTo(link.dataset.page));
  });
  document.getElementById('btn-launch')?.addEventListener('click', launchDashboard);

  // Animate loading bar
  setLoadProgress(40, 'Loading NexSight AI...');
  await new Promise(r => setTimeout(r, 350));
  setLoadProgress(80, 'Preparing interface...');
  await new Promise(r => setTimeout(r, 350));
  setLoadProgress(100, 'Ready!');
  await new Promise(r => setTimeout(r, 400));
  hideLoadingScreen();

  // Show login screen if not authenticated
  if (!checkAuth()) {
    const ls = document.getElementById('login-screen');
    if (ls) ls.classList.remove('hidden');
    // Focus username field
    setTimeout(() => document.getElementById('login-user')?.focus(), 100);
  }
  // If already authenticated, update avatar with stored username
  const storedUser = localStorage.getItem('nx_user');
  if (storedUser) {
    const av = document.querySelector('.topbar-avatar');
    if (av) av.textContent = storedUser.slice(0, 2).toUpperCase();
  }
}

async function launchDashboard() {
  const landing   = document.getElementById('landing');
  const dashboard = document.getElementById('dashboard');
  const btn       = document.getElementById('btn-launch');

  // Disable button and show spinner
  if (btn) { btn.disabled = true; btn.innerHTML = '<span style="opacity:0.7">Loading…</span>'; }

  try {
    const status = await api.dataStatus();

    if (!status.telemetry_loaded || status.telemetry_records === 0) {
      setLoadProgress(45, 'Generating synthetic manufacturing data...');
      await api.generateSynthetic();
      showToast('✅ 10K synthetic records generated!', 'success');
    }

    setLoadProgress(65, 'Loading AI analytics models...');
    await new Promise(r => setTimeout(r, 400));

    setLoadProgress(85, 'Initializing real-time feeds...');
    await new Promise(r => setTimeout(r, 300));

    setLoadProgress(100, 'Ready!');
    await new Promise(r => setTimeout(r, 400));

    // Transition to dashboard
    landing.classList.add('fade-out');
    setTimeout(() => {
      landing.classList.remove('active');
      landing.style.display = 'none';
      dashboard.classList.remove('hidden');
      hideLoadingScreen();

      // Start real-time
      liveData.init();

      // Load default page
      navigateTo('overview');

      // Auto-refresh every 60s
      _autoRefreshTimer = setInterval(() => {
        if (_currentPage === 'overview') loadOverview();
      }, 60000);

    }, 600);

  } catch (err) {
    console.error('Launch error:', err);
    setLoadProgress(0, 'Connection failed — retrying...');
    showToast('Backend connection failed. Start the server first!', 'error', 6000);
    setTimeout(hideLoadingScreen, 2000);
    // Still show dashboard but with error state
    landing.classList.remove('active');
    landing.style.display = 'none';
    dashboard.classList.remove('hidden');
    liveData.init();
    navigateTo('overview');
  }
}

// Start
document.addEventListener('DOMContentLoaded', initApp);
