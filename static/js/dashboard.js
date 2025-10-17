// ===============================================
//  AquaNova Dashboard Script (Fixed + Simplified)
//  Hiển thị dữ liệu mới nhất & phần trăm thức ăn
// ===============================================

// ---- API endpoints ----
const LATEST_API = '/dashboard/latest?n=200';
const SUMMARY_API = '/dashboard/summary';

async function loadSummary() {
  try {
    const res = await fetch(SUMMARY_API);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const json = await res.json();
    document.getElementById('summary').innerHTML =
      `<div>Ponds: <b>${json.ponds ?? 0}</b></div>
       <div>Devices: <b>${json.devices ?? 0}</b></div>`;
  } catch (e) {
    console.error(e);
    const el = document.getElementById('summary');
    if (el) el.textContent = 'Summary load error';
  }
}

// ---- Load Latest Readings & Feed Percentage ----
async function loadLatest() {
  try {
    const res = await fetch(LATEST_API);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const json = await res.json();
    const items = Array.isArray(json.items) ? json.items : [];

    // --- render bảng dữ liệu ---
    const tbody = document.querySelector('#readings tbody');
    if (tbody) {
      tbody.innerHTML = '';
      items.forEach(r => {
        const tr = document.createElement('tr');
        const ts = r.ts || '';
        const do_duc = r.turbidity ?? '';
        const nhiet_do = r.temperature ?? '';
        const phan_tram = r.feed ?? '';

        tr.innerHTML = `
          <td>${ts}</td>
          <td>${do_duc}</td>
          <td>${nhiet_do}</td>
          <td>${phan_tram}%</td>`;
        tbody.appendChild(tr);
      });
    }

    // --- chuẩn hoá dữ liệu feed (% thức ăn) ---
    const normalized = items
      .map(x => ({
        ts: x.ts,
        feed: x.feed ?? null
      }))
      .filter(x => x.feed != null && x.ts)
      .sort((a, b) => new Date(a.ts) - new Date(b.ts));

    // --- cập nhật 1 doughnut mới nhất ---
    updateFeedPie(normalized);
  } catch (e) {
    console.error('[loadLatest] error:', e);
  }
}

// ---- Doughnut Chart ----
let feedPieChart = null;

function ensureFeedPie() {
  if (feedPieChart) return feedPieChart;
  const canvas = document.getElementById('feedPie1');
  if (!canvas) return null;
  const ctx = canvas.getContext('2d');
  feedPieChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Remaining', 'Used'],
      datasets: [{
        data: [0, 100],
        backgroundColor: ['#4f46e5', '#e8eefb'],
        borderWidth: 0,
        hoverOffset: 3,
        cutout: '65%'
      }]
    },
    options: { plugins: { legend: { display: false } }, animation: { duration: 300 } }
  });
  return feedPieChart;
}

function setPie(percent, ts) {
  const chart = ensureFeedPie();
  if (!chart) return;

  const clamp = v => Math.max(0, Math.min(100, Number(v)));
  const p = isNaN(percent) ? NaN : clamp(percent);

  if (isNaN(p)) {
    chart.data.datasets[0].data = [0, 100];
    chart.update();
    document.getElementById('feedPie1Num').textContent = '--%';
    document.getElementById('feedPie1Time').textContent = '—';
    return;
  }

  const used = 100 - p;
  let color = '#4f46e5';
  if (p < 10) color = '#dc2626';
  else if (p < 30) color = '#d97706';

  chart.data.datasets[0].data = [p, used];
  chart.data.datasets[0].backgroundColor = [color, '#e8eefb'];
  chart.update();

  document.getElementById('feedPie1Num').textContent = `${p.toFixed(1)}%`;
  const d = new Date(ts);
  document.getElementById('feedPie1Time').textContent = isNaN(d) ? (ts || '') : d.toLocaleTimeString();
}

// --- cập nhật 1 biểu đồ gần nhất ---
function updateFeedPie(sortedItemsAsc) {
  if (!sortedItemsAsc.length) {
    setPie(NaN, '');
    return;
  }
  const last = sortedItemsAsc[sortedItemsAsc.length - 1];
  setPie(Number(last.feed), last.ts);
}

// ---- Khởi chạy ban đầu & cập nhật định kỳ ----
loadSummary();
loadLatest();
setInterval(() => { loadLatest(); loadSummary(); }, 10000);
document.addEventListener('DOMContentLoaded', () => {
  loadFeedStatus();
  setInterval(loadFeedStatus, 10000);
});