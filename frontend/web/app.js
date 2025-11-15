const API_BASE = window.APP_CONFIG?.API_BASE || window.API_BASE || "http://localhost:8088";
const PAGE_SIZE = 5;

const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message");
const messages = document.getElementById("messages");
const chatStatus = document.getElementById("chat-status");
const searchForm = document.getElementById("search-form");
const searchText = document.getElementById("search-text");
const searchStatus = document.getElementById("search-status");
const searchResults = document.getElementById("search-results");
const uploadForm = document.getElementById("upload-form");
const uploadStatus = document.getElementById("upload-status");
const uploadResult = document.getElementById("upload-result");
const fileInput = document.getElementById("file");
const uploadsList = document.getElementById("uploads-list");
const refreshUploadsBtn = document.getElementById("refresh-uploads");
const moreUploadsBtn = document.getElementById("more-uploads");
const logsList = document.getElementById("logs-list");
const refreshLogsBtn = document.getElementById("refresh-logs");
const moreLogsBtn = document.getElementById("more-logs");

let uploadsOffset = 0;
let logsOffset = 0;

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `bubble ${role}`;
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

function formatDate(dateStr) {
  if (!dateStr) return "";
  try {
    return new Date(dateStr).toLocaleString();
  } catch (_) {
    return dateStr;
  }
}

async function loadUploads(reset = false) {
  if (reset) uploadsOffset = 0;
  if (reset) uploadsList.innerHTML = "";
  const url = `${API_BASE}/api/uploads?limit=${PAGE_SIZE}&offset=${uploadsOffset}`;
  try {
    const resp = await fetch(url);
    if (!resp.ok) throw new Error("No se pudo obtener uploads");
    const data = await resp.json();
    const items = data.items || [];
    items.forEach((u) => {
      const item = document.createElement("div");
      item.className = "list-item";
      const meta = document.createElement("div");
      meta.className = "list-meta";
      meta.textContent = `${formatDate(u.created_at)} | ${u.content_type || ""} | ${Math.round((u.size_bytes || 0)/1024)} KB`;
      item.textContent = `${u.id} | ${u.filename}`;
      item.appendChild(meta);
      uploadsList.appendChild(item);
    });
    if (!uploadsList.childElementCount) uploadsList.textContent = "Sin uploads";
    uploadsOffset += items.length;
  } catch (err) {
    console.error(err);
    if (!uploadsList.childElementCount) uploadsList.textContent = "Error al cargar uploads";
  }
}

async function loadLogs(reset = false) {
  if (reset) logsOffset = 0;
  if (reset) logsList.innerHTML = "";
  const url = `${API_BASE}/api/chat/logs?limit=${PAGE_SIZE}&offset=${logsOffset}`;
  try {
    const resp = await fetch(url);
    if (!resp.ok) throw new Error("No se pudo obtener logs");
    const data = await resp.json();
    const items = data.items || [];
    items.forEach((l) => {
      const item = document.createElement("div");
      item.className = "list-item";
      const meta = document.createElement("div");
      meta.className = "list-meta";
      meta.textContent = `${formatDate(l.created_at)} | ${l.provider || ""}`;
      item.textContent = l.message?.slice(0, 80) || "";
      item.appendChild(meta);
      logsList.appendChild(item);
    });
    if (!logsList.childElementCount) logsList.textContent = "Sin logs";
    logsOffset += items.length;
  } catch (err) {
    console.error(err);
    if (!logsList.childElementCount) logsList.textContent = "Error al cargar logs";
  }
}

async function runSearch(text) {
  searchStatus.textContent = "Buscando...";
  searchResults.textContent = "Cargando...";
  try {
    const resp = await fetch(`${API_BASE}/api/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!resp.ok) throw new Error(`Error ${resp.status}`);
    const data = await resp.json();
    searchResults.innerHTML = "";
    (data.results || []).forEach((r) => {
      const item = document.createElement("div");
      item.className = "list-item";
      const meta = document.createElement("div");
      meta.className = "list-meta";
      const score = r.score ? `score ${r.score.toFixed(3)}` : "";
      meta.textContent = `${formatDate(r.created_at)} ${score}`;
      item.textContent = `${r.filename || r.path || ""}`;
      if (r.chunk) {
        const chunk = document.createElement("div");
        chunk.className = "list-meta";
        chunk.textContent = r.chunk.slice(0, 120);
        item.appendChild(chunk);
      }
      item.appendChild(meta);
      searchResults.appendChild(item);
    });
    if (!searchResults.childElementCount) searchResults.textContent = "Sin resultados";
  } catch (err) {
    console.error(err);
    searchResults.textContent = "No se pudo buscar";
  } finally {
    searchStatus.textContent = "Listo";
  }
}

chatForm.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const text = messageInput.value.trim();
  if (!text) return;
  addMessage("user", text);
  chatStatus.textContent = "Consultando...";
  messageInput.value = "";
  try {
    const resp = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    if (!resp.ok) throw new Error(`Error ${resp.status}`);
    const data = await resp.json();
    addMessage("bot", data.message || "(sin respuesta)");
    loadLogs(true);
  } catch (err) {
    console.error(err);
    addMessage("bot", "Hubo un error al consultar el agente.");
  } finally {
    chatStatus.textContent = "Listo";
  }
});

searchForm.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const text = searchText.value.trim();
  if (!text) return;
  runSearch(text);
});

uploadForm.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  if (!fileInput.files.length) return;
  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  uploadStatus.textContent = "Subiendo...";
  uploadResult.textContent = "";
  try {
    const resp = await fetch(`${API_BASE}/api/upload`, { method: "POST", body: formData });
    if (!resp.ok) throw new Error(`Error ${resp.status}`);
    const data = await resp.json();
    uploadResult.textContent = `Subido: ${data.filename} (id ${data.id})`;
    loadUploads(true);
  } catch (err) {
    console.error(err);
    uploadResult.textContent = "No se pudo subir el archivo.";
  } finally {
    uploadStatus.textContent = "Pendiente";
    uploadForm.reset();
  }
});

refreshUploadsBtn.addEventListener("click", () => loadUploads(true));
moreUploadsBtn.addEventListener("click", () => loadUploads(false));
refreshLogsBtn.addEventListener("click", () => loadLogs(true));
moreLogsBtn.addEventListener("click", () => loadLogs(false));

loadUploads(true);
loadLogs(true);
