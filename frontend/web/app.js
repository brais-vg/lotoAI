const API_BASE = window.APP_CONFIG?.API_BASE || window.API_BASE || "http://localhost:8088";

const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message");
const messages = document.getElementById("messages");
const chatStatus = document.getElementById("chat-status");
const uploadForm = document.getElementById("upload-form");
const uploadStatus = document.getElementById("upload-status");
const uploadResult = document.getElementById("upload-result");
const fileInput = document.getElementById("file");

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `bubble ${role}`;
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
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
  } catch (err) {
    console.error(err);
    uploadResult.textContent = "No se pudo subir el archivo.";
  } finally {
    uploadStatus.textContent = "Pendiente";
    uploadForm.reset();
  }
});
