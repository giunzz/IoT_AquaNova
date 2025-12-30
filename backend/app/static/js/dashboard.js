/* =====================================================
   CONSTANTS
===================================================== */
const SAFE_TEMP_MIN = 0;
const SAFE_TEMP_MAX = 1000;
const TURB_WARN = 200;

/* =====================================================
   DOM
===================================================== */
const lightToggle   = document.getElementById('lightToggle');
const lightStatus   = document.getElementById('lightStatus');

const modeButtons   = document.querySelectorAll('.seg-btn');
const colorDots     = document.querySelectorAll('.color-dot');
const colorPicker   = document.getElementById('customColor');

const feedBtn       = document.getElementById('feedNowBtn');
const feedMsg       = document.getElementById('feedNowMsg');

const warnTurb      = document.getElementById('warnTurb');
const warnTemp      = document.getElementById('warnTemp');

const menuBtn       = document.getElementById('menuBtn');
const sidebar       = document.querySelector('aside');

/* =====================================================
   STATE
===================================================== */
let lightOn = true;
let turbChart = null;

/* =====================================================
   LIGHT
===================================================== */
async function setLight(on, color = null) {
  const payload = { light: on ? 1 : 0 };
  if (on && color) payload.color = color;

  await fetch('/control/light', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
}

lightToggle?.addEventListener('click', async () => {
  lightOn = !lightToggle.classList.contains('on');
  lightToggle.classList.toggle('on', lightOn);

  lightStatus.textContent = lightOn ? '● ON' : '● OFF';
  lightStatus.className = `light-status ${lightOn ? 'on' : 'off'}`;

  await setLight(lightOn);
});

/* ================= MODE ================= */
async function setMode(mode) {
  await fetch('/control/mode', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode })
  });
}

modeButtons.forEach(btn => {
  btn.addEventListener('click', async () => {
    modeButtons.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    const mode = Number(btn.dataset.mode);
    await setMode(mode);
  });
});


/* =====================================================
   COLOR
===================================================== */
colorDots.forEach(dot => {
  dot.addEventListener('click', async () => {
    colorDots.forEach(d => d.classList.remove('active'));
    dot.classList.add('active');
    if (lightOn) await setLight(true, dot.dataset.color);
  });
});

colorPicker?.addEventListener('change', async e => {
  if (lightOn) await setLight(true, e.target.value.toUpperCase());
});

/* =====================================================
   FEED NOW
===================================================== */
feedBtn?.addEventListener('click', async () => {
  feedBtn.disabled = true;
  feedMsg.textContent = 'Feeding...';

  try {
    const r = await fetch('/control/feed-now', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount: 20 })
    });
    const j = await r.json();
    if (j.ok) {
      feedMsg.textContent = 'Feed command sent';
      feedMsg.style.color = '#16a34a';
    } else throw '';
  } catch {
    feedMsg.textContent = 'Feed error';
    feedMsg.style.color = '#dc2626';
  }

  setTimeout(() => feedMsg.textContent = '', 2000);
  feedBtn.disabled = false;
});

/* =====================================================
   CHART
===================================================== */
function ensureChart(ctx, labels, data) {
  if (turbChart) {
    turbChart.data.labels = labels;
    turbChart.data.datasets[0].data = data;
    turbChart.update();
    return;
  }

  turbChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Turbidity',
        data,
        borderWidth: 2,
        tension: 0.25,
        pointRadius: 2,
        fill: true
      }]
    },
    options: {
      responsive: true,
      interaction: { mode: 'index', intersect: false }
    }
  });
}

