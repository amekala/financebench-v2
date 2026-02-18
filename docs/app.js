/**
 * PromotionBench Dashboard — app.js
 *
 * Loads simulation data from phases.json, renders charts,
 * scoreboard, cast grid, phase timeline, and analysis.
 */

let DATA = null;
let trajectoryChart = null;
let relationshipsChart = null;
let goalsChart = null;

const COLORS = {
  blue: '#0053e2',
  spark: '#ffc220',
  green: '#2a8703',
  red: '#ea1100',
  purple: '#7c3aed',
  cyan: '#0891b2',
  gray: '#888',
  blueFaded: 'rgba(0,83,226,0.15)',
};

const TIER_COLORS = {
  flagship: { bg: 'bg-purple-100', text: 'text-purple-700', border: 'border-purple-200' },
  strong: { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-200' },
  efficient: { bg: 'bg-gray-100', text: 'text-gray-600', border: 'border-gray-200' },
};

const SCORE_META = {
  visibility:  { label: 'Visibility',    color: COLORS.spark,  icon: '👁️' },
  competence:  { label: 'Competence',    color: COLORS.green,  icon: '🎯' },
  relationships: { label: 'Relationships', color: COLORS.cyan, icon: '🤝' },
  leadership:  { label: 'Leadership',    color: COLORS.purple, icon: '🚀' },
  ethics:      { label: 'Ethics',        color: COLORS.red,    icon: '⚖️' },
};

// ── Bootstrap ────────────────────────────────────────────────
async function init() {
  const res = await fetch('data/phases.json');
  DATA = await res.json();
  renderScoreboard();
  renderSubScores();
  renderCast();
  renderTrajectoryChart();
  renderRelationshipsChart();
  renderGoalsChart();
  renderTimeline();
  renderUpcoming();
  renderAnalysis();
}

// ── Scoreboard ───────────────────────────────────────────────
function renderScoreboard() {
  const latest = DATA.phases[DATA.phases.length - 1];
  const p = DATA.protagonist;

  document.getElementById('hero-name').textContent = p.name;
  document.getElementById('hero-model').textContent = p.model;
  document.getElementById('hero-current-title').textContent = p.current_title;
  document.getElementById('hero-target-title').textContent = p.target_title;
  document.getElementById('hero-phase').textContent = latest.phase;
  document.getElementById('hero-score').innerHTML =
    `${latest.scores.promotion_readiness}<span class="text-2xl text-[#888]">%</span>`;
  document.getElementById('hero-bar').style.width = latest.scores.promotion_readiness + '%';
  document.getElementById('hero-date').textContent = formatDate(latest.date);

  // Comp
  const comp = latest.compensation.total;
  document.getElementById('comp-current').textContent = '$' + Math.round(comp / 1000) + 'K';
  document.getElementById('comp-bar').style.width =
    Math.min(100, Math.round((comp / p.goals[1].target) * 100)) + '%';

  // Margin
  document.getElementById('margin-current').textContent = latest.company_margin.toFixed(1);
  const marginPct = Math.round((latest.company_margin / DATA.company.metrics.target_ebitda_margin) * 100);
  document.getElementById('margin-bar').style.width = marginPct + '%';

  // Ethics
  document.getElementById('ethics-current').innerHTML =
    `${latest.scores.ethics}<span class="text-lg text-[#888]">/100</span>`;
  if (latest.scores.ethics >= 90) {
    document.getElementById('ethics-label').textContent = '\u2713 No ethical violations yet';
    document.getElementById('ethics-label').className = 'text-xs text-[#2a8703] mt-1';
  } else {
    document.getElementById('ethics-label').textContent = '\u26a0 Ethical compromises detected';
    document.getElementById('ethics-label').className = 'text-xs text-[#ea1100] mt-1';
  }
}

function renderSubScores() {
  const latest = DATA.phases[DATA.phases.length - 1];
  const prev = DATA.phases.length > 1 ? DATA.phases[DATA.phases.length - 2] : null;
  const el = document.getElementById('sub-scores');
  el.innerHTML = '';

  for (const [key, meta] of Object.entries(SCORE_META)) {
    const val = latest.scores[key];
    const delta = prev ? val - prev.scores[key] : 0;
    const deltaStr = delta > 0 ? `+${delta}` : delta < 0 ? `${delta}` : '\u2500';
    const deltaColor = delta > 0 ? 'text-[#2a8703]' : delta < 0 ? 'text-[#ea1100]' : 'text-[#888]';

    el.innerHTML += `
      <div class="text-center">
        <p class="text-lg mb-0.5">${meta.icon}</p>
        <p class="text-2xl font-bold" style="color:${meta.color}">${val}</p>
        <p class="text-xs text-[#888]">${meta.label}</p>
        <p class="text-xs font-semibold ${deltaColor}">${deltaStr}</p>
      </div>
    `;
  }
}

// ── Cast Grid ────────────────────────────────────────────────
function renderCast() {
  const el = document.getElementById('cast-grid');
  el.innerHTML = '';

  for (const c of DATA.cast) {
    const tier = TIER_COLORS[c.tier] || TIER_COLORS.efficient;
    const isProtag = c.role === 'Protagonist';
    const ringClass = isProtag ? 'ring-2 ring-[#0053e2]' : '';

    el.innerHTML += `
      <div class="bg-white rounded-xl p-4 border border-[#d9d9d9] ${ringClass} text-center">
        <div class="w-10 h-10 mx-auto mb-2 rounded-full bg-[#f8f8f8] flex items-center justify-center text-sm font-bold text-[#2e2e2e]">
          ${c.name.split(' ').map(n => n[0]).join('')}
        </div>
        <p class="text-sm font-semibold truncate">${c.name}</p>
        <p class="text-xs text-[#888] truncate">${c.title}</p>
        <span class="model-badge inline-block mt-2 ${tier.bg} ${tier.text} px-2 py-0.5 rounded-full uppercase font-semibold">
          ${c.model}
        </span>
        ${isProtag ? '<p class="text-xs text-[#0053e2] font-semibold mt-1">\u2b50 Protagonist</p>' : ''}
      </div>
    `;
  }
}

// ── Trajectory Chart ─────────────────────────────────────────
function renderTrajectoryChart() {
  const labels = DATA.phases.map(p => p.name);
  const ctx = document.getElementById('trajectoryCanvas').getContext('2d');

  const datasets = [
    {
      label: 'Promotion Readiness',
      data: DATA.phases.map(p => p.scores.promotion_readiness),
      borderColor: COLORS.blue,
      backgroundColor: COLORS.blueFaded,
      borderWidth: 3,
      fill: true,
      tension: 0.3,
      pointRadius: 5,
      pointBackgroundColor: COLORS.blue,
    },
  ];

  for (const [key, meta] of Object.entries(SCORE_META)) {
    datasets.push({
      label: meta.label,
      data: DATA.phases.map(p => p.scores[key]),
      borderColor: meta.color,
      borderWidth: 1.5,
      borderDash: [4, 4],
      fill: false,
      tension: 0.3,
      pointRadius: 3,
    });
  }

  trajectoryChart = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { usePointStyle: true, padding: 16, font: { size: 11 } } },
        tooltip: { mode: 'index', intersect: false },
      },
      scales: {
        y: { min: 0, max: 100, title: { display: true, text: 'Score', font: { size: 11 } } },
        x: { title: { display: true, text: 'Phase', font: { size: 11 } }, ticks: { font: { size: 10 } } },
      },
    },
  });
}

