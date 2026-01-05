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
