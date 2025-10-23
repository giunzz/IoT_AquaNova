// ===============================================
//  AquaNova Dashboard Script (Final Version)
//  Hiển thị dữ liệu cảm biến, đồng bộ thời gian,
//  biểu đồ thức ăn và thống kê tổng quan hệ thống
//  (Đã fix hiển thị múi giờ Việt Nam GMT+7)
// ===============================================

// ---- API endpoints ----
const LATEST_API = '/dashboard/latest?n=200';
const SUMMARY_API = '/dashboard/summary';

// ------------------------------------------------------------
// 🕐 Hàm tiện ích: Chuyển thời gian UTC → Giờ Việt Nam (GMT+7)
// ------------------------------------------------------------
function toVNTime(ts) {
  if (!ts) return '';
  const d = new Date(ts);
  if (isNaN(d)) return ts;
  d.setHours(d.getHours() + 7);
  return d.toLocaleString('vi-VN', { hour12: false });
}

// ------------------------------------------------------------
// 📊 Load thống kê tổng quan (số hồ, số thiết bị)
// ------------------------------------------------------------
async function loadSummary() {
  try {
    const res = await fetch(SUMMARY_API);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const json = await res.json();

    document.getElementById('summary').innerHTML = `
      <div>Ponds: <b>${json.ponds ?? 0}</b></div>
      <div>Devices: <b>${json.devices ?? 0}</b></div>`;
  } catch (e) {
    console.error(e);
    const el = document.getElementById('summary');
    if (el) el.textContent = 'Summary load error';
  }
}

// ------------------------------------------------------------
// 📈 Load dữ liệu mới nhất (độ đục, nhiệt độ, % thức ăn)
// ------------------------------------------------------------
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
        tr.innerHTML = `
          <td>${toVNTime(r.ts)}</td>
          <td>${r.turbidity ?? ''}</td>
          <td>${r.temperature ?? ''}</td>
          <td>${r.feed ?? ''}%</td>`;
        tbody.appendChild(tr);
      });
    }

    // --- chuẩn hoá dữ liệu thức ăn (% feed) ---
    const normalized = items
      .map(x => ({ ts: x.ts, feed: x.feed ?? null }))
      .filter(x => x.feed != null && x.ts)
      .sort((a, b) => new Date(a.ts) - new Date(b.ts));

    // --- cập nhật biểu đồ thức ăn ---
    updateFeedPie(normalized);
  } catch (e) {
    console.error('[loadLatest] error:', e);
  }
}

// ------------------------------------------------------------
// 🥧 Biểu đồ Doughnut hiển thị phần trăm thức ăn
// ------------------------------------------------------------
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
    options: { 
      plugins: { legend: { display: false } },
      animation: { duration: 300 } 
    }
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
  if (p < 10) color = '#dc2626';     // đỏ cảnh báo
  else if (p < 30) color = '#d97706'; // cam cảnh báo nhẹ

  chart.data.datasets[0].data = [p, used];
  chart.data.datasets[0].backgroundColor = [color, '#e8eefb'];
  chart.update();

  // Hiển thị giá trị % và thời gian tương ứng
  document.getElementById('feedPie1Num').textContent = `${p.toFixed(1)}%`;
  document.getElementById('feedPie1Time').textContent = toVNTime(ts);
}

// --- cập nhật biểu đồ với bản ghi mới nhất ---
function updateFeedPie(sortedItemsAsc) {
  if (!sortedItemsAsc.length) {
    setPie(NaN, '');
    return;
  }
  const last = sortedItemsAsc[sortedItemsAsc.length - 1];
  setPie(Number(last.feed), last.ts);
}

// ------------------------------------------------------------
// ⏱️ Khởi chạy ban đầu & cập nhật định kỳ
// ------------------------------------------------------------
function initDashboard() {
  loadSummary();
  loadLatest();

  // Cập nhật mỗi 10 giây
  setInterval(() => {
    loadLatest();
    loadSummary();
  }, 10000);
}

// Khi trang web đã load xong
document.addEventListener('DOMContentLoaded', initDashboard);