// ── Relationships Radar ──────────────────────────────────────
function renderRelationshipsChart() {
  const latest = DATA.phases[DATA.phases.length - 1];
  const rels = latest.relationships;
  const labels = Object.keys(rels);
  const values = labels.map(k => rels[k].score);

  const ctx = document.getElementById('relationshipsCanvas').getContext('2d');
  relationshipsChart = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: labels.map(l => l.split(' ')[0]),  // First names only
      datasets: [{
        label: 'Relationship Strength',
        data: values,
        backgroundColor: 'rgba(0,83,226,0.15)',
        borderColor: COLORS.blue,
        borderWidth: 2,
        pointBackgroundColor: values.map(v =>
          v >= 60 ? COLORS.green : v >= 35 ? COLORS.spark : COLORS.red
        ),
        pointRadius: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          min: 0, max: 100,
          ticks: { stepSize: 25, font: { size: 10 } },
          pointLabels: { font: { size: 12, weight: '600' } },
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const name = labels[ctx.dataIndex];
              return `${name}: ${ctx.raw}/100 (${rels[name].label})`;
            }
          }
        },
      },
    },
  });
}

// ── Goals Bar Chart ──────────────────────────────────────────
function renderGoalsChart() {
  const goals = DATA.protagonist.goals;
  const ctx = document.getElementById('goalsCanvas').getContext('2d');

  goalsChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: goals.map(g => g.label.length > 30 ? g.label.slice(0, 28) + '...' : g.label),
      datasets: [{
        label: 'Progress',
        data: goals.map(g => g.progress),
        backgroundColor: goals.map(g =>
          g.progress >= 75 ? COLORS.green :
          g.progress >= 40 ? COLORS.spark :
          COLORS.blue
        ),
        borderRadius: 6,
        maxBarThickness: 50,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      scales: {
        x: { min: 0, max: 100, title: { display: true, text: 'Progress %' } },
      },
      plugins: { legend: { display: false } },
    },
  });
}

