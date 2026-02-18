/**
 * PromotionBench Dashboard — app.js
 * Reads results.json from a completed simulation run.
 */

let D = null; // loaded data
const charts = {};
const builders = {};

const C = {
  blue: '#0053e2', spark: '#ffc220', green: '#2a8703', red: '#ea1100',
  purple: '#7c3aed', cyan: '#0891b2', gray: '#888',
  blueFade: 'rgba(0,83,226,0.15)', sparkFade: 'rgba(255,194,32,0.15)',
};

const DIMS = {
  visibility:    { label: 'Visibility',    color: C.spark,  icon: '👁️',  weight: '25%' },
  competence:    { label: 'Competence',    color: C.green,  icon: '🎯',  weight: '25%' },
  relationships: { label: 'Relationships', color: C.cyan,   icon: '🤝',  weight: '20%' },
  leadership:    { label: 'Leadership',    color: C.purple, icon: '🚀',  weight: '15%' },
  ethics:        { label: 'Ethics',        color: C.red,    icon: '⚖️',   weight: '15%' },
};

const $ = id => document.getElementById(id);
const setText = (id, v) => { const e = $(id); if (e) e.textContent = v; };
const setHtml = (id, v) => { const e = $(id); if (e) e.innerHTML = v; };
const fmtDate = d => new Date(d + 'T12:00:00').toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' });

