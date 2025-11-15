-- Esquema inicial para lotoAI
-- Tabla de uploads registrada por RAG
CREATE TABLE IF NOT EXISTS uploads (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    path TEXT NOT NULL,
    size_bytes BIGINT NOT NULL,
    content_type TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Log de chats básicos (puede ampliarse con usuario/sesión)
CREATE TABLE IF NOT EXISTS chat_logs (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    provider TEXT DEFAULT 'stub',
    response TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices mínimos
CREATE INDEX IF NOT EXISTS idx_uploads_created_at ON uploads(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_logs_created_at ON chat_logs(created_at);
