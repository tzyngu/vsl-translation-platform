const API = document.body.dataset.backendUrl;
let accessToken = null;
let accessTokenPromise = null;

function getCookie(name) {
  return document.cookie.split('; ').find(row => row.startsWith(`${name}=`))?.split('=')[1] || '';
}

async function ensureAccessToken() {
  if (accessToken) return accessToken;
  if (!accessTokenPromise) {
    accessTokenPromise = fetch('/api/token/', {
      method: 'POST',
      headers: { 'X-CSRFToken': decodeURIComponent(getCookie('csrftoken')) },
    }).then(async response => {
      if (response.status === 401 || response.status === 403) throw new Error('Phiên đăng nhập đã hết hạn.');
      if (!response.ok) throw new Error('Không thể kết nối dịch vụ xác thực.');
      accessToken = (await response.json()).token;
      return accessToken;
    }).finally(() => { accessTokenPromise = null; });
  }
  return accessTokenPromise;
}

async function api(path, options = {}) {
  const token = await ensureAccessToken();
  const response = await fetch(`${API}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`, ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    if (response.status === 401 && !location.pathname.startsWith('/login') && !location.pathname.startsWith('/register')) {
      location.href = '/login/';
    }
    throw new Error(body.detail || JSON.stringify(body));
  }
  return response.json();
}

function showMessage(text) {
  const node = document.querySelector('#global-message');
  if (!node) return;
  node.textContent = text;
  node.classList.remove('hidden');
}

async function loadDashboard() {
  if (!document.querySelector('#gesture-count')) return;
  try {
    const [health, gestures, active] = await Promise.all([api('/api/health'), api('/api/gestures'), api('/api/models/active')]);
    document.querySelector('#backend-health').textContent = health.status;
    document.querySelector('#gesture-count').textContent = `${gestures.length} ký hiệu`;
    document.querySelector('#active-model').textContent = active.model_name;
  } catch (error) { showMessage(error.message); }
}

function gestureCard(gesture, withImport = false) {
  const uploader = withImport ? `<div class="gesture-uploader"><img src="${gesture.owner_avatar_url || '/static/images/avatar1.png'}" alt="Avatar"><span><small>Người upload</small><strong>${gesture.owner_username || 'Người dùng'}</strong></span></div>` : '';
  return `<article class="card gesture-card">${uploader}<h2>${gesture.display_name}</h2><p><code>${gesture.label_name}</code></p><p>${gesture.description || ''}</p><p>${gesture.num_samples || 0} samples</p>${withImport ? `<button data-import="${gesture._id}">Import</button>` : ''}</article>`;
}

async function loadGestures() {
  const target = document.querySelector('#gesture-list');
  if (!target) return;
  try { target.innerHTML = (await api('/api/gestures')).map(item => gestureCard(item)).join(''); }
  catch (error) { showMessage(error.message); }
}

async function loadLibrary() {
  const target = document.querySelector('#public-gesture-list');
  if (!target) return;
  try {
    target.innerHTML = (await api('/api/gestures/public')).map(item => gestureCard(item, true)).join('');
    target.querySelectorAll('[data-import]').forEach(button => button.addEventListener('click', async () => {
      await api(`/api/gestures/${button.dataset.import}/import`, { method: 'POST' });
      button.textContent = 'Đã import';
      button.disabled = true;
    }));
  } catch (error) { showMessage(error.message); }
}

document.querySelector('#gesture-form')?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const payload = {
    label_name: form.get('label_name'), display_name: form.get('display_name'),
    description: form.get('description'), is_public: form.get('is_public') === 'on',
  };
  try {
    const gesture = await api('/api/gestures', { method: 'POST', body: JSON.stringify(payload) });
    const files = new FormData();
    for (const file of form.getAll('files')) files.append('files', file);
    const token = await ensureAccessToken();
    const response = await fetch(`${API}/api/gestures/${gesture._id}/samples`, { method: 'POST', credentials: 'include', headers: { 'Authorization': `Bearer ${token}` }, body: files });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Không thể xử lý video.');
    document.querySelector('#upload-result').textContent = JSON.stringify(result, null, 2);
  } catch (error) { showMessage(error.message); }
});

async function loadJobs() {
  const target = document.querySelector('#training-job-list');
  if (!target) return;
  const jobs = await api('/api/training/jobs');
  target.innerHTML = jobs.map(job => `<article class="card"><strong>${job.status}</strong><p>${job.message || ''}</p><small>${job.created_at}</small></article>`).join('');
}
document.querySelector('#create-training-job')?.addEventListener('click', async () => { await api('/api/training/jobs', { method: 'POST' }); loadJobs(); });

async function loadModels() {
  const target = document.querySelector('#model-list');
  if (!target) return;
  const models = await api('/api/models');
  target.innerHTML = models.map(model => `<article class="card"><strong>${model.model_name}</strong><p>${model.architecture || ''}</p><code>${model.model_path}</code><p>${model.is_active ? 'Active' : ''}</p></article>`).join('');
}

loadDashboard(); loadGestures(); loadLibrary(); loadJobs(); loadModels();
