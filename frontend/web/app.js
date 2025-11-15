const API_BASE = window.APP_CONFIG?.API_BASE || window.API_BASE || "http://localhost:8088";

const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message");
const messages = document.getElementById("messages");
const chatStatus = document.getElementById("chat-status");
const uploadForm = document.getElementById("upload-form");
const uploadStatus = document.getElementById("upload-status");
const uploadResult = document.getElementById("upload-result");
const fileInput = document.getElementById("file");
const uploadsList = document.getElementById("uploads-list");
const refreshUploadsBtn = document.getElementById("refresh-uploads");
const logsList = document.getElementById("logs-list");
const refreshLogsBtn = document.getElementById("refresh-logs");

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `bubble ${role}`;
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

async function loadUploads() {
  uploadsList.textContent = "Cargando...";
  try {
    const resp = await fetch(`${API_BASE}/api/uploads`);
    if (!resp.ok) throw new Error("No se pudo obtener uploads");
    const data = await resp.json();
    uploadsList.innerHTML = "";
    (data.items || []).forEach((u) => {
      const item = document.createElement("div");
      item.className = "list-item";
      item.textContent = `${u.id} · ${u.filename} (${Math.round((u.size_bytes || 0)/1024)} KB)`;
      uploadsList.appendChild(item);
    });
    if (!uploadsList.childElementCount) uploadsList.textContent = "Sin uploads";
  } catch (err) {
    console.error(err);
    uploadsList.textContent = "Error al cargar uploads";
  }
}

async function loadLogs() {
  logsList.textContent = "Cargando...";
  try {
    const resp = await fetch(`${API_BASE}/api/chat/logs`);
    if (!resp.ok) throw new Error("No se pudo obtener logs");
    const data = await resp.json();
    logsList.innerHTML = "";
    (data.items || []).forEach((l) => {
      const item = document.createElement("div");
      item.className = "list-item";
      item.textContent = `${l.provider || ""} · ${l.message?.slice(0,80) || ""}`;
      logsList.appendChild(item);
    });
    if (!logsList.childElementCount) logsList.textContent = "Sin logs";
  } catch (err) {
    console.error(err);
    logsList.textContent = "Error al cargar logs";
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
    loadLogs();
  } catch (err) {
    console.error(err);
    addMessage("bot", "Hubo un error al consultar el agente.");
  } finally {
    chatStatus.textContent = "Listo";
  }
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
    loadUploads();
  } catch (err) {
    console.error(err);
    uploadResult.textContent = "No se pudo subir el archivo.";
  } finally {
    uploadStatus.textContent = "Pendiente";
    uploadForm.reset();
  }
});

refreshUploadsBtn.addEventListener("click", loadUploads);
refreshLogsBtn.addEventListener("click", loadLogs);

// carga inicial
loadUploads();
loadLogs();
