/* ===============================
   API ENDPOINTS
================================ */
const FEED_NOW_API     = '/control/feed-now';
const SCHEDULE_API     = '/control/schedule';
const SCHEDULES_API    = '/control/schedules';
const FEED_LOGS_API    = '/control/feed-logs?limit=20';
const FEED_AMOUNT_API  = '/dashboard/last';

/* ===============================
   DOM
================================ */
const scRows         = document.getElementById('scRows');
const feedLogRows    = document.getElementById('feedLogRows');

const feedNowBtn     = document.getElementById('feedNowBtn');
const fnAmount       = document.getElementById('fnAmount');

const addScheduleBtn = document.getElementById('addScheduleBtn');
const scDate         = document.getElementById('scDate');
const scTime         = document.getElementById('scTime');
const scRepeat       = document.getElementById('scRepeat');
const scAmount       = document.getElementById('scAmount');

/* ===============================
   LOAD SCHEDULES
================================ */
async function loadSchedules(){
  scRows.innerHTML = '';

  try {
    const r = await fetch(SCHEDULES_API, { cache: 'no-store' });
    const j = await r.json();

    (j.items || []).forEach((s, i) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${i + 1}</td>
        <td>${s.date || ''}</td>
        <td>${s.time || ''}</td>
        <td>${s.repeat || ''}</td>
        <td>${s.amount ?? ''}</td>
        <td></td>
      `;
      scRows.appendChild(tr);
    });

  } catch (e) {
    console.error('[SCHEDULES] load failed', e);
  }
}

/* ===============================
   LOAD FEED LOGS
================================ */
async function loadFeedLogs(){
  feedLogRows.innerHTML = '';

  try {
    const r = await fetch(FEED_LOGS_API, { cache: 'no-store' });
    const j = await r.json();

    (j.items || []).forEach((log, i) => {
      const d = log.day ? new Date(log.day) : null;

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${i + 1}</td>
        <td>${d ? d.toLocaleString('vi-VN') : ''}</td>
      `;
      feedLogRows.appendChild(tr);
    });

  } catch (e) {
    console.error('[FEED LOGS] load failed', e);
  }
}

/* ===============================
   FEED NOW
================================ */
async function feedNow(){
  feedNowBtn.disabled = true;

  try {
    await fetch(FEED_NOW_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        amount: Number(fnAmount.value)
      })
    });
  } catch (e) {
    alert('Feed command failed');
  } finally {
    setTimeout(() => feedNowBtn.disabled = false, 800);
  }
}

