  const LATEST_API = '/dashboard/latest?n=200';   // lấy đủ để có 2 mẫu gần nhất
  const SUMMARY_API = '/dashboard/summary';

  async function loadSummary() {
    try {
      const res = await fetch(SUMMARY_API);
      if (!res.ok) throw new Error('HTTP '+res.status);
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

  // ====== Bảng dữ liệu + cập nhật 2 doughnut ======
  async function loadLatest() {
    try {
      const res = await fetch(LATEST_API);
      if (!res.ok) throw new Error('HTTP '+res.status);
      const json = await res.json();
      const items = Array.isArray(json.items) ? json.items : [];

      // --- render bảng (tuỳ dữ liệu của bạn)
      const tbody = document.querySelector('#readings tbody');
      if (tbody) {
        tbody.innerHTML = '';
        items.forEach(r => {
          const tr = document.createElement('tr');
          const ts = r.ts || '';
          const dev = r.deviceId || r.device_id || '';
          const pH  = r.ph ?? '';
          const DO  = r.do ?? r.turbidity ?? '';     // tuỳ schema
          const T   = r.temp ?? r.temperature ?? '';

          tr.innerHTML = `
            <td>${ts}</td>
            <td>${dev}</td>
            <td>${pH}</td>
            <td>${DO}</td>
            <td>${T}</td>`;
          tbody.appendChild(tr);
        });
      }

      // --- chuẩn hoá dữ liệu feed và sort tăng theo thời gian
      const normalized = items
        .map(x => ({
          ts: x.ts,
          feed: (x.feed_amount ?? x.feed)
        }))
        .filter(x => x.feed != null && x.ts);

      normalized.sort((a,b) => new Date(a.ts) - new Date(b.ts));

      // --- cập nhật 2 doughnut gần nhất
      updateLastTwoPies(normalized);
    } catch (e) {
      console.error(e);
    }
  }

  // ====== DOUGHNUT (2 bản ghi gần nhất) ======
  const pieCharts = {};  // lưu instance theo id canvas

  function ensureFeedPie(canvasId){
    if (pieCharts[canvasId]) return pieCharts[canvasId];
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null; // phòng ngừa thiếu phần tử
    const ctx = canvas.getContext('2d');
    pieCharts[canvasId] = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Remaining','Used'],
        datasets: [{
          data: [0, 100],
          backgroundColor: ['#4f46e5', '#e8eefb'],
          borderWidth: 0,
          hoverOffset: 3,
          cutout: '65%'
        }]
      },
      options: { plugins:{ legend:{ display:false } }, animation:{ duration:300 } }
    });
    return pieCharts[canvasId];
  }

  function setPie(canvasId, percent, numId, timeId, warnId, ts){
    const chart = ensureFeedPie(canvasId);
    if (!chart) return;

    const clamp01 = v => Math.max(0, Math.min(100, Number(v)));
    const p = isNaN(percent) ? NaN : clamp01(percent);

    if (isNaN(p)) {
      chart.data.datasets[0].data = [0, 100];
      chart.data.datasets[0].backgroundColor = ['#4f46e5', '#e8eefb'];
      chart.update();
      const n = document.getElementById(numId);
      const t = document.getElementById(timeId);
      const w = document.getElementById(warnId);
      if (n) n.textContent = '--%';
      if (t) t.textContent = '—';
      if (w) w.style.display = 'none';
      return;
    }

    const used = 100 - p;
    let color = '#4f46e5';
    if (p < 10) color = '#dc2626';
    else if (p < 30) color = '#d97706';

    chart.data.datasets[0].data = [p, used];
    chart.data.datasets[0].backgroundColor = [color, '#e8eefb'];
    chart.update();

    const n = document.getElementById(numId);
    const t = document.getElementById(timeId);
    const w = document.getElementById(warnId);
    if (n) n.textContent = `${p.toFixed(1)}%`;
    if (t) {
      const d = new Date(ts);
      t.textContent = isNaN(d) ? (ts || '') : d.toLocaleTimeString();
    }
    if (w) w.style.display = (p < 10) ? 'inline-block' : 'none';
  }

  /** Cập nhật 2 doughnut từ mảng bản ghi đã sort tăng theo thời gian */
  function updateLastTwoPies(sortedItemsAsc){
    const n = sortedItemsAsc.length;
    const last1 = n >= 1 ? sortedItemsAsc[n-1] : null; // mới nhất
    const last2 = n >= 2 ? sortedItemsAsc[n-2] : null; // kế trước

    if (last1)
      setPie('feedPie1', Number(last1.feed), 'feedPie1Num', 'feedPie1Time', 'feedPie1Warn', last1.ts);
    else
      setPie('feedPie1', NaN, 'feedPie1Num', 'feedPie1Time', 'feedPie1Warn');

    if (last2)
      setPie('feedPie2', Number(last2.feed), 'feedPie2Num', 'feedPie2Time', 'feedPie2Warn', last2.ts);
    else
      setPie('feedPie2', NaN, 'feedPie2Num', 'feedPie2Time', 'feedPie2Warn');
  }

  // ====== chạy lần đầu & poll ======
  loadSummary();
  loadLatest();
  setInterval(() => { loadLatest(); loadSummary(); }, 10000);