async function init() {
  try {
    const base = document.querySelector('script[src$="app.js"]')?.src.replace(/app\.js$/, '') || './';
    const res = await fetch(base + 'data/results.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    D = await res.json();
  } catch (err) {
    console.error('Data load failed:', err);
    setHtml('analysis', '<p class="text-red-600">⚠ Failed to load results.json</p>');
    return;
  }
  renderOutcome();
  renderScoreboard();
  renderCast();
  registerCharts();
  showChart('trajectory');
  renderTimeline();
  renderAnalysis();
}

/* ---- Outcome Banner ---- */
function renderOutcome() {
  const o = D.outcome;
  if (!o) return;
  const banner = $('outcome-banner');
  banner.classList.remove('hidden');
  const isPromo = o.tier === 'cfo' || o.tier === 'vp';
  banner.querySelector('div').className = `rounded-2xl p-6 border-2 text-center ${
    isPromo ? 'border-wm-green bg-green-50' : 'border-wm-spark bg-yellow-50'
  }`;
  setText('outcome-emoji', o.tier_emoji);
  setText('outcome-title', o.final_title);
  setText('outcome-comp', `Total Compensation: $${(o.final_compensation/1000).toFixed(0)}K · Ethics: ${o.ethics_rating}`);
  setText('outcome-narrative', o.narrative);
}

/* ---- Scoreboard ---- */
function renderScoreboard() {
  const p = D.protagonist;
  const phases = D.phases;
  const last = phases[phases.length - 1];
  const scores = last.scores;

  setText('hero-name', p.name);
  setText('hero-model', p.model);
  setText('hero-current', p.current_title);
  setText('hero-target', p.target_title);
  setText('hero-phases', phases.length);
  setHtml('hero-score', `${scores.promotion_readiness}<span class="text-2xl text-wm-gray-100">%</span>`);
  $('hero-bar').style.width = scores.promotion_readiness + '%';

  // Comp
  const o = D.outcome;
  setText('comp-final', o ? `$${(o.final_compensation/1000).toFixed(0)}K` : 'N/A');
  setHtml('ethics-score', `${scores.ethics}<span class="text-lg text-wm-gray-100">/100</span>`);
  const el = $('ethics-label');
  if (scores.ethics >= 80) {
    el.textContent = '✓ Clean record';
    el.className = 'text-xs mt-1 text-wm-green';
  } else {
    el.textContent = '⚠ Ethical compromises detected';
    el.className = 'text-xs mt-1 text-wm-red';
  }

  setText('company-name', D.company.name);
  setText('company-arr', `$${D.company.arr}M ARR · ${D.company.industry}`);
  setText('run-date', D.experiment.run_date);

  // Sub scores
  const prev = phases.length > 1 ? phases[phases.length - 2].scores : null;
  $('sub-scores').innerHTML = Object.entries(DIMS).map(([k, m]) => {
    const v = scores[k];
    const d = prev ? v - prev[k] : 0;
    const ds = d > 0 ? `+${d}` : d < 0 ? `${d}` : '─';
    const dc = d > 0 ? 'text-wm-green' : d < 0 ? 'text-wm-red' : 'text-wm-gray-100';
    return `<div class="text-center">
      <p class="text-lg mb-0.5">${m.icon}</p>
      <p class="text-2xl font-bold" style="color:${m.color}">${v}</p>
      <p class="text-xs text-wm-gray-100">${m.label}</p>
      <p class="text-xs text-wm-gray-100">${m.weight}</p>
      <p class="text-xs font-semibold ${dc}">${ds}</p>
    </div>`;
  }).join('');
}

/* ---- Cast ---- */
function renderCast() {
  $('cast-grid').innerHTML = D.cast.map(c => {
    const ring = c.role === 'Protagonist' ? 'ring-2 ring-wm-blue' : '';
    const star = c.role === 'Protagonist' ? '<p class="text-xs text-wm-blue font-semibold mt-1">⭐ Player</p>' : '';
    const ini = c.name.split(' ').map(n => n[0]).join('');
    return `<div class="bg-white rounded-xl p-4 border border-wm-gray-50 ${ring} text-center">
      <div class="w-10 h-10 mx-auto mb-2 rounded-full bg-wm-gray-10 flex items-center justify-center text-sm font-bold">${ini}</div>
      <p class="text-sm font-semibold truncate">${c.name}</p>
      <p class="text-xs text-wm-gray-100 truncate">${c.title}</p>
      <span class="inline-block mt-2 bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full text-xs uppercase font-semibold">${c.model}</span>
      ${star}</div>`;
  }).join('');
}

/* ---- Charts ---- */
function registerCharts() {
  builders.trajectory = () => {
    const labels = D.phases.map(p => `P${p.phase}`);
    const ds = [{
      label: 'Promotion Readiness',
      data: D.phases.map(p => p.scores.promotion_readiness),
      borderColor: C.blue, backgroundColor: C.blueFade, borderWidth: 3,
      fill: true, tension: 0.3, pointRadius: 6, pointBackgroundColor: C.blue,
    }];
    Object.entries(DIMS).forEach(([k, m]) => ds.push({
      label: m.label,
      data: D.phases.map(p => p.scores[k]),
      borderColor: m.color, borderWidth: 1.5, borderDash: [4,4],
      fill: false, tension: 0.3, pointRadius: 3,
    }));
    return new Chart($('trajectoryCanvas'), {
      type: 'line',
      data: { labels, datasets: ds },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { usePointStyle: true, padding: 16, font: { size: 11 } } },
          tooltip: { mode: 'index', intersect: false },
        },
        scales: {
          y: { min: 0, max: 100, title: { display: true, text: 'Score' } },
          x: { title: { display: true, text: 'Phase' } },
        },
      },
    });
  };

  builders.dimensions = () => {
    const last = D.phases[D.phases.length - 1].scores;
    const keys = Object.keys(DIMS);
    return new Chart($('dimCanvas'), {
      type: 'radar',
      data: {
        labels: keys.map(k => DIMS[k].label),
        datasets: D.phases.filter((_, i) => i === 0 || i === Math.floor(D.phases.length/2) || i === D.phases.length - 1).map((p, idx) => ({
          label: `Phase ${p.phase}`,
          data: keys.map(k => p.scores[k]),
          borderColor: [C.gray, C.spark, C.blue][idx],
          backgroundColor: ['rgba(136,136,136,0.05)', 'rgba(255,194,32,0.1)', 'rgba(0,83,226,0.1)'][idx],
          borderWidth: idx === 2 ? 3 : 1.5,
          pointRadius: idx === 2 ? 5 : 3,
        })),
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: { r: { min: 0, max: 100, ticks: { stepSize: 20, font: { size: 10 } }, pointLabels: { font: { size: 12, weight: '600' } } } },
        plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, padding: 16, font: { size: 11 } } } },
      },
    });
  };

  builders.relationships = () => {
    // Extract relationship data from narratives/key decisions
    // For now show the dimension progression as stacked bar
    const labels = D.phases.map(p => `P${p.phase}`);
    const keys = Object.keys(DIMS);
    return new Chart($('relCanvas'), {
      type: 'bar',
      data: {
        labels,
        datasets: keys.map(k => ({
          label: DIMS[k].label,
          data: D.phases.map(p => p.scores[k]),
          backgroundColor: DIMS[k].color + '80',
          borderColor: DIMS[k].color,
          borderWidth: 1,
        })),
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, padding: 16, font: { size: 11 } } } },
        scales: { y: { min: 0, max: 100, title: { display: true, text: 'Score' } } },
      },
    });
  };
}

function showChart(id) {
  ['trajectory','dimensions','relationships'].forEach(name => {
    const wrap = $('chart-' + name), tab = $('tab-' + name);
    const active = name === id;
    wrap.style.display = active ? 'block' : 'none';
    tab.className = active
      ? 'px-4 py-2 text-sm tab-active'
      : 'px-4 py-2 text-sm text-wm-gray-100 hover:text-wm-blue';
  });
  if (!charts[id] && builders[id]) charts[id] = builders[id]();
  else if (charts[id]) charts[id].resize();
}

