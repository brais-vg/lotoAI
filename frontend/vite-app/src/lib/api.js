const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8088";

async function fetchJson(url, options = {}) {
    const resp = await fetch(url, options);
    if (!resp.ok) throw new Error(`Error ${resp.status}`);
    return resp.json();
}

export const api = {
    chat: {
        sendMessage: (message) =>
            fetchJson(`${API_BASE}/api/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message }),
            }),
        getLogs: (limit = 20, offset = 0) =>
            fetchJson(`${API_BASE}/api/chat/logs?limit=${limit}&offset=${offset}`),
    },
    upload: {
        uploadFile: async (file) => {
            const form = new FormData();
            form.append("file", file);
            const resp = await fetch(`${API_BASE}/api/upload`, { method: "POST", body: form });
            if (!resp.ok) throw new Error(`Error ${resp.status}`);
            return resp.json();
        },
        list: (limit = 20, offset = 0) =>
            fetchJson(`${API_BASE}/api/uploads?limit=${limit}&offset=${offset}`),
    },
    search: {
        search: (text) =>
            fetchJson(`${API_BASE}/api/search`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text }),
            }),
    },
};