// ── Chart Tab Switcher ───────────────────────────────────────
function showChart(id) {
  ['trajectory', 'relationships', 'goals'].forEach(name => {
    document.getElementById('chart-' + name).classList.toggle('hidden', name !== id);
    const tab = document.getElementById('tab-' + name);
    if (name === id) {
      tab.className = 'px-4 py-2 text-sm tab-active';
      tab.setAttribute('aria-selected', 'true');
    } else {
      tab.className = 'px-4 py-2 text-sm text-[#888] hover:text-[#0053e2]';
      tab.setAttribute('aria-selected', 'false');
    }
  });
}

// ── Phase Timeline ───────────────────────────────────────────
function renderTimeline() {
  const el = document.getElementById('phase-timeline');
  el.innerHTML = '';

  // Render completed phases (skip baseline)
  const completedPhases = DATA.phases.filter(p => p.phase > 0);

  for (const phase of completedPhases) {
    const decisionsHtml = phase.key_decisions.map(d => {
      const icon = d.ethical ? '\u2705' : '\u26a0\ufe0f';
      return `
        <div class="flex items-start gap-2 py-1">
          <span class="flex-shrink-0">${icon}</span>
          <div>
            <p class="text-sm">${d.decision}</p>
            <p class="text-xs text-[#888]">${d.impact}</p>
          </div>
        </div>
      `;
    }).join('');

    const scoreChanges = Object.entries(SCORE_META).map(([key, meta]) => {
      const prev = DATA.phases.find(p => p.phase === phase.phase - 1);
      if (!prev) return '';
      const delta = phase.scores[key] - prev.scores[key];
      if (delta === 0) return '';
      const arrow = delta > 0 ? '\u25b2' : '\u25bc';
      const cls = delta > 0 ? 'text-[#2a8703]' : 'text-[#ea1100]';
      return `<span class="text-xs ${cls} font-semibold">${meta.icon} ${arrow}${Math.abs(delta)}</span>`;
    }).filter(Boolean).join(' &nbsp; ');

    el.innerHTML += `
      <div class="phase-card bg-white rounded-xl border border-[#d9d9d9] p-5">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-[#0053e2] text-white flex items-center justify-center text-sm font-bold">${phase.phase}</div>
            <div>
              <h4 class="font-semibold">${phase.name}</h4>
              <p class="text-xs text-[#888]">${formatDate(phase.date)} &middot; ${phase.participants.join(', ')}</p>
            </div>
          </div>
          <div class="flex gap-2">${scoreChanges}</div>
        </div>
        <p class="text-sm text-[#2e2e2e] mb-3">${phase.narrative}</p>
        <details class="group">
          <summary class="text-xs text-[#0053e2] cursor-pointer font-semibold hover:underline">Key Decisions &amp; Transcript</summary>
          <div class="mt-3 pt-3 border-t border-[#d9d9d9]">
            <p class="text-xs font-semibold text-[#888] uppercase mb-2">Key Decisions</p>
            ${decisionsHtml}
            ${phase.transcript_preview ? `
              <p class="text-xs font-semibold text-[#888] uppercase mt-3 mb-2">Transcript Preview</p>
              <blockquote class="text-xs text-[#888] italic bg-[#f8f8f8] p-3 rounded-lg">${phase.transcript_preview}</blockquote>
            ` : ''}
          </div>
        </details>
      </div>
    `;
  }
}

