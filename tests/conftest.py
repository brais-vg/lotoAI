"""Global pytest fixtures for lotoAI tests."""

import os
import pytest
from pathlib import Path
from typing import Generator

# Set test environment
os.environ.setdefault("TESTING", "1")
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/lotoai_test")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")


@pytest.fixture(scope="session")
def test_fixtures_dir() -> Path:
    """Path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def sample_documents_dir(test_fixtures_dir: Path) -> Path:
    """Path to sample documents for testing."""
    return test_fixtures_dir / "documents"


@pytest.fixture
def sample_pdf_path(sample_documents_dir: Path) -> Path:
    """Path to sample PDF file."""
    pdf_path = sample_documents_dir / "sample.pdf"
    if not pdf_path.exists():
        # Create a simple test PDF if it doesn't exist
        _create_test_pdf(pdf_path)
    return pdf_path


@pytest.fixture
def sample_text_content() -> str:
    """Sample text content for testing."""
    return """
    Este es un documento de prueba para el sistema lotoAI.
    
    El sistema RAG permite buscar información en documentos subidos.
    La palabra clave para verificar es: ORNITORRINCO.
    
    Este párrafo contiene información adicional sobre el funcionamiento
    del sistema de búsqueda vectorial y embeddings.
    """


@pytest.fixture
def mock_rag_results() -> list:
    """Mock RAG search results."""
    return [
        {
            "id": 1,
            "filename": "test_doc.pdf",
            "chunk": "Este es el contenido del documento de prueba.",
            "chunk_index": 0,
            "score": 0.85,
            "content_type": "application/pdf",
        },
        {
            "id": 2,
            "filename": "otro_doc.pdf",
            "chunk": "Otro fragmento de texto relevante.",
            "chunk_index": 0,
            "score": 0.72,
            "content_type": "application/pdf",
        },
    ]


def _create_test_pdf(path: Path) -> None:
    """Create a simple test PDF file."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        
        path.parent.mkdir(parents=True, exist_ok=True)
        c = canvas.Canvas(str(path), pagesize=letter)
        c.drawString(100, 750, "Documento de Prueba LotoAI")
        c.drawString(100, 700, "Palabra clave: ORNITORRINCO")
        c.save()
    except ImportError:
        # If reportlab not available, create empty file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"%PDF-1.4 test")
