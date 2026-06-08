const video = document.querySelector('#camera-video');
const canvas = document.querySelector('#camera-canvas');
const context = canvas.getContext('2d');
const words = [];
let stream = null;
let socket = null;
let timer = null;

function renderWords() {
  document.querySelector('#word-list').innerHTML = words.map(word => `<span class="word">${displayLabel(word)}</span>`).join('');
}

function updateRealtime(result) {
  document.querySelector('#hands-status').textContent = result.hands_detected ? 'Đã detect' : 'Không thấy tay';
  document.querySelector('#window-status').textContent = `${result.window_frames}/30`;
  document.querySelector('#prediction-latency').textContent = `${result.elapsed_ms} ms`;
  if (result.prediction) {
    document.querySelector('#prediction-label').textContent =
      result.prediction.display_label || displayLabel(result.prediction.label);
    document.querySelector('#prediction-confidence').textContent = `${(result.prediction.confidence * 100).toFixed(1)}%`;
  }
  if (result.accepted_word) { words.push(result.accepted_word); renderWords(); }
}

document.querySelector('#start-camera').addEventListener('click', async () => {
  if (stream) return;
  stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false });
  video.srcObject = stream;
  const token = await ensureAccessToken();
  socket = new WebSocket(`${API.replace('http', 'ws')}/api/inference/ws?token=${encodeURIComponent(token)}`);
  socket.onmessage = event => updateRealtime(JSON.parse(event.data));
  socket.onopen = () => {
    timer = setInterval(() => {
      if (socket.readyState !== WebSocket.OPEN || video.videoWidth === 0) return;
      context.drawImage(video, 0, 0, 640, 480);
      socket.send(JSON.stringify({ frame: canvas.toDataURL('image/jpeg', 0.65) }));
    }, 100);
  };
});

document.querySelector('#stop-camera').addEventListener('click', () => {
  clearInterval(timer); timer = null;
  socket?.close(); socket = null;
  stream?.getTracks().forEach(track => track.stop()); stream = null;
});

document.querySelector('#reset-words').addEventListener('click', () => {
  words.length = 0; renderWords();
  document.querySelector('#translated-sentence').textContent = '...';
  document.querySelector('#translation-provider').textContent = '...';
});

document.querySelector('#translate-button').addEventListener('click', async () => {
  try {
    const result = await api('/api/inference/translate', { method: 'POST', body: JSON.stringify({ labels: words }) });
    document.querySelector('#translated-sentence').textContent = result.sentence || '...';
    document.querySelector('#translation-provider').textContent =
      result.provider === 'openai' ? 'OpenAI' : `Fallback${result.warning ? ` (${result.warning})` : ''}`;
  } catch (error) { showMessage(error.message); }
});
