document.addEventListener('DOMContentLoaded', () => {
  const goToWorkspace = document.getElementById('goToWorkspace');
  const workspace = document.getElementById('workspace');
  const uploadForm = document.getElementById('uploadForm');
  const uploadStatus = document.getElementById('uploadStatus');
  const docList = document.getElementById('docList');
  const askForm = document.getElementById('askForm');
  const answerContainer = document.getElementById('answerContainer');
  const citationsList = document.getElementById('citationsList');
  const fileInput = document.getElementById('fileInput');
  const chatForm = document.getElementById('chatForm');
  const chatInput = document.getElementById('chatInput');
  const chatMessages = document.getElementById('chatMessages');
  const chatClear = document.getElementById('chatClear');

  const STORAGE_KEY = 'docuhelp_local_index_v1';
  let state = { documents: [], pages: [] };
  const CHAT_KEY = 'docuhelp_chat_v1';
  let chat = []; // {role:'me'|'bot', text:string, at:number}

  function saveState() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch {}
  }

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) state = JSON.parse(raw);
    } catch {}
  }

  loadState();
  loadChat();
  renderDocList();
  renderChat();

  if (goToWorkspace && workspace) {
    goToWorkspace.addEventListener('click', () => {
      workspace.style.display = 'grid';
      window.scrollTo({ top: workspace.offsetTop - 12, behavior: 'smooth' });
    });
  }

  if (uploadForm) {
    uploadForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const files = fileInput.files;
      if (!files || files.length === 0) {
        uploadStatus.textContent = 'Aucun fichier sélectionné.';
        return;
      }
      uploadStatus.textContent = 'Indexation en cours…';
      for (const file of files) {
        const docId = `${Date.now()}_${Math.random().toString(36).slice(2)}`;
        state.documents.unshift({ id: docId, name: file.name, size: file.size, type: file.type || guessMime(file.name) });
        const ext = (file.name.split('.').pop() || '').toLowerCase();
        if (ext === 'txt') {
          const text = await file.text();
          state.pages.push({ docId, page: 1, text: normalize(text), name: file.name });
        } else if (ext === 'pdf') {
          const pages = await extractPdfPages(file);
          pages.forEach(p => state.pages.push({ docId, page: p.page, text: normalize(p.text), name: file.name }));
        }
      }
      saveState();
      renderDocList();
      uploadStatus.textContent = 'Indexation terminée.';
      fileInput.value = '';
    });
  }

  if (askForm) {
    askForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const q = document.getElementById('question').value.trim();
      if (!q) return;
      answerContainer.textContent = 'Recherche en cours…';
      citationsList.innerHTML = '';
      const results = search(q, state.pages);
      if (results.length === 0) {
        answerContainer.textContent = 'Aucune information pertinente trouvée.';
        return;
      }
      const top = results.slice(0, 5);
      const snippets = top.map(r => `• ${escapeHtml(r.snippet)}…`).join('\n');
      answerContainer.innerHTML = snippets.replace(/\n/g, '<br/>');
      top.forEach(r => {
        const li = document.createElement('li');
        li.textContent = `${r.name} — page ${r.page}`;
        li.title = r.snippet;
        citationsList.appendChild(li);
      });

      // Enrichir le chat avec la question et un condensé de réponse
      pushChat('me', q);
      pushChat('bot', top.map(x => `Extrait ${x.name} p.${x.page}: ${x.snippet}`).join('\n'));
      renderChat();
      saveChat();
    });
  }

  if (chatForm && chatInput) {
    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const msg = chatInput.value.trim();
      if (!msg) return;
      pushChat('me', msg);
      // Simule une réponse: utilise la recherche
      const results = search(msg, state.pages).slice(0, 2);
      const reply = results.length ? results.map(r => `${r.name} p.${r.page}: ${r.snippet}`).join('\n') : "Je n'ai rien trouvé dans les documents.";
      pushChat('bot', reply);
      chatInput.value = '';
      renderChat();
      saveChat();
    });
  }

  if (chatClear) {
    chatClear.addEventListener('click', () => {
      chat = [];
      renderChat();
      saveChat();
    });
  }

  function renderDocList() {
    if (!docList) return;
    docList.innerHTML = '';
    if (state.documents.length === 0) {
      const li = document.createElement('li');
      li.className = 'muted';
      li.textContent = 'Aucun document pour le moment.';
      docList.appendChild(li);
      return;
    }
    for (const d of state.documents) {
      const li = document.createElement('li');
      const meta = `${(d.type || '').split('/')[1] || 'fichier'} · ${d.size} o`;
      li.innerHTML = `<span class="doc-name">${escapeHtml(d.name)}</span> <span class="doc-meta muted">${meta}</span>`;
      docList.appendChild(li);
    }
  }

  function search(query, pages) {
    const tokens = tokenize(query);
    const scored = [];
    for (const p of pages) {
      const textLower = p.text.toLowerCase();
      let score = 0;
      for (const t of tokens) {
        score += countOccurrences(textLower, t);
      }
      if (score > 0) {
        scored.push({ ...p, score, snippet: p.text.slice(0, 240) });
      }
    }
    scored.sort((a, b) => b.score - a.score);
    return scored;
  }

  function tokenize(q) {
    const stop = new Set(['le','la','les','de','des','du','un','une','et','ou','a','à','au','aux','the','an','of','for','to','in','on','is','are','est','sont','avec','par','pour','sur','dans','que','qui']);
    return q.toLowerCase().split(/[^\p{L}\p{N}]+/u).filter(t => t && t.length > 2 && !stop.has(t));
  }

  function countOccurrences(haystack, needle) {
    let count = 0, i = 0;
    while ((i = haystack.indexOf(needle, i)) !== -1) { count++; i += needle.length; }
    return count;
  }

  function normalize(text) {
    return text.replace(/\r/g, '').replace(/[\x00-\x09\x0B\x0C\x0E-\x1F]+/g, ' ').replace(/\s+/g, ' ').trim();
  }

  function guessMime(name) {
    const ext = (name.split('.').pop() || '').toLowerCase();
    if (ext === 'pdf') return 'application/pdf';
    if (ext === 'txt') return 'text/plain';
    return 'application/octet-stream';
  }

  async function extractPdfPages(file) {
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await window['pdfjsLib'].getDocument({ data: arrayBuffer }).promise;
    const pages = [];
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      const text = content.items.map(it => it.str || '').join(' ');
      pages.push({ page: i, text });
    }
    return pages;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
  }

  function pushChat(role, text) {
    chat.push({ role, text, at: Date.now() });
    if (chat.length > 200) chat.shift();
  }

  function renderChat() {
    if (!chatMessages) return;
    chatMessages.innerHTML = '';
    for (const m of chat) {
      const div = document.createElement('div');
      div.className = 'chat-bubble ' + (m.role === 'me' ? 'me' : '');
      div.textContent = m.text;
      chatMessages.appendChild(div);
    }
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function saveChat() {
    try { localStorage.setItem(CHAT_KEY, JSON.stringify(chat)); } catch {}
  }

  function loadChat() {
    try {
      const raw = localStorage.getItem(CHAT_KEY);
      if (raw) chat = JSON.parse(raw);
    } catch {}
  }
});

