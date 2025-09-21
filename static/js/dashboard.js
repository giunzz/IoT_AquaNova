async function loadSummary() {
  const res = await fetch('/dashboard/summary');
  const json = await res.json();
  document.getElementById('summary').innerHTML =
    `<div>Ponds: <b>${json.ponds}</b></div><div>Devices: <b>${json.devices}</b></div>`;
}

async function loadLatest() {
  const res = await fetch('/dashboard/latest');
  const json = await res.json();
  const tbody = document.querySelector('#readings tbody');
  tbody.innerHTML = '';
  json.items.forEach(r => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${r.ts || ''}</td><td>${r.deviceId || ''}</td><td>${r.ph ?? ''}</td><td>${r.do ?? ''}</td><td>${r.temp ?? ''}</td>`;
    tbody.appendChild(tr);
  });
}

// load ngay và poll mỗi 10s
loadSummary();
loadLatest();
setInterval(loadLatest, 10000);
