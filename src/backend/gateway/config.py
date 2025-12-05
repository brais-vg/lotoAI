"""Gateway configuration."""

import os

ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://agent-orchestrator:8090")
RAG_SERVER_URL = os.getenv("RAG_SERVER_URL", "http://rag-server:8000")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
LOG_PATH = os.getenv("LOG_PATH", "./logs/app.log")
