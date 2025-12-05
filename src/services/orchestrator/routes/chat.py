"""Chat routes."""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..core.chat_history import get_history_manager, ChatMessage
from ..core.rag_client import fetch_rag_context, format_context, get_source_citations
from ..core.llm_client import generate_response
from ..core.prompts import build_system_prompt

logger = logging.getLogger("orchestrator.routes.chat")
router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    citations: Optional[str] = None
    history: List[dict]


class HistoryResponse(BaseModel):
    messages: List[dict]


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process chat message with RAG context.
    """
    try:
        history_manager = get_history_manager()
        session_id = request.session_id
        
        # Add user message to history
        history_manager.add_message(session_id, "user", request.message)
        
        # 1. Fetch context from RAG
        rag_results = await fetch_rag_context(request.message)
        context_str = format_context(rag_results)
        
        # 2. Build system prompt
        system_prompt = build_system_prompt(context_str)
        
        # 3. Get chat history for context
        history_context = history_manager.get_context_messages(session_id)
        
        # 4. Generate response
        llm_response = generate_response(
            system_prompt=system_prompt,
            user_message=request.message,
            history=history_context
        )
        
        # 5. Add bot response to history
        history_manager.add_message(session_id, "bot", llm_response)
        
        # 6. Prepare response
        citations = get_source_citations(rag_results)
        full_history = [m.to_dict() for m in history_manager.get_history(session_id)]
        
        return ChatResponse(
            response=llm_response,
            citations=citations,
            history=full_history
        )
        
    except Exception as exc:
        logger.error(f"Chat processing failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/chat/history", response_model=HistoryResponse)
async def get_history(
    session_id: str = "default",
    limit: int = 50,
    offset: int = 0
):
    """Get chat history."""
    manager = get_history_manager()
    messages = manager.get_history(session_id, limit, offset)
    return HistoryResponse(messages=[m.to_dict() for m in messages])


@router.delete("/chat/history")
async def clear_history(session_id: str = "default"):
    """Clear chat history."""
    manager = get_history_manager()
    manager.clear_history(session_id)
    return {"status": "cleared"}