/* =====================================================
   LOAD DASHBOARD
===================================================== */
async function loadDashboard() {
  const latest = await (await fetch('/dashboard/latest?n=60')).json();
  const items = latest.items || [];

  if (!items.length) return;

  const arr = items.slice().reverse();

  const labels = arr.map(r => {
    const d = new Date(r.ts || '');
    return isNaN(d) ? '' : d.toLocaleTimeString('vi-VN', { hour12: false });
  });

  const turb = arr.map(r => Number(r.turbidity ?? NaN));
  ensureChart(document.getElementById('turbChart').getContext('2d'), labels, turb);

  const latestTurb = turb[turb.length - 1];
  warnTurb.className = latestTurb > TURB_WARN ? 'badge alert' : 'badge safe';
  warnTurb.textContent = `Turbidity: ${latestTurb}`;

  const tbody = document.getElementById('tempRows');
  tbody.innerHTML = '';

  items.slice(0, 10).forEach(r => {
    const t = Number(r.temperature ?? NaN);
    const ok = !isNaN(t) && t >= SAFE_TEMP_MIN && t <= SAFE_TEMP_MAX;

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${new Date(r.ts).toLocaleString()}</td>
      <td>${isNaN(t) ? '' : t.toFixed(2)}</td>
      <td>${SAFE_TEMP_MIN} – ${SAFE_TEMP_MAX}</td>
      <td>${r.deviceId ?? ''}</td>
      <td><span class="badge ${ok ? 'safe' : 'alert'}">${ok ? 'Safe' : 'Alert'}</span></td>
    `;
    tbody.appendChild(tr);

    warnTemp.className = ok ? 'badge safe' : 'badge alert';
    warnTemp.textContent = `Temperature: ${t}`;
  });
}
// ==============================
// FEED LEVEL (Dashboard)
// ONLY: /dashboard/latest?n=1
// ==============================
// ==============================
// FEED LEVEL (Dashboard)
// API: /dashboard/latest?n=1
// ==============================
const FEED_AMOUNT_API = '/dashboard/latest?n=1';

function setFeedBadge(level){
  const badge = document.getElementById('feedLevelBadge');
  if (!badge) return;

  badge.classList.remove('safe', 'alert');
  if (level >= 20) {
    badge.classList.add('safe');
    badge.textContent = 'OK';
  } else {
    badge.classList.add('alert');
    badge.textContent = 'LOW';
  }
}

// Lấy feed_level “bền” với nhiều format response
function extractFeedLevel(j){
  // case A: { items: [ {...} ] }
  if (j?.items && Array.isArray(j.items) && j.items[0]) {
    const x = j.items[0];
    return x.feed_level ?? x.feedLevel ?? x.feedLevelPct ?? null;
  }

  // case B: [ {...} ]
  if (Array.isArray(j) && j[0]) {
    const x = j[0];
    return x.feed_level ?? x.feedLevel ?? x.feedLevelPct ?? null;
  }

  // case C: { ok:true, data:{ items:[...] } } hoặc { data:{...} }
  if (j?.data) return extractFeedLevel(j.data);

  return null;
}

async function loadFeedLevelDashboard(){
  const valueEl = document.getElementById('feedLevelValue');
  const badgeEl = document.getElementById('feedLevelBadge');
  if (!valueEl || !badgeEl) return;

  try {
    const r = await fetch(FEED_AMOUNT_API, { cache: 'no-store' });
    if (!r.ok) return;

    const j = await r.json();

    // Debug 1 lần để bạn nhìn format thật
    console.log('[FEED API RESPONSE]', j);

    const levelRaw = extractFeedLevel(j);
    if (levelRaw == null) return;

    const level = Math.max(0, Math.min(100, Number(levelRaw)));
    valueEl.textContent = `${level}%`;
    setFeedBadge(level);

  } catch (e) {
    console.warn('[FEED LEVEL] load failed', e);
  }
}

// gọi luôn, không cần DOMContentLoaded
loadFeedLevelDashboard();
setInterval(loadFeedLevelDashboard, 10000);



/* =====================================================
   MOBILE MENU
===================================================== */
menuBtn?.addEventListener('click', () => {
  sidebar.classList.toggle('active');
});

/* =====================================================
   INIT
===================================================== */
loadDashboard();
setInterval(loadDashboard, 60000);
