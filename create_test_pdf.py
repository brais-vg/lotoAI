from reportlab.pdfgen import canvas

def create_pdf(filename):
    c = canvas.Canvas(filename)
    c.drawString(100, 750, "Documento de Prueba LotoAI")
    c.drawString(100, 700, "Este es un documento PDF de prueba creado para verificar el sistema RAG.")
    c.drawString(100, 650, "Contenido importante:")
    c.drawString(100, 600, "- El sistema debe ser capaz de leer este texto.")
    c.drawString(100, 550, "- La palabra clave es: ORNITORRINCO.")
    c.drawString(100, 500, "- Si el sistema encuentra esta palabra, la prueba es exitosa.")
    c.save()

if __name__ == "__main__":
    create_pdf("test_rag_doc.pdf")
    print("PDF creado exitosamente: test_rag_doc.pdf")
