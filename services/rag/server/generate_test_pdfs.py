"""
Synthetic PDF generator for RAG testing.
Creates test PDFs with known content to validate RAG improvements.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from pathlib import Path


def create_synthetic_pdfs(output_dir: str = "./test_pdfs"):
    """Create synthetic test PDFs with diverse content."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # PDF 1: Technical Documentation
    create_technical_doc(output_path / "technical_architecture.pdf")
    
    # PDF 2: Product Features
    create_product_features(output_path / "product_features.pdf")
    
    # PDF 3: User Guide
    create_user_guide(output_path / "user_guide.pdf")
    
    # PDF 4: FAQ Document
    create_faq_document(output_path / "faq_document.pdf")
    
    # PDF 5: Research Paper (multi-page, complex)
    create_research_paper(output_path / "research_paper.pdf")
    
    print(f"✓ Created 5 synthetic test PDFs in {output_dir}/")
    return output_path


def create_technical_doc(filename):
    """Technical architecture document."""
    doc = SimpleDocTemplate(str(filename), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='darkblue',
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("LotoAI System Architecture", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Overview
    story.append(Paragraph("System Overview", styles['Heading2']))
    story.append(Paragraph(
        "LotoAI is a modular AI services platform built with a microservices architecture. "
        "The system consists of three main components: Gateway (FastAPI), Agent Orchestrator, "
        "and RAG Server. Each component communicates via REST APIs and shares data through "
        "PostgreSQL and Qdrant vector database.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.3*inch))
    
    # Architecture
    story.append(Paragraph("Architecture Components", styles['Heading2']))
    story.append(Paragraph(
        "<b>Gateway Component:</b> The Gateway serves as the main entry point for all client "
        "requests. It runs on port 8088 and handles routing to appropriate backend services. "
        "The Gateway implements rate limiting, authentication, and request validation.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph(
        "<b>Agent Orchestrator:</b> This component manages AI interactions using OpenAI's API. "
        "It runs on port 8090 and provides chat functionality with conversation history tracking. "
        "The orchestrator includes a fallback stub mode for development without API keys.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph(
        "<b>RAG Server:</b> The Retrieval-Augmented Generation server handles document upload, "
        "indexing, and semantic search. It uses Qdrant for vector storage and supports both "
        "OpenAI and local Sentence Transformers for embeddings. The server implements advanced "
        "features like reranking, multi-query retrieval, and unlimited chunking.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.3*inch))
    
    # Technical Details
    story.append(Paragraph("Technical Specifications", styles['Heading2']))
    story.append(Paragraph(
        "Database: PostgreSQL 15 stores metadata, user sessions, and upload records. "
        "Vector Database: Qdrant 1.7 manages embedding vectors with HNSW indexing. "
        "Message Queue: NATS handles asynchronous communication between services. "
        "Object Storage: MinIO provides S3-compatible storage for uploaded files.",
        styles['BodyText']
    ))
    
    doc.build(story)


def create_product_features(filename):
    """Product features document."""
    doc = SimpleDocTemplate(str(filename), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], 
                                   fontSize=24, spaceAfter=30, alignment=TA_CENTER)
    story.append(Paragraph("LotoAI Product Features", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Core Features", styles['Heading2']))
    
    # Chat Feature
    story.append(Paragraph("<b>Intelligent Chat:</b>", styles['Heading3']))
    story.append(Paragraph(
        "LotoAI provides advanced conversational AI powered by GPT-4. The chat feature "
        "includes context retention, multi-turn conversations, and integration with "
        "uploaded documents through RAG. Users can ask questions about their documents "
        "and receive accurate, contextual answers.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.2*inch))
    
    # Document Upload
    story.append(Paragraph("<b>Document Upload & Processing:</b>", styles['Heading3']))
    story.append(Paragraph(
        "Support for multiple file formats including PDF, DOCX, HTML, and Markdown. "
        "Automatic text extraction with layout preservation. Smart chunking creates "
        "overlapping segments for better context preservation. Maximum file size: 50MB.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.2*inch))
    
    # Search
    story.append(Paragraph("<b>Semantic Search:</b>", styles['Heading3']))
    story.append(Paragraph(
        "Hybrid search combines vector similarity with keyword matching. Reranking with "
        "cross-encoder models improves result relevance. Multi-query retrieval uses query "
        "expansion for better recall. Supports filtering by date, file type, and metadata.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("Advanced Capabilities", styles['Heading2']))
    story.append(Paragraph(
        "Local Embeddings: Run completely offline with Sentence Transformers. "
        "Privacy-focused deployment without external API dependence. "
        "Multilingual Support: BGE-M3 model supports 100+ languages. "
        "Scalability: Handles thousands of documents with sub-second search times.",
        styles['BodyText']
    ))
    
    doc.build(story)


def create_user_guide(filename):
    """User guide document."""
    doc = SimpleDocTemplate(str(filename), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                   fontSize=24, spaceAfter=30, alignment=TA_CENTER)
    story.append(Paragraph("LotoAI User Guide", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Getting Started", styles['Heading2']))
    story.append(Paragraph(
        "Welcome to LotoAI! This guide will help you get started with uploading documents "
        "and using the chat interface. The system is designed to be intuitive and requires "
        "no technical knowledge to use.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("Uploading Documents", styles['Heading2']))
    story.append(Paragraph(
        "Step 1: Click the 'Upload' button in the top right corner. "
        "Step 2: Select one or more files from your computer (PDF, Word, or text files). "
        "Step 3: Wait for the upload to complete - you'll see a progress indicator. "
        "Step 4: Once uploaded, documents are automatically indexed and searchable.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("Using Chat", styles['Heading2']))
    story.append(Paragraph(
        "The chat interface allows you to ask questions about your uploaded documents. "
        "Simply type your question in natural language and press Enter. The AI will "
        "search your documents and provide relevant answers with source citations. "
        "You can ask follow-up questions to dive deeper into topics.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("Search Tips", styles['Heading2']))
    story.append(Paragraph(
        "Be specific: More detailed questions yield better results. "
        "Use keywords: Include important terms from your documents. "
        "Ask one thing at a time: Break complex questions into smaller parts. "
        "Check sources: Always verify the cited document sections.",
        styles['BodyText']
    ))
    
    doc.build(story)


def create_faq_document(filename):
    """FAQ document."""
    doc = SimpleDocTemplate(str(filename), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                   fontSize=24, spaceAfter=30, alignment=TA_CENTER)
    story.append(Paragraph("Frequently Asked Questions", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    faqs = [
        ("What file formats are supported?", 
         "LotoAI supports PDF, DOCX, DOC, TXT, MD, HTML, and HTM files. The maximum file size is 50MB per file."),
        
        ("How does the search work?",
         "The system uses hybrid search combining vector embeddings and keyword matching. Documents are split into semantic chunks and indexed. When you search, the system finds relevant chunks and optionally reranks them for better accuracy."),
        
        ("Is my data private?",
         "Yes! You can run LotoAI completely locally with no external API calls. Use the local embedding mode (EMBEDDING_PROVIDER=local) for full privacy. Your documents never leave your infrastructure."),
        
        ("How many documents can I upload?",
         "There's no hard limit on document count. The system scales to thousands of documents. Performance depends on your hardware resources."),
        
        ("What is reranking?",
         "Reranking is a two-stage retrieval process. First, we find candidate documents using fast vector search. Then, a more accurate cross-encoder model reorders results by relevance. This improves answer quality significantly."),
        
        ("Can I use this offline?",
         "Yes! Configure EMBEDDING_PROVIDER=local and you can run the entire RAG system without internet access. You'll need to download the embedding models once (about 500MB)."),
        
        ("How do I improve search quality?",
         "Enable reranking (ENABLE_RERANKING=1), use smaller chunk sizes (CHUNK_SIZE_CHARS=600), and ensure documents are well-formatted. For multilingual content, use the BGE-M3 embedding model."),
    ]
    
    for q, a in faqs:
        story.append(Paragraph(f"<b>Q: {q}</b>", styles['Heading3']))
        story.append(Paragraph(a, styles['BodyText']))
        story.append(Spacer(1, 0.2*inch))
    
    doc.build(story)


def create_research_paper(filename):
    """Multi-page research paper."""
    doc = SimpleDocTemplate(str(filename), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                   fontSize=24, spaceAfter=30, alignment=TA_CENTER)
    story.append(Paragraph("Advances in Retrieval-Augmented Generation", title_style))
    story.append(Paragraph("<i>A Comprehensive Study</i>", styles['Normal']))
    story.append(Spacer(1, 0.5*inch))
    
    # Abstract
    story.append(Paragraph("Abstract", styles['Heading2']))
    story.append(Paragraph(
        "Retrieval-Augmented Generation (RAG) has emerged as a powerful paradigm for enhancing "
        "large language models with external knowledge. This paper examines recent advances in "
        "RAG systems, focusing on embedding models, chunking strategies, and reranking techniques. "
        "We present experimental results showing that multi-stage retrieval with cross-encoder "
        "reranking improves accuracy by 15-20% compared to single-stage vector search. "
        "Our findings demonstrate that unlimited chunking with 25% overlap provides optimal "
        "context preservation while maintaining reasonable computational costs.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.3*inch))
    
    # Introduction
    story.append(Paragraph("1. Introduction", styles['Heading2']))
    story.append(Paragraph(
        "Large Language Models (LLMs) have revolutionized natural language processing, but they "
        "suffer from knowledge cutoff dates and inability to access proprietary or recent information. "
        "RAG addresses these limitations by augmenting LLM prompts with relevant documents retrieved "
        "from external knowledge bases. The effectiveness of RAG systems depends critically on three "
        "components: the embedding model used for vectorization, the chunking strategy for document "
        "segmentation, and the retrieval mechanism for finding relevant content.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(PageBreak())
    
    # Methods
    story.append(Paragraph("2. Methodology", styles['Heading2']))
    story.append(Paragraph("2.1 Embedding Models", styles['Heading3']))
    story.append(Paragraph(
        "We evaluated three embedding approaches: OpenAI's text-embedding-3-small (1536 dimensions), "
        "all-MiniLM-L6-v2 (384 dimensions), and BAAI BGE-M3 (1024 dimensions). Each model was tested "
        "on a corpus of 2000 technical documents with known question-answer pairs. Performance metrics "
        "included Mean Reciprocal Rank (MRR), Precision@10, and Recall@10.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("2.2 Chunking Strategies", styles['Heading3']))
    story.append(Paragraph(
        "Document chunking was performed with three strategies: fixed-size (800 characters), "
        "semantic paragraph-based, and hybrid paragraph-sentence splitting. We tested chunk limits "
        "of 4, 50, and unlimited (with 500 safety limit). Overlap ratios of 0%, 25%, and 50% were "
        "compared for context preservation.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("2.3 Reranking", styles['Heading3']))
    story.append(Paragraph(
        "Two-stage retrieval was implemented using fast vector search (k=50) followed by cross-encoder "
        "reranking (ms-marco-MiniLM-L-6-v2) to select top-10 results. We compared this against "
        "single-stage retrieval and reciprocal rank fusion (RRF) with multiple query variants.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(PageBreak())
    
    # Results
    story.append(Paragraph("3. Results", styles['Heading2']))
    story.append(Paragraph(
        "Experimental results show that BGE-M3 embeddings achieved MRR of 0.863, significantly "
        "outperforming all-MiniLM-L6-v2 (MRR: 0.710) while OpenAI embeddings reached 0.945. "
        "Unlimited chunking with 25% overlap improved recall by 23% compared to 4-chunk limit. "
        "Reranking provided consistent 15-18% accuracy improvements across all embedding models. "
        "The combination of BGE-M3, unlimited chunking, and reranking achieved 89.2% accuracy on "
        "our test set, approaching proprietary API performance while remaining fully local.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.3*inch))
    
    # Conclusion
    story.append(Paragraph("4. Conclusion", styles['Heading2']))
    story.append(Paragraph(
        "This study demonstrates that high-quality RAG systems can be built using open-source "
        "components. The key findings are: (1) Unlimited chunking with overlap prevents information "
        "loss, (2) Reranking significantly improves relevance, (3) BGE-M3 provides excellent quality "
        "for multilingual scenarios. Future work should explore dynamic chunking based on document "
        "structure and hybrid retrieval combining dense and sparse representations.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.3*inch))
    
    # References
    story.append(Paragraph("References", styles['Heading2']))
    refs = [
        "Lewis, P., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS.",
        "Karpukhin, V., et al. (2020). Dense Passage Retrieval for Open-Domain Question Answering. EMNLP.",
        "Xiao, S., et al. (2023). C-Pack: Packaged Resources for General Chinese Embeddings. arXiv.",
    ]
    for ref in refs:
        story.append(Paragraph(f"• {ref}", styles['BodyText']))
    
    doc.build(story)


if __name__ == "__main__":
    output_dir = create_synthetic_pdfs()
    print(f"\n✓ Test PDFs created successfully in: {output_dir}")
    print("\nTo test RAG:")
    print("1. Upload all PDFs to the RAG server")
    print("2. Use test_queries.json for validation")
    print("3. Compare results before/after reranking")
