const API = '';
let currentSessionId = null;
let isStreaming = false;

(async function init() {
  const token = localStorage.getItem('miphi_token');
  if (!token) { window.location.href = '/'; return; }
  try {
    const res = await authFetch('/api/auth/me');
    if (!res.ok) { logout(); return; }
    const user = await res.json();
    document.getElementById('user-name').textContent = user.username;
    document.getElementById('user-avatar').textContent = user.username[0].toUpperCase();
  } catch(_) { logout(); return; }
  await loadSessions();
  checkHealth();
  setInterval(checkHealth, 30000); // recheck every 30s
})();

async function checkHealth() {
  const badge = document.getElementById('model-status');
  try {
    const res = await fetch(API + '/api/health');
    const data = await res.json();
    if (data.vllm && data.vllm.reachable) {
      const modelShort = (data.vllm.model || '').split('/').pop() || 'LLM';
      badge.textContent = '⬤ ' + modelShort + ' Online';
      badge.className = 'model-badge online';
    } else {
      badge.textContent = '⬤ LLM Offline';
      badge.className = 'model-badge offline';
    }
  } catch(_) {
    badge.textContent = '⬤ LLM Offline';
    badge.className = 'model-badge offline';
  }
}

function getToken() { return localStorage.getItem('miphi_token'); }
function authFetch(url, opts = {}) {
  return fetch(API + url, { ...opts, headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + getToken(), ...(opts.headers || {}) } });
}
function logout() { localStorage.removeItem('miphi_token'); window.location.href = '/'; }

async function loadSessions() {
  const res = await authFetch('/api/chat/sessions');
  if (!res.ok) return;
  const sessions = await res.json();
  const list = document.getElementById('sessions-list');
  if (!sessions.length) { list.innerHTML = '<p class="sessions-empty">No conversations yet</p>'; return; }
  list.innerHTML = sessions.map(s => `<div class="session-item ${s.id === currentSessionId ? 'active' : ''}" onclick="loadSession('${s.id}', this.dataset.title)" data-id="${s.id}" data-title="${s.title.replace(/"/g,'&quot;')}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg><span class="session-item-title">${esc(s.title)}</span></div>`).join('');
}

async function createNewSession() {
  const res = await authFetch('/api/chat/sessions', { method: 'POST', body: JSON.stringify({ title: 'New Chat' }) });
  if (!res.ok) return;
  const s = await res.json();
  currentSessionId = s.id;
  document.getElementById('session-title').textContent = s.title;
  document.getElementById('messages-area').innerHTML = buildWelcome();
  await loadSessions(); markActive(s.id);
}

async function loadSession(id, title) {
  currentSessionId = id;
  document.getElementById('session-title').textContent = title;
  markActive(id);
  const res = await authFetch('/api/chat/sessions/' + id + '/messages');
  if (!res.ok) return;
  const msgs = await res.json();
  const area = document.getElementById('messages-area');
  area.innerHTML = msgs.length ? '' : buildWelcome();
  msgs.forEach(m => appendMessage(m.role, m.content));
  scrollToBottom();
}

function markActive(id) {
  document.querySelectorAll('.session-item').forEach(el => el.classList.toggle('active', el.dataset.id === id));
}

async function sendMessage() {
  if (isStreaming) return;
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;
  if (!currentSessionId) await createNewSession();
  input.value = ''; input.style.height = 'auto';
  document.getElementById('messages-area').querySelector('#welcome-screen')?.remove();
  appendMessage('user', text); scrollToBottom();
  const aEl = appendMessage('assistant', '', { streaming: true });
  isStreaming = true; document.getElementById('send-btn').disabled = true;
  try {
    const res = await authFetch('/api/chat/stream', { method: 'POST', body: JSON.stringify({ session_id: currentSessionId, message: text }) });
    if (!res.ok) { const err = await res.json(); updateContent(aEl, '⚠️ Error: ' + (err.detail || 'Unknown error')); return; }
    const reader = res.body.getReader(); const dec = new TextDecoder();
    let full = '';
    while (true) {
      const { done, value } = await reader.read(); if (done) break;
      const lines = dec.decode(value).split('\n');
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const p = line.slice(6);
        if (p === '[DONE]') break;
        if (p.startsWith('[ERROR]')) {
          const errMsg = p.slice(7).trim();
          // Provide friendly message for connection errors
          if (errMsg.includes('Connection error') || errMsg.includes('connect')) {
            updateContent(aEl, '⚠️ The LLM engine (vLLM) is not running. Please start vLLM first.\n\nRun in a new terminal:\n  cd /home/aloukik_joshi/miphi-chatbot\n  docker compose up vllm_cpu\n\nOr check the status badge at the top right.');
          } else {
            updateContent(aEl, '⚠️ ' + errMsg);
          }
          checkHealth(); // refresh badge
          break;
        }
        full += p.replace(/\\n/g, '\n');
        updateContent(aEl, full, true); scrollToBottom();
      }
    }
    if (full) {
      updateContent(aEl, full, false);
      await loadSessions();
    }
  } catch(err) { updateContent(aEl, '⚠️ Network error: ' + err.message); }
  finally { isStreaming = false; document.getElementById('send-btn').disabled = false; scrollToBottom(); }
}

function sendQuickMessage(btn) { document.getElementById('chat-input').value = btn.textContent; sendMessage(); }

function appendMessage(role, content, opts = {}) {
  const area = document.getElementById('messages-area');
  const av = role === 'user' ? (document.getElementById('user-avatar').textContent || 'U') : 'M';
  const div = document.createElement('div');
  div.className = 'message ' + role;
  div.innerHTML = `<div class="message-avatar">${av}</div><div class="message-content ${opts.streaming ? 'streaming-cursor' : ''}">${opts.streaming ? '<div class="typing-indicator"><span></span><span></span><span></span></div>' : esc(content)}</div>`;
  area.appendChild(div); return div;
}

function updateContent(el, content, streaming = false) {
  const c = el.querySelector('.message-content');
  c.style.whiteSpace = 'pre-wrap';
  c.textContent = content;
  c.classList.toggle('streaming-cursor', streaming);
}

function buildWelcome() {
  return '<div class="welcome-screen" id="welcome-screen"><div class="welcome-icon">M</div><h2>MiPhi AI Assistant</h2><p>Ask me anything about MiPhi products, storage, embedded systems, or semiconductor technology.</p><div class="welcome-chips"><button class="chip" onclick="sendQuickMessage(this)">Tell me about MiPhi B100</button><button class="chip" onclick="sendQuickMessage(this)">What are enterprise SSD options?</button><button class="chip" onclick="sendQuickMessage(this)">Explain NAND flash technology</button></div></div>';
}

function scrollToBottom() { const a = document.getElementById('messages-area'); a.scrollTop = a.scrollHeight; }
function esc(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function handleInputKey(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }
function autoResize(el) { el.style.height = 'auto'; el.style.height = Math.min(el.scrollHeight, 160) + 'px'; }
function toggleSidebar() { document.getElementById('sidebar').classList.toggle('collapsed'); }