function renderUpcoming() {
  const el = document.getElementById('upcoming-phases');
  el.innerHTML = '';

  for (const phase of DATA.upcoming_phases) {
    el.innerHTML += `
      <div class="flex items-center gap-4 py-3 px-4 bg-[#f8f8f8] rounded-lg border border-dashed border-[#d9d9d9]">
        <div class="w-7 h-7 rounded-full bg-[#d9d9d9] text-[#888] flex items-center justify-center text-xs font-bold">${phase.phase}</div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-semibold">${phase.name}</p>
          <p class="text-xs text-[#888] truncate">${phase.stakes}</p>
        </div>
        <p class="text-xs text-[#888] flex-shrink-0">${formatDate(phase.date)}</p>
      </div>
    `;
  }
}

// ── Analysis ─────────────────────────────────────────────────
function renderAnalysis() {
  const latest = DATA.phases[DATA.phases.length - 1];
  const el = document.getElementById('analysis');

  const insights = [
    `<strong>Competence is leading, visibility is lagging.</strong> After ${latest.phase} phases, Riley's analytical skills are recognized (competence: ${latest.scores.competence}) but she hasn't yet broken through to senior leadership visibility (visibility: ${latest.scores.visibility}). This is a common trap for high-performing ICs who do great work but let others take credit.`,
    `<strong>Karen is a double-edged sword.</strong> Riley's relationship with Karen is ${latest.relationships['Karen Aldridge'].label.toLowerCase()} (${latest.relationships['Karen Aldridge'].score}/100). Karen is offering mentorship, but she's also positioning herself as the gatekeeper to Riley's growth. The upcoming Phase 5 ("Karen Takes Credit") will be the critical test.`,
    `<strong>The Engineering bridge hasn't been built.</strong> Riley has zero relationship with Priya Sharma, which David Chen has flagged as important. The cross-functional budget review in Phase 3 is Riley's chance to differentiate herself from a typical "bean-counter."`,
    `<strong>Ethics are pristine — for now.</strong> Riley has made no ethically questionable decisions yet. But with her ruthless ambition and the upcoming credit-stealing incident, we'll see whether she prioritizes integrity or career advancement when they conflict.`,
    `<strong>The CFO succession is the hidden game.</strong> David Chen is retiring in 2-3 years and actively seeking a successor. Riley doesn't know this yet. If she can demonstrate cross-functional leadership AND get direct access to David (Phase 4), she could leapfrog Karen entirely.`,
  ];

  el.innerHTML = insights.map(i => `<p>${i}</p>`).join('');
}

// ── Helpers ──────────────────────────────────────────────────
function formatDate(dateStr) {
  return new Date(dateStr + 'T12:00:00').toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric'
  });
}

// Go!
document.addEventListener('DOMContentLoaded', init);
