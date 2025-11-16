import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8088";
const PAGE_SIZE = 5;

async function fetchJson(url, options = {}) {
  const resp = await fetch(url, options);
  if (!resp.ok) throw new Error(`Error ${resp.status}`);
  return resp.json();
}

function Section({ title, children, actions }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>{title}</h2>
        <div className="actions">{actions}</div>
      </div>
      {children}
    </section>
  );
}

export default function App() {
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  const [chatStatus, setChatStatus] = useState("Listo");

  const [searchText, setSearchText] = useState("");
  const [searchStatus, setSearchStatus] = useState("Listo");
  const [searchResults, setSearchResults] = useState([]);

  const [uploads, setUploads] = useState([]);
  const [uploadsOffset, setUploadsOffset] = useState(0);
  const [uploadsLoading, setUploadsLoading] = useState(false);

  const [logs, setLogs] = useState([]);
  const [logsOffset, setLogsOffset] = useState(0);
  const [logsLoading, setLogsLoading] = useState(false);

  const [uploadStatus, setUploadStatus] = useState("Pendiente");
  const [uploadResult, setUploadResult] = useState("");

  const loadUploads = async (reset = false) => {
    try {
      setUploadsLoading(true);
      const offset = reset ? 0 : uploadsOffset;
      const data = await fetchJson(`${API_BASE}/api/uploads?limit=${PAGE_SIZE}&offset=${offset}`);
      const items = data.items || [];
      setUploads(reset ? items : [...uploads, ...items]);
      setUploadsOffset(offset + items.length);
    } catch (err) {
      console.error(err);
    } finally {
      setUploadsLoading(false);
    }
  };

  const loadLogs = async (reset = false) => {
    try {
      setLogsLoading(true);
      const offset = reset ? 0 : logsOffset;
      const data = await fetchJson(`${API_BASE}/api/chat/logs?limit=${PAGE_SIZE}&offset=${offset}`);
      const items = data.items || [];
      setLogs(reset ? items : [...logs, ...items]);
      setLogsOffset(offset + items.length);
    } catch (err) {
      console.error(err);
    } finally {
      setLogsLoading(false);
    }
  };

  useEffect(() => {
    loadUploads(true);
    loadLogs(true);
  }, []);

  const handleChat = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    const userMsg = { role: "user", text: chatInput };
    setChatMessages((msgs) => [...msgs, userMsg]);
    setChatInput("");
    setChatStatus("Consultando...");
    try {
      const data = await fetchJson(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg.text }),
      });
      setChatMessages((msgs) => [...msgs, { role: "bot", text: data.message || "(sin respuesta)" }]);
      loadLogs(true);
    } catch (err) {
      console.error(err);
      setChatMessages((msgs) => [...msgs, { role: "bot", text: "Error en chat" }]);
    } finally {
      setChatStatus("Listo");
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchText.trim()) return;
    setSearchStatus("Buscando...");
    setSearchResults([]);
    try {
      const data = await fetchJson(`${API_BASE}/api/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: searchText }),
      });
      setSearchResults(data.results || []);
    } catch (err) {
      console.error(err);
      setSearchResults([]);
    } finally {
      setSearchStatus("Listo");
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    const file = e.target.file.files[0];
    if (!file) return;
    setUploadStatus("Subiendo...");
    setUploadResult("");
    const form = new FormData();
    form.append("file", file);
    try {
      const resp = await fetch(`${API_BASE}/api/upload`, { method: "POST", body: form });
      if (!resp.ok) throw new Error(`Error ${resp.status}`);
      const data = await resp.json();
      setUploadResult(`Subido: ${data.filename} (id ${data.id})`);
      loadUploads(true);
    } catch (err) {
      console.error(err);
      setUploadResult("No se pudo subir el archivo.");
    } finally {
      setUploadStatus("Pendiente");
      e.target.reset();
    }
  };

  const renderList = (items, loading) => {
    if (loading && !items.length) return <div className="list">Cargando...</div>;
    if (!items.length) return <div className="list">Sin datos</div>;
    return (
      <div className="list">
        {items.map((item, idx) => (
          <div key={idx} className="list-item">
            {item.filename || item.message || item.chunk || item.path || JSON.stringify(item)}
            <div className="list-meta">
              {item.created_at ? new Date(item.created_at).toLocaleString() : ""}
              {item.content_type ? ` | ${item.content_type}` : ""}
              {item.score ? ` | score ${item.score.toFixed(3)}` : ""}
              {item.size_bytes ? ` | ${Math.round(item.size_bytes / 1024)} KB` : ""}
            </div>
            {item.chunk ? <div className="list-meta">{item.chunk.slice(0, 120)}</div> : null}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="page">
      <header>
        <h1>lotoAI (Vite)</h1>
        <p>Cliente React conectado al gateway.</p>
      </header>

      <main>
        <Section title="Chat" actions={<span className="status">{chatStatus}</span>}>
          <div className="messages">
            {chatMessages.map((m, i) => (
              <div key={i} className={`bubble ${m.role}`}>{m.text}</div>
            ))}
          </div>
          <form className="form" onSubmit={handleChat}>
            <textarea
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              rows={3}
              placeholder="Escribe tu mensaje"
            />
            <button type="submit">Enviar</button>
          </form>
        </Section>

        <Section title="Busqueda" actions={<span className="status">{searchStatus}</span>}>
          <form className="form" onSubmit={handleSearch}>
            <input
              type="text"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              placeholder="Texto a buscar (contenido o nombre)"
            />
            <button type="submit">Buscar</button>
          </form>
          {renderList(searchResults, false)}
        </Section>

        <Section title="Subir archivo" actions={<span className="status">{uploadStatus}</span>}>
          <form className="form" onSubmit={handleUpload} encType="multipart/form-data">
            <input type="file" name="file" />
            <button type="submit">Subir</button>
          </form>
          <div className="upload-result">{uploadResult}</div>
        </Section>

        <Section
          title="Uploads recientes"
          actions={
            <div className="actions-inline">
              <button type="button" onClick={() => loadUploads(true)} disabled={uploadsLoading}>
                Refrescar
              </button>
              <button type="button" onClick={() => loadUploads(false)} disabled={uploadsLoading}>
                Más
              </button>
            </div>
          }
        >
          {renderList(uploads, uploadsLoading)}
        </Section>

        <Section
          title="Logs de chat"
          actions={
            <div className="actions-inline">
              <button type="button" onClick={() => loadLogs(true)} disabled={logsLoading}>
                Refrescar
              </button>
              <button type="button" onClick={() => loadLogs(false)} disabled={logsLoading}>
                Más
              </button>
            </div>
          }
        >
          {renderList(logs, logsLoading)}
        </Section>
      </main>
    </div>
  );
}