/* ===============================
   ADD SCHEDULE
================================ */
async function addSchedule(){
  const body = {
    date: scDate.value,
    time: scTime.value,
    repeat: scRepeat.value,
    amount: Number(scAmount.value)
  };

  try {
    const r = await fetch(SCHEDULE_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    if (!r.ok) {
      const j = await r.json();
      alert(j.error || 'Add schedule failed');
      return;
    }

    loadSchedules();

  } catch (e) {
    alert('Server unreachable');
  }
}

/* ===============================
   INIT
================================ */
feedNowBtn.onclick     = feedNow;
addScheduleBtn.onclick = addSchedule;

loadSchedules();
loadFeedLogs();

setInterval(loadSchedules, 10000);
setInterval(loadFeedLogs, 10000);


/* ===============================
   MOBILE MENU
================================ */
menuBtn?.onclick = () => {
  document.querySelector('aside')?.classList.toggle('active');
};
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>AquaNova – Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />

  <link rel="icon" type="image/png"
        href="{{ url_for('static', filename='img/logo_aquanova.png') }}">
  <link rel="stylesheet"
        href="{{ url_for('static', filename='css/styles.css') }}">

  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>

  <style>
    :root{
      --brand:#0ea5e9;
      --bg:#f6f7fb;
      --ok:#16a34a;
      --bad:#dc2626;
      --muted:#6b7280;
    }

    *{box-sizing:border-box;margin:0;padding:0}
    body{
      background:var(--bg);
      font-family:system-ui,Arial;
      min-height:100vh;
      display:flex;
      flex-direction:column;
    }

    header{
      background:var(--brand);
      color:#fff;
      padding:14px 18px;
      display:flex;
      justify-content:space-between;
      align-items:center;
    }

    .layout{
      display:grid;
      grid-template-columns:240px 1fr;
      flex:1;
    }

    aside{
      background:#fff;
      border-right:1px solid #e5e7eb;
      padding:16px;
    }

    aside a{
      display:block;
      padding:10px 12px;
      border-radius:10px;
      margin-bottom:8px;
      text-decoration:none;
      color:#111;
    }

    aside a.active{
      background:#eef7ff;
      color:#0a6db2;
    }

    main{padding:20px}

    .cards{
      display:grid;
      grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
      gap:16px;
    }

    .card{
      background:#fff;
      border-radius:14px;
      padding:18px;
    }

    /* ===== LIGHT ===== */
    .light-header{
      display:flex;
      justify-content:space-between;
      align-items:center;
    }

    .toggle{
      width:44px;height:24px;
      border-radius:999px;
      background:#e5e7eb;
      position:relative;
      cursor:pointer;
    }
    .toggle.on{background:var(--ok)}
    .toggle .knob{
      width:20px;height:20px;
      background:#fff;border-radius:50%;
      position:absolute;top:2px;left:2px;
      transition:.2s;
    }
    .toggle.on .knob{left:22px}

    .light-status.on{color:var(--ok);font-weight:600}
    .light-status.off{color:var(--bad);font-weight:600}

    .segmented{
      display:flex;
      border:1px solid #e5e7eb;
      border-radius:10px;
      overflow:hidden;
    }
    .seg-btn{
      flex:1;
      padding:8px 0;
      border:none;
      background:#fff;
      cursor:pointer;
    }
    .seg-btn.active{
      background:#eef7ff;
      color:#0a6db2;
      font-weight:600;
    }

    .color-row{display:flex;gap:10px;align-items:center}
    .color-dot{
      width:26px;height:26px;border-radius:50%;
      border:2px solid #e5e7eb;
      cursor:pointer;
    }
    .color-dot.active{border:3px solid var(--brand)}

    /* ===== GRID ===== */
    .grid2{
      display:grid;
      grid-template-columns:1.2fr 1fr;
      gap:18px;
      margin-top:18px;
    }

    .badge{
      padding:4px 10px;
      border-radius:999px;
      font-size:12px;
    }
    .safe{background:#dcfce7;color:#166534}
    .alert{background:#fee2e2;color:#991b1b}

    table{width:100%;border-collapse:collapse}
    th,td{padding:8px;border-bottom:1px solid #eee;font-size:13px}

    footer{
      background:#fff;
      border-top:1px solid #e5e7eb;
      text-align:center;
      padding:14px;
      font-size:14px;
      color:var(--muted);
    }

    @media(max-width:1000px){
      .layout{grid-template-columns:1fr}
      aside{display:none}
      .grid2{grid-template-columns:1fr}
    }
    .btn-feed{
    width:100%;
    padding:12px 0;
    border:none;
    border-radius:12px;

    background:#0ea5e9;     /* xanh biển AquaNova */
    color:#ffffff;          /* chữ trắng */
    font-size:15px;
    font-weight:600;

    cursor:pointer;
    transition:all .2s ease;
  }

  .btn-feed:hover{
    background:#0284c7;     /* xanh đậm hơn khi hover */
  }

  .btn-feed:active{
    transform:scale(0.97);
  }

  .btn-feed:disabled{
    background:#93c5fd;     /* xanh nhạt khi disable */
    cursor:not-allowed;
  }
  .footer-full{
      width:100%;
      padding:14px 0;
      text-align:center;
      font-size:14px;
      background:#fff;
      color:#6b7280;
      border-top:1px solid #e5e7eb;
    }

  </style>
</head>

<body>

<header>
  <h2>AquaNova</h2>
  <span>Dashboard</span>
</header>

<div class="layout">

    <aside>
    <nav class="menu">
      <a href="{{ url_for('home') }}">Dashboard</a>
      <a href="{{ url_for('temperature_page') }}">Temperature</a>
      <a href="{{ url_for('turbidity_page') }}">Turbidity</a>
      <a class="active" href="{{ url_for('feed_timer_page') }}">Feed Timer</a>
      <a href="{{ url_for('chatbot.chatbot_page') }}">Chatbot</a>
    </nav>
  </aside>

  <main>

    <!-- ===== TOP CARDS ===== -->
    <div class="cards">

      <!-- LIGHT -->
      <div class="card">
        <div class="light-header">
          <h4>Light</h4>
          <div id="lightToggle" class="toggle on">
            <div class="knob"></div>
          </div>
        </div>
        <div id="lightStatus" class="light-status on">● ON</div>

        <div style="margin-top:12px">
          <div>Mode</div>
          <div class="segmented">
            <button class="seg-btn active" data-mode="0">Normal</button>
            <button class="seg-btn active" data-mode="1">Shift</button>
            <button class="seg-btn" data-mode="2">Blink</button>
          </div>
        </div>

        <div style="margin-top:12px">
          <div>Color</div>
          <div class="color-row">
            <button class="color-dot active" data-color="#FFFFFF" style="background:#fff"></button>
            <button class="color-dot" data-color="#FF0000" style="background:#dc2626"></button>
            <button class="color-dot" data-color="#2563eb" style="background:#2563eb"></button>
            <button class="color-dot" data-color="#16a34a" style="background:#16a34a"></button>
            <input type="color" id="customColor">
          </div>
        </div>
      </div>

      <!-- FEED -->
      <div class="card">
        <h4>Feed</h4>
        <button id="feedNowBtn" class="btn-feed">Feed now</button>
        <div id="feedNowMsg"></div>
      </div>

      <!-- WARNING -->
      <div class="card">
        <h4>Warnings</h4>
        <div id="warnTurb" class="badge safe">Turbidity OK</div>
        <div id="warnTemp" class="badge safe" style="margin-top:6px">Temperature OK</div>
      </div>

    </div>

    <!-- ===== CHART + TABLE ===== -->
    <div class="grid2">
      <div class="card">
        <h3>Turbidity</h3>
        <canvas id="turbChart" height="260"></canvas>
      </div>

      <div class="card">
        <h3>Temperature</h3>
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Temp (°C)</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody id="tempRows"></tbody>
        </table>
      </div>
    </div>

  </main>
</div>

<footer class="footer-full">
  <h4>Thành viên thực hiện</h4>
  <p>
    Hoàng Ngọc Dung – 23139006 |
    Đoàn Minh Duy Bình – 23139005 |
    Trần Hữu Dương – 23130009
  </p>
</footer>

<script src="{{ url_for('static', filename='js/dashboard.js') }}"></script>
</body>
</html>
