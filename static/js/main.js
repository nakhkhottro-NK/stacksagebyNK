// ════════════════════════════════════════════════════════════
// StackSage v2.0 — main.js
// Theme, mobile drawer, chat, share, bookmarks, animations
// ════════════════════════════════════════════════════════════

// ── THEME TOGGLE ────────────────────────────────────────────
function initTheme() {
  const saved = localStorage.getItem('stacksage_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  updateThemeIcon(saved);
}

function toggleTheme() {
  const cur = document.documentElement.getAttribute('data-theme');
  const next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('stacksage_theme', next);
  updateThemeIcon(next);
}

function updateThemeIcon(theme) {
  const btn = document.getElementById('themeToggle');
  if (btn) {
    btn.innerHTML = theme === 'dark' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
    btn.title = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
  }
}

// ── MOBILE DRAWER ───────────────────────────────────────────
function toggleDrawer() {
  document.getElementById('mobileDrawer')?.classList.toggle('open');
  document.getElementById('drawerOverlay')?.classList.toggle('show');
}

// ── QUERY HELPERS ───────────────────────────────────────────
function setQuery(text) {
  const input = document.getElementById('queryInput');
  const domain = document.getElementById('domainInput');
  if (input) {
    input.value = text;
    if (domain) domain.value = text;
    input.focus();
  }
}

// ── SEARCH FORM SUBMIT ──────────────────────────────────────
function initSearchForm() {
  const form = document.getElementById('searchForm');
  if (!form) return;
  form.addEventListener('submit', () => {
    const di = document.getElementById('domainInput');
    const qi = document.getElementById('queryInput');
    if (di && qi) di.value = qi.value.trim();
    const btn = document.getElementById('searchBtn');
    if (btn) {
      btn.querySelector('.btn-text')?.classList.add('hidden');
      btn.querySelector('.btn-loading')?.classList.remove('hidden');
      btn.disabled = true;
    }
  });
}

// ── TOAST ───────────────────────────────────────────────────
function showToast(message, isError = false) {
  let toast = document.getElementById('toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast'; toast.className = 'toast';
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.style.borderLeftColor = isError ? 'var(--accent-danger)' : 'var(--accent-3)';
  toast.style.borderLeftWidth = '4px';
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3000);
}

// ── BOOKMARK ────────────────────────────────────────────────
async function bookmarkRepo(name, url, stars, language, description) {
  try {
    const resp = await fetch('/api/bookmark', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_name: name, repo_url: url, stars, language, description })
    });
    const data = await resp.json();
    if (data.success) showToast(`✓ Bookmarked: ${name.split('/').pop()}`);
    else showToast('Failed to bookmark.', true);
  } catch (e) { showToast('Network error.', true); }
}

async function removeBookmark(bid, cardEl) {
  if (!confirm('Remove this bookmark?')) return;
  try {
    const r = await fetch(`/api/bookmark/${bid}`, { method: 'DELETE' });
    const d = await r.json();
    if (d.success) {
      cardEl?.remove();
      showToast('Bookmark removed.');
    }
  } catch (e) { showToast('Network error.', true); }
}

// ── SHARE LINK ──────────────────────────────────────────────
async function generateShareLink(searchId) {
  try {
    const r = await fetch(`/api/share/${searchId}`, { method: 'POST' });
    const d = await r.json();
    if (d.success) {
      navigator.clipboard.writeText(d.url).then(() => {
        showToast('📋 Share link copied!');
      }).catch(() => {
        prompt('Copy this link:', d.url);
      });
    }
  } catch (e) { showToast('Failed to create share link.', true); }
}

// ── AI CHAT WIDGET ──────────────────────────────────────────
let chatHistory = [];

function toggleChat() {
  const panel = document.getElementById('chatPanel');
  if (!panel) return;
  panel.classList.toggle('hidden');
  if (!panel.classList.contains('hidden') && chatHistory.length === 0) {
    appendChat('ai', "Hi! I'm StackSage AI. Ask me anything about these results — top repos, which to learn first, why certain languages dominate, anything 👋");
  }
}

function appendChat(role, text) {
  const box = document.getElementById('chatMessages');
  if (!box) return;
  const div = document.createElement('div');
  div.className = `chat-msg ${role}`;
  div.textContent = text;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

async function sendChatMessage() {
  const input = document.getElementById('chatInput');
  if (!input) return;
  const msg = input.value.trim();
  if (!msg) return;

  appendChat('user', msg);
  chatHistory.push({ role: 'user', text: msg });
  input.value = '';

  const box = document.getElementById('chatMessages');
  const loadingDiv = document.createElement('div');
  loadingDiv.className = 'chat-msg ai loading';
  loadingDiv.textContent = 'Thinking…';
  box.appendChild(loadingDiv);
  box.scrollTop = box.scrollHeight;

  try {
    const searchId = document.body.dataset.searchId || null;
    const r = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg, search_id: searchId, history: chatHistory })
    });
    const d = await r.json();
    loadingDiv.remove();
    const reply = d.reply || d.error || 'No response.';
    appendChat('ai', reply);
    chatHistory.push({ role: 'assistant', text: reply });
  } catch (e) {
    loadingDiv.remove();
    appendChat('ai', '⚠ Network error. Please try again.');
  }
}

function initChat() {
  const input = document.getElementById('chatInput');
  if (input) {
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter') { e.preventDefault(); sendChatMessage(); }
    });
  }
}

// ── SCROLL REVEAL ───────────────────────────────────────────
function initScrollReveal() {
  if (!('IntersectionObserver' in window)) return;
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        observer.unobserve(e.target);
      }
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.feat-card, .stat-card, .repo-card, .card')
    .forEach(el => {
      el.classList.add('reveal');
      observer.observe(el);
    });
}

// ── FLASH AUTO-DISMISS ──────────────────────────────────────
function initFlashes() {
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity 0.5s, transform 0.5s';
      el.style.opacity = '0';
      el.style.transform = 'translateX(40px)';
      setTimeout(() => el.remove(), 500);
    }, 5000);
  });
}

// ── INIT ────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initSearchForm();
  initChat();
  initScrollReveal();
  initFlashes();
});
