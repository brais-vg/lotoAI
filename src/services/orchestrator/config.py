"""Orchestrator configuration module."""

import os

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "")

# RAG Server
RAG_SERVER_URL = os.getenv("RAG_SERVER_URL", "http://rag-server:8000")

# Chat configuration
CHAT_TEMPERATURE = float(os.getenv("CHAT_TEMPERATURE", "0.7"))
CHAT_MAX_TOKENS = int(os.getenv("CHAT_MAX_TOKENS", "1500"))
CHAT_HISTORY_LENGTH = int(os.getenv("CHAT_HISTORY_LENGTH", "5"))

# RAG configuration
RAG_MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", "0.01"))
RAG_CONTEXT_CHARS = int(os.getenv("RAG_CONTEXT_CHARS", "1000"))

# Logging
MAX_LOG_LENGTH = 500
