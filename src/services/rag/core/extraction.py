"""Text extraction from various file formats."""

import io
import logging
from typing import Optional

logger = logging.getLogger("rag-server.extraction")


def extract_text_from_bytes(data: bytes, content_type: str, filename: str) -> str:
    """
    Extract text from different file formats.
    Supports: PDF, DOCX, MD, HTML, TXT
    
    Returns:
        Extracted and cleaned text, empty string on failure.
    """
    ct = (content_type or "").lower()
    name = filename.lower()
    text = ""
    
    # PDF
    if "pdf" in ct or name.endswith(".pdf"):
        text = _extract_pdf(data)
    
    # DOCX
    elif "word" in ct or name.endswith((".docx", ".doc")):
        text = _extract_docx(data)
    
    # HTML
    elif "html" in ct or name.endswith((".html", ".htm")):
        text = _extract_html(data)
    
    # Markdown
    elif name.endswith(".md"):
        text = _extract_markdown(data)
    
    # Plain text (fallback)
    else:
        text = _extract_plaintext(data)
    
    return _clean_text(text)


def _extract_pdf(data: bytes) -> str:
    """Extract text from PDF using pypdf."""
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(data))
        pages = [p.extract_text() or "" for p in reader.pages]
        return "\n".join(pages)
    except Exception as exc:
        logger.warning("Failed to extract PDF text: %s", exc)
        return ""


def _extract_docx(data: bytes) -> str:
    """Extract text from DOCX using python-docx."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(data))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    except Exception as exc:
        logger.warning("Failed to extract DOCX text: %s", exc)
        return ""


def _extract_html(data: bytes) -> str:
    """Extract text from HTML using BeautifulSoup."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(data, "lxml")
        for script in soup(["script", "style"]):
            script.decompose()
        return soup.get_text(separator="\n", strip=True)
    except Exception as exc:
        logger.warning("Failed to extract HTML text: %s", exc)
        return ""


def _extract_markdown(data: bytes) -> str:
    """Extract text from Markdown."""
    try:
        import markdown
        from bs4 import BeautifulSoup
        html = markdown.markdown(data.decode("utf-8", errors="ignore"))
        soup = BeautifulSoup(html, "lxml")
        return soup.get_text(separator="\n", strip=True)
    except Exception as exc:
        logger.warning("Failed to extract Markdown text: %s", exc)
        return ""


def _extract_plaintext(data: bytes) -> str:
    """Extract text from plain text file."""
    try:
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _clean_text(text: str) -> str:
    """Clean extracted text: remove empty lines and control characters."""
    if not text:
        return ""
    
    # Remove multiple empty lines
    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if line]
    text = "\n".join(lines)
    
    # Remove control characters except newlines
    text = "".join(char for char in text if char.isprintable() or char == "\n")
    
    return text
