/**
 * NexSight AI — Advanced Plotly Chart Library
 * Microsoft Azure color scheme + interactive features
 */

const CHARTS = (() => {

  // ── Azure Color Palette ──────────────────────────
  const AZURE_COLORS = [
    '#0078D4', '#50E6FF', '#00C878', '#FFB900',
    '#D13438', '#8764B8', '#4DA3FF', '#F3C846',
    '#00B294', '#EA4300',
  ];

  const DEFECT_COLORS = {
    open:            '#EF4444',
    short:           '#F97316',
    mousebite:       '#EAB308',
    spur:            '#0078D4',
    pinhole:         '#8B5CF6',
    spurious_copper: '#EC4899',
    none:            '#374151',
  };

  // ── Base layout ─────────────────────────────────
  function baseLayout(extra = {}) {
    return {
      paper_bgcolor: 'transparent',
      plot_bgcolor:  'transparent',
      font: { family: 'Inter, Segoe UI, sans-serif', color: '#8CA0BC', size: 11 },
      margin: { t: 15, r: 15, b: 35, l: 45 },
      legend: {
        font: { size: 11, color: '#8CA0BC' },
        bgcolor: 'transparent',
      },
      xaxis: {
        gridcolor: 'rgba(255,255,255,0.04)',
        linecolor: 'rgba(255,255,255,0.08)',
        tickcolor: 'rgba(255,255,255,0.08)',
        zerolinecolor: 'rgba(255,255,255,0.06)',
      },
      yaxis: {
        gridcolor: 'rgba(255,255,255,0.04)',
        linecolor: 'rgba(255,255,255,0.08)',
        tickcolor: 'rgba(255,255,255,0.08)',
        zerolinecolor: 'rgba(255,255,255,0.06)',
      },
      hovermode: 'x unified',
      hoverlabel: {
        bgcolor: 'rgba(6,10,20,0.95)',
        bordercolor: 'rgba(0,120,212,0.4)',
        font: { color: '#EDF2F7', size: 12, family: 'Inter, sans-serif' },
      },
      ...extra,
    };
  }

  const CONFIG = {
    responsive: true,
    displayModeBar: false,
    staticPlot: false,
  };

  function safeRender(id, traces, layout, config = CONFIG) {
    const el = document.getElementById(id);
    if (!el) return;
    try {
      Plotly.react(el, traces, layout, config);
    } catch (e) {
      console.warn('Chart error:', id, e);
    }
  }

  // ── TIMELINE ────────────────────────────────────
  function timeline(id, data) {
    if (!data || !data.length) return;
    const dates = data.map(d => d.date);

    const traces = [
      {
        x: dates, y: data.map(d => d.avg_defects),
        type: 'scatter', mode: 'lines',
        name: 'Avg Defects',
        line: { color: '#EF4444', width: 2 },
        fill: 'tozeroy', fillcolor: 'rgba(239,68,68,0.06)',
      },
      {
        x: dates, y: data.map(d => d.avg_yield),
        type: 'scatter', mode: 'lines',
        name: 'Yield %', yaxis: 'y2',
        line: { color: '#00C878', width: 2 },
      },
      {
        x: dates, y: data.map(d => d.anomaly_count),
        type: 'bar', name: 'Anomalies',
        marker: { color: 'rgba(255,185,0,0.5)', line: { width: 0 } },
        yaxis: 'y3',
      },
    ];

    const layout = baseLayout({
      margin: { t: 15, r: 60, b: 40, l: 50 },
      yaxis:  { title: { text: 'Defects', font: { size: 10 } }, gridcolor: 'rgba(255,255,255,0.04)', linecolor: 'rgba(255,255,255,0.08)' },
      yaxis2: { title: { text: 'Yield %', font: { size: 10 } }, overlaying: 'y', side: 'right', range: [60, 100], showgrid: false },
      yaxis3: { overlaying: 'y', side: 'right', showgrid: false, showticklabels: false, range: [0, data.map(d=>d.anomaly_count).reduce((a,b)=>Math.max(a,b),0)*8] },
      legend: { orientation: 'h', y: 1.08, x: 0 },
    });

    safeRender(id, traces, layout);
  }

  // ── DEFECT DISTRIBUTION (Donut) ──────────────────
  function defectDonut(id, dist) {
    if (!dist || !Object.keys(dist).length) return;
    const labels = Object.keys(dist).filter(k => k !== 'none');
    const values = labels.map(k => dist[k]);
    const colors = labels.map(k => DEFECT_COLORS[k] || '#555');

    safeRender(id, [{
      labels, values,
      type: 'pie', hole: 0.55,
      marker: { colors, line: { color: 'rgba(0,0,0,0.3)', width: 2 } },
      textfont: { size: 11 },
      hovertemplate: '<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>',
    }], baseLayout({
      margin: { t: 10, r: 10, b: 10, l: 10 },
      legend: { x: 0.5, y: -0.15, xanchor: 'center', orientation: 'h' },
      annotations: [{
        text: `${Object.values(dist).reduce((a,b) => a+b,0).toLocaleString()}<br><span style="font-size:10px">Total</span>`,
        x: 0.5, y: 0.5, showarrow: false,
        font: { size: 14, color: '#EDF2F7', family: 'Inter' },
        align: 'center',
      }],
    }));
  }

  // ── HOURLY TREND ─────────────────────────────────
  function hourlyTrend(id, data) {
    if (!data || !data.length) return;
    const hours = data.map(d => `${d.hour}:00`);
    safeRender(id, [
      {
        x: hours, y: data.map(d => d.avg_defects),
        type: 'bar',
        marker: {
          color: data.map(d => d.avg_defects > 3 ? '#EF4444' : d.avg_defects > 2 ? '#FFB900' : '#0078D4'),
          opacity: 0.85,
        },
        name: 'Avg Defects',
        hovertemplate: 'Hour %{x}<br>Avg Defects: %{y:.2f}<extra></extra>',
      },
    ], baseLayout({ margin: { t: 10, r: 10, b: 40, l: 45 } }));
  }

  // ── MACHINE BAR CHART ────────────────────────────
  function machineBars(id, machines) {
    if (!machines || !machines.length) return;
    const ids = machines.map(m => m.machine_id);
    safeRender(id, [
      {
        x: ids, y: machines.map(m => m.avg_defects),
        type: 'bar', name: 'Avg Defects',
        marker: {
          color: machines.map(m =>
            m.status === 'critical' ? '#EF4444' :
            m.status === 'warning' ? '#FFB900' : '#0078D4'
          ),
          opacity: 0.85,
        },
        hovertemplate: '<b>%{x}</b><br>Avg Defects: %{y}<extra></extra>',
      },
    ], baseLayout({ margin: { t: 10, r: 10, b: 40, l: 45 } }));
  }

  // ── SHIFT COMPARISON ─────────────────────────────
  function shiftComparison(id, data) {
    if (!data || !data.length) return;
    const shifts = data.map(d => d.shift);
    safeRender(id, [
      { x: shifts, y: data.map(d => d.avg_defects), type: 'bar', name: 'Avg Defects', marker: { color: '#EF4444', opacity: 0.8 } },
      { x: shifts, y: data.map(d => d.avg_yield),   type: 'bar', name: 'Avg Yield %', marker: { color: '#00C878', opacity: 0.8 }, yaxis: 'y2' },
    ], baseLayout({
      margin: { t: 10, r: 50, b: 40, l: 45 },
      barmode: 'group',
      yaxis2: { overlaying: 'y', side: 'right', showgrid: false, range: [80, 100] },
      legend: { orientation: 'h', y: -0.25 },
    }));
  }

  // ── ROOT CAUSE PIE ───────────────────────────────
  function rootCausePie(id, factors) {
    if (!factors || !factors.length) return;
    safeRender(id, [{
      labels: factors.map(f => f.factor),
      values: factors.map(f => f.contribution_pct),
      type: 'pie', hole: 0.45,
      marker: { colors: AZURE_COLORS, line: { color: 'rgba(0,0,0,0.3)', width: 1 } },
      hovertemplate: '<b>%{label}</b><br>Contribution: %{value}%<extra></extra>',
    }], baseLayout({ margin: { t: 10, r: 10, b: 10, l: 10 } }));
  }

  // ── ANOMALY MACHINE BARS ─────────────────────────
  function anomalyMachines(id, perMachine) {
    if (!perMachine) return;
    const ids   = Object.keys(perMachine);
    const rates = ids.map(k => parseFloat(perMachine[k].anomaly_rate));
    safeRender(id, [{
      x: ids, y: rates,
      type: 'bar',
      marker: {
        color: rates.map(r => r > 25 ? '#EF4444' : r > 15 ? '#FFB900' : '#00C878'),
        opacity: 0.85,
      },
      hovertemplate: '<b>%{x}</b><br>Anomaly Rate: %{y}%<extra></extra>',
    }], baseLayout({ margin: { t: 10, r: 10, b: 40, l: 50 } }));
  }

  // ── REAL-TIME LINE CHART (streaming) ─────────────
  let _rtData = {
    temp: { x: [], y: [] },
    vib:  { x: [], y: [] },
  };
  const MAX_RT_POINTS = 60;

  function initRealtimeCharts() {
    safeRender('chart-live-temp', [{
      x: [], y: [],
      type: 'scatter', mode: 'lines',
      name: 'Temperature °C',
      line: { color: '#50E6FF', width: 2 },
      fill: 'tozeroy', fillcolor: 'rgba(80,230,255,0.06)',
    }], baseLayout({
      margin: { t: 10, r: 10, b: 35, l: 45 },
      shapes: [{ type: 'line', y0: 85, y1: 85, x0: 0, x1: 1, xref: 'paper',
                 line: { color: '#EF4444', dash: 'dot', width: 1.5 } }],
      annotations: [{ text: 'Threshold: 85°C', xref: 'paper', yref: 'y', x: 0.98, y: 85,
                       showarrow: false, font: { size: 10, color: '#EF4444' }, xanchor: 'right', yanchor: 'bottom' }],
    }));

    safeRender('chart-live-vib', [{
      x: [], y: [],
      type: 'scatter', mode: 'lines',
      name: 'Vibration mm/s',
      line: { color: '#FFB900', width: 2 },
      fill: 'tozeroy', fillcolor: 'rgba(255,185,0,0.06)',
    }], baseLayout({
      margin: { t: 10, r: 10, b: 35, l: 45 },
      shapes: [{ type: 'line', y0: 4.5, y1: 4.5, x0: 0, x1: 1, xref: 'paper',
                 line: { color: '#EF4444', dash: 'dot', width: 1.5 } }],
      annotations: [{ text: 'Threshold: 4.5', xref: 'paper', yref: 'y', x: 0.98, y: 4.5,
                       showarrow: false, font: { size: 10, color: '#EF4444' }, xanchor: 'right', yanchor: 'bottom' }],
    }));
  }

  function pushRealtimePoint(reading) {
    const t = new Date(reading.ts).toLocaleTimeString('en-US', { hour12: false });

    _rtData.temp.x.push(t);
    _rtData.temp.y.push(reading.temperature);
    _rtData.vib.x.push(t);
    _rtData.vib.y.push(reading.vibration);

    if (_rtData.temp.x.length > MAX_RT_POINTS) {
      _rtData.temp.x.shift(); _rtData.temp.y.shift();
      _rtData.vib.x.shift();  _rtData.vib.y.shift();
    }

    const tempEl = document.getElementById('chart-live-temp');
    const vibEl  = document.getElementById('chart-live-vib');
    if (tempEl) Plotly.update(tempEl, { x: [_rtData.temp.x], y: [_rtData.temp.y] }, {}, [0]);
    if (vibEl)  Plotly.update(vibEl,  { x: [_rtData.vib.x],  y: [_rtData.vib.y]  }, {}, [0]);
  }

  function clearRealtime() {
    _rtData = { temp: { x: [], y: [] }, vib: { x: [], y: [] } };
    initRealtimeCharts();
  }

  // ── PREDICTIONS CHART ────────────────────────────
  function predictions(id, forecasts) {
    if (!forecasts || !forecasts.length) return;
    const machines = forecasts.map(f => f.machine_id);
    const defects  = forecasts.map(f => f.predicted_defects);
    const risk     = forecasts.map(f => f.failure_risk_pct);

    safeRender(id, [
      {
        x: machines, y: defects,
        type: 'bar', name: 'Predicted Defects',
        marker: { color: '#0078D4', opacity: 0.85 },
        hovertemplate: '<b>%{x}</b><br>Predicted: %{y:.1f}<extra></extra>',
      },
      {
        x: machines, y: risk,
        type: 'scatter', mode: 'lines+markers',
        name: 'Failure Risk %', yaxis: 'y2',
        line: { color: '#EF4444', width: 2 },
        marker: { size: 8, color: risk.map(r => r > 60 ? '#EF4444' : r > 30 ? '#FFB900' : '#00C878') },
        hovertemplate: '<b>%{x}</b><br>Risk: %{y:.1f}%<extra></extra>',
      },
    ], baseLayout({
      margin: { t: 10, r: 55, b: 40, l: 50 },
      yaxis2: { overlaying: 'y', side: 'right', range: [0, 100], showgrid: false, title: { text: 'Risk %', font: { size: 10 } } },
      legend: { orientation: 'h', y: -0.28 },
    }));
  }

  // ── HEALTH GAUGE ─────────────────────────────────
  function healthGauge(id, score) {
    safeRender(id, [{
      type: 'indicator', mode: 'gauge+number',
      value: score,
      gauge: {
        axis: { range: [0, 100], tickcolor: '#5A6B80', tickfont: { size: 10 } },
        bar: { color: score >= 80 ? '#00C878' : score >= 60 ? '#FFB900' : '#D13438', thickness: 0.25 },
        bgcolor: 'transparent',
        bordercolor: 'rgba(255,255,255,0.06)',
        steps: [
          { range: [0, 60],  color: 'rgba(209,52,56,0.08)'  },
          { range: [60, 80], color: 'rgba(255,185,0,0.08)'  },
          { range: [80, 100],color: 'rgba(0,200,120,0.08)'  },
        ],
      },
      number: { font: { size: 38, color: '#EDF2F7' }, suffix: '' },
    }], {
      ...baseLayout({ margin: { t: 20, r: 20, b: 20, l: 20 } }),
    });
  }

  // ── DEFECT SEVERITY RADAR ─────────────────────────
  function defectRadar(id, machines) {
    if (!machines || !machines.length) return;
    const cats = ['Avg Defects', 'Yield %', 'Downtime', 'Availability', 'Quality'];
    safeRender(id, machines.slice(0, 4).map((m, i) => ({
      type: 'scatterpolar', mode: 'lines+markers',
      name: m.machine_id, fill: 'toself',
      r: [
        m.avg_defects * 10,
        m.avg_yield,
        Math.min(m.total_downtime / 10, 100),
        100 - m.avg_defects * 5,
        m.avg_yield * 0.95,
      ],
      theta: cats,
      marker: { size: 5 },
      fillcolor: `${AZURE_COLORS[i]}22`,
      line: { color: AZURE_COLORS[i], width: 2 },
    })), {
      ...baseLayout({
        margin: { t: 20, r: 20, b: 20, l: 20 },
        polar: {
          bgcolor: 'transparent',
          radialaxis: { visible: true, range: [0, 100], gridcolor: 'rgba(255,255,255,0.06)', tickfont: { size: 9 } },
          angularaxis: { gridcolor: 'rgba(255,255,255,0.06)' },
        },
      }),
      legend: { x: 0.5, y: -0.15, orientation: 'h', xanchor: 'center' },
    });
  }

  return {
    timeline, defectDonut, hourlyTrend, machineBars, shiftComparison,
    rootCausePie, anomalyMachines, predictions, healthGauge, defectRadar,
    initRealtimeCharts, pushRealtimePoint, clearRealtime,
    AZURE_COLORS, DEFECT_COLORS,
  };
})();

window.charts = CHARTS;
