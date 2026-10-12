const fileInput = document.getElementById('fileInput');
const dropzone = document.getElementById('dropzone');
const uploadStatus = document.getElementById('uploadStatus');
const docList = document.getElementById('docList');
const chunkCountBadge = document.getElementById('chunkCountBadge');
const chatStream = document.getElementById('chatStream');
const chatForm = document.getElementById('chatForm');
const queryInput = document.getElementById('queryInput');
const clearChatBtn = document.getElementById('clearChatBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  fetchDocuments();
  setupDragAndDrop();
});

// Drag and drop setup
function setupDragAndDrop() {
  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length) uploadFiles(files);
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) uploadFiles(fileInput.files);
  });
}

// Upload files
async function uploadFiles(files) {
  const formData = new FormData();
  for (let file of files) {
    formData.append('files', file);
  }

  uploadStatus.className = 'upload-status';
  uploadStatus.textContent = 'Indexing documents into vector store...';

  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });

    const data = await res.json();
    if (res.ok) {
      uploadStatus.className = 'upload-status success';
      uploadStatus.textContent = `Indexed ${data.documents.length} file(s) successfully!`;
      fetchDocuments();
      fileInput.value = '';
    } else {
      throw new Error(data.detail || 'Upload failed');
    }
  } catch (err) {
    uploadStatus.className = 'upload-status error';
    uploadStatus.textContent = `Error: ${err.message}`;
  }
}

// Fetch documents
async function fetchDocuments() {
  try {
    const res = await fetch('/api/documents');
    const data = await res.json();
    chunkCountBadge.textContent = `${data.total_chunks} chunks`;

    if (data.documents.length === 0) {
      docList.innerHTML = '<p class="empty-state">No documents indexed yet.</p>';
      return;
    }

    docList.innerHTML = data.documents.map(doc => `
      <div class="doc-card">
        <div class="doc-info">
          <span class="doc-name" title="${doc.filename}">${doc.filename}</span>
          <span class="doc-meta">${doc.num_chunks} chunks</span>
        </div>
        <button class="btn-del" onclick="deleteDocument('${doc.doc_id}')" title="Remove Document">✕</button>
      </div>
    `).join('');
  } catch (err) {
    console.error('Error fetching documents:', err);
  }
}

// Delete document
async function deleteDocument(docId) {
  try {
    const res = await fetch(`/api/documents/${docId}`, { method: 'DELETE' });
    if (res.ok) fetchDocuments();
  } catch (err) {
    console.error('Error deleting document:', err);
  }
}

// Submit query
chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const query = queryInput.value.trim();
  if (!query) return;

  appendMessage('user', query);
  queryInput.value = '';

  const assistantMsgId = appendMessage('assistant', '<div class="loading-pulse">Retrieving relevant chunks and generating answer...</div>');

  try {
    const res = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query, top_k: 4 })
    });

    const data = await res.json();
    if (res.ok) {
      updateAssistantMessage(assistantMsgId, data);
    } else {
      throw new Error(data.detail || 'Query failed');
    }
  } catch (err) {
    updateAssistantMessage(assistantMsgId, {
      answer: `Error: ${err.message}`,
      sources: []
    });
  }
});

function appendMessage(role, content) {
  const msgId = 'msg-' + Date.now();
  const msgEl = document.createElement('div');
  msgEl.className = `message ${role}`;
  msgEl.id = msgId;

  const avatar = role === 'user' ? '👤' : '🤖';
  msgEl.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div class="msg-body">${content}</div>
  `;

  chatStream.appendChild(msgEl);
  chatStream.scrollTop = chatStream.scrollHeight;
  return msgId;
}

function updateAssistantMessage(msgId, data) {
  const msgEl = document.getElementById(msgId);
  if (!msgEl) return;

  const bodyEl = msgEl.querySelector('.msg-body');
  
  let sourcesHtml = '';
  if (data.sources && data.sources.length > 0) {
    sourcesHtml = `
      <div class="sources-container">
        <div class="sources-title">Verified Sources (${data.sources.length})</div>
        <div class="source-badges">
          ${data.sources.map(s => `
            <span class="source-pill" title="${escapeHtml(s.excerpt)}">
              📄 ${s.filename} (Score: ${s.score})
            </span>
          `).join('')}
        </div>
        ${data.latency_sec ? `<div class="latency-meta">Retrieved & synthesized in ${data.latency_sec}s</div>` : ''}
      </div>
    `;
  }

  bodyEl.innerHTML = `
    <p>${escapeHtml(data.answer)}</p>
    ${sourcesHtml}
  `;

  chatStream.scrollTop = chatStream.scrollHeight;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.innerText = text;
  return div.innerHTML;
}

function usePrompt(text) {
  queryInput.value = text;
  queryInput.focus();
}

clearChatBtn.addEventListener('click', () => {
  chatStream.innerHTML = `
    <div class="message assistant welcome-card">
      <div class="msg-avatar">🤖</div>
      <div class="msg-body">
        <h3>DocuRAG Ready</h3>
        <p>Chat cleared. Ask a new question about your indexed documents.</p>
      </div>
    </div>
  `;
});