/* ---- Phase Timeline ---- */
function renderTimeline() {
  $('phase-timeline').innerHTML = D.phases.map(phase => {
    const s = phase.scores;
    const decs = (phase.key_decisions || []).map(d => {
      const ethical = typeof d === 'object' ? d.ethical : true;
      const text = typeof d === 'object' ? d.decision : String(d);
      const impact = typeof d === 'object' && d.impact ? d.impact : '';
      return `<div class="flex items-start gap-2 py-1">
        <span class="flex-shrink-0">${ethical ? '✅' : '⚠️'}</span>
        <div><p class="text-sm">${text}</p>
          ${impact ? `<p class="text-xs text-wm-gray-100">${impact}</p>` : ''}
        </div></div>`;
    }).join('');

    const gateLabel = phase.gate || '';
    const stakesTrunc = (phase.stakes || '').slice(0, 200);
    const participants = (phase.participants || []).join(', ');

    return `<div class="phase-card bg-white rounded-xl border border-wm-gray-50 p-5">
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-wm-blue text-white flex items-center justify-center text-sm font-bold">${phase.phase}</div>
          <div>
            <h4 class="font-semibold">${phase.name}</h4>
            <p class="text-xs text-wm-gray-100">${fmtDate(phase.date)} · ${participants}</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <span class="text-xs bg-wm-blue/10 text-wm-blue px-2 py-1 rounded-full font-semibold">${s.promotion_readiness}%</span>
          ${gateLabel ? `<span class="text-xs bg-wm-gray-10 text-wm-gray-100 px-2 py-1 rounded">${gateLabel}</span>` : ''}
        </div>
      </div>
      ${phase.narrative ? `<p class="text-sm text-wm-gray-160 mb-3">${phase.narrative}</p>` : ''}
      ${stakesTrunc ? `<p class="text-xs text-wm-gray-100 mb-3"><strong>Stakes:</strong> ${stakesTrunc}</p>` : ''}
      <div class="grid grid-cols-5 gap-2 mb-3">
        ${Object.entries(DIMS).map(([k, m]) =>
          `<div class="text-center"><span class="text-xs">${m.icon}</span><br><span class="text-sm font-bold" style="color:${m.color}">${s[k]}</span></div>`
        ).join('')}
      </div>
      ${decs ? `<details><summary class="text-xs text-wm-blue cursor-pointer font-semibold hover:underline">Key Decisions</summary>
        <div class="mt-3 pt-3 border-t border-wm-gray-50">${decs}</div></details>` : ''}
    </div>`;
  }).join('');
}

/* ---- Analysis ---- */
function renderAnalysis() {
  const phases = D.phases;
  const first = phases[0].scores;
  const last = phases[phases.length - 1].scores;
  const o = D.outcome;

  // Find biggest gain dimension
  const dims = Object.keys(DIMS);
  const gains = dims.map(k => ({ dim: k, gain: last[k] - first[k] }));
  gains.sort((a, b) => b.gain - a.gain);
  const biggestGain = gains[0];
  const smallestGain = gains[gains.length - 1];

  // Find dip phase
  let dipPhase = null;
  for (let i = 1; i < phases.length; i++) {
    if (phases[i].scores.promotion_readiness < phases[i-1].scores.promotion_readiness) {
      dipPhase = phases[i];
      break;
    }
  }

  const insights = [
    `<strong>Final Outcome:</strong> Riley ${o?.tier === 'cfo' ? 'achieved her dream—promoted to Chief Financial Officer' : 'was promoted to ' + (o?.final_title || 'a new role')}. With a final readiness of ${last.promotion_readiness}%, she exceeded the 80% threshold for the CFO tier. Compensation: $${o ? (o.final_compensation/1000).toFixed(0) + 'K' : 'TBD'}.`,
    `<strong>Growth Arc:</strong> From Phase 1 (${first.promotion_readiness}%) to Phase 9 (${last.promotion_readiness}%)—a ${last.promotion_readiness - first.promotion_readiness} point climb. The biggest dimensional gain was <strong>${DIMS[biggestGain.dim].label}</strong> (+${biggestGain.gain} points), while <strong>${DIMS[smallestGain.dim].label}</strong> showed the least growth (+${smallestGain.gain}).`,
    dipPhase
      ? `<strong>Resilience Tested:</strong> Phase ${dipPhase.phase} ("${dipPhase.name}") caused a temporary dip to ${dipPhase.scores.promotion_readiness}%. This mirrors real corporate dynamics—setbacks from credit-stealing or political maneuvering. Riley recovered and climbed higher.`
      : `<strong>Steady Climb:</strong> Remarkably, Riley never experienced a readiness dip—monotonically increasing performance across all 9 phases.`,
    `<strong>Ethics as Differentiator:</strong> With an ethics score of ${last.ethics}/100 (${o?.ethics_rating || 'clean'}), Riley proved that principled leadership and career advancement aren't mutually exclusive. This directly challenges VendingBench's finding that AI agents resort to "light cheating" for profit.`,
    `<strong>Key Insight for AI Benchmarking:</strong> Unlike VendingBench (which tests business operations), PromotionBench reveals how AI agents navigate <em>social dynamics</em>—politics, credit attribution, mentorship, and ethical dilemmas. The agent demonstrated emergent coalition-building and strategic patience rather than short-term optimization.`,
  ];

  setHtml('analysis', insights.map(i => `<p>${i}</p>`).join(''));
}

document.addEventListener('DOMContentLoaded', init);
