const API = '';

function switchTab(tab) {
  clearMessage();
  const show = tab === 'login' ? 'form-login' : 'form-register';
  const hide = tab === 'login' ? 'form-register' : 'form-login';
  document.getElementById(show).classList.remove('hidden');
  document.getElementById(hide).classList.add('hidden');
  document.getElementById('tab-login').classList.toggle('active', tab === 'login');
  document.getElementById('tab-register').classList.toggle('active', tab === 'register');
}

function showMessage(text, type = 'error') {
  const el = document.getElementById('auth-message');
  el.textContent = text;
  el.className = 'auth-message ' + type;
  el.classList.remove('hidden');
}

function clearMessage() {
  document.getElementById('auth-message').classList.add('hidden');
}

function setLoading(btnId, loading) {
  const btn = document.getElementById(btnId);
  btn.disabled = loading;
  btn.querySelector('.btn-label').classList.toggle('hidden', loading);
  btn.querySelector('.btn-spinner').classList.toggle('hidden', !loading);
}

async function handleLogin(e) {
  e.preventDefault(); clearMessage();
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value;
  if (!username || !password) { showMessage('Please fill in all fields.'); return; }
  setLoading('login-btn', true);
  try {
    const res = await fetch(API + '/api/auth/login', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({username, password}) });
    const data = await res.json();
    if (!res.ok) { showMessage(data.detail || 'Login failed.'); return; }
    localStorage.setItem('miphi_token', data.access_token);
    window.location.href = '/chat.html';
  } catch(err) { showMessage('Network error — is the server running?'); }
  finally { setLoading('login-btn', false); }
}

async function handleRegister(e) {
  e.preventDefault(); clearMessage();
  const username = document.getElementById('reg-username').value.trim();
  const email = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-password').value;
  if (!username || !email || !password) { showMessage('Please fill in all fields.'); return; }
  if (password.length < 8) { showMessage('Password must be at least 8 characters.'); return; }
  setLoading('register-btn', true);
  try {
    const res = await fetch(API + '/api/auth/register', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({username, email, password}) });
    const data = await res.json();
    if (!res.ok) { showMessage(data.detail || 'Registration failed.'); return; }
    localStorage.setItem('miphi_token', data.access_token);
    window.location.href = '/chat.html';
  } catch(err) { showMessage('Network error — is the server running?'); }
  finally { setLoading('register-btn', false); }
}

(function(){ if (localStorage.getItem('miphi_token')) window.location.href = '/chat.html'; })();
