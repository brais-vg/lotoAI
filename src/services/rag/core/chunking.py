"""Text chunking with semantic awareness."""

import logging
import re
from typing import Any, Dict, List

from ..config import CHUNK_SIZE, CHUNK_OVERLAP, MIN_CHUNK_SIZE

logger = logging.getLogger("rag-server.chunking")


def chunk_text(text: str) -> List[Dict[str, Any]]:
    """
    Split text into semantic chunks with overlap and metadata.
    
    Prioritizes paragraph boundaries, then sentences.
    
    Returns:
        List of dicts with 'text', 'chunk_index', 'total_chunks', 'type' keys.
    """
    if not text or len(text.strip()) < MIN_CHUNK_SIZE:
        return []
    
    # Try paragraph-based chunking first
    paragraphs = _split_by_paragraphs(text)
    
    if paragraphs:
        chunks = _create_chunks_from_segments(paragraphs, "paragraph")
    else:
        # Fallback to sentence-based
        sentences = _split_by_sentences(text)
        chunks = _create_chunks_from_segments(sentences, "sentence")
    
    # Add metadata
    total = len(chunks)
    return [
        {
            "text": chunk["text"],
            "chunk_index": i,
            "total_chunks": total,
            "type": chunk["type"],
        }
        for i, chunk in enumerate(chunks)
    ]


def _split_by_paragraphs(text: str) -> List[str]:
    """Split text by double newlines (paragraphs)."""
    paragraphs = re.split(r'\n\s*\n', text)
    return [p.strip() for p in paragraphs if p.strip()]


def _split_by_sentences(text: str) -> List[str]:
    """Split text by sentence boundaries."""
    sentence_pattern = r'(?<=[.!?])\s+'
    sentences = re.split(sentence_pattern, text)
    return [s.strip() for s in sentences if s.strip()]


def _create_chunks_from_segments(
    segments: List[str], 
    segment_type: str
) -> List[Dict[str, Any]]:
    """
    Combine segments into chunks respecting size limits.
    
    Uses greedy algorithm: accumulate segments until chunk_size is reached,
    then start new chunk with overlap from previous.
    """
    chunks = []
    current_chunk = []
    current_length = 0
    
    for segment in segments:
        segment_len = len(segment)
        
        # If single segment exceeds chunk size, split it
        if segment_len > CHUNK_SIZE:
            # Flush current chunk first
            if current_chunk:
                chunks.append({
                    "text": " ".join(current_chunk),
                    "type": segment_type
                })
                current_chunk = []
                current_length = 0
            
            # Split large segment into smaller parts
            for part in _split_large_segment(segment):
                chunks.append({"text": part, "type": "long_segment"})
            continue
        
        # Check if adding segment exceeds limit
        if current_length + segment_len + 1 > CHUNK_SIZE and current_chunk:
            # Create chunk from accumulated segments
            chunks.append({
                "text": " ".join(current_chunk),
                "type": segment_type
            })
            
            # Start new chunk with overlap
            overlap_start = max(0, len(current_chunk) - 2)
            current_chunk = current_chunk[overlap_start:]
            current_length = sum(len(s) for s in current_chunk) + len(current_chunk)
        
        current_chunk.append(segment)
        current_length += segment_len + 1
    
    # Don't forget the last chunk
    if current_chunk:
        chunks.append({
            "text": " ".join(current_chunk),
            "type": segment_type
        })
    
    return chunks


def _split_large_segment(segment: str) -> List[str]:
    """Split a segment that's too large into smaller parts."""
    parts = []
    words = segment.split()
    current_part = []
    current_length = 0
    
    for word in words:
        word_len = len(word)
        if current_length + word_len + 1 > CHUNK_SIZE and current_part:
            parts.append(" ".join(current_part))
            # Keep some overlap
            overlap_words = max(1, len(current_part) // 4)
            current_part = current_part[-overlap_words:]
            current_length = sum(len(w) for w in current_part) + len(current_part)
        
        current_part.append(word)
        current_length += word_len + 1
    
    if current_part:
        parts.append(" ".join(current_part))
    
    return parts
