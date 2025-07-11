from docx import Document as DocxDocument
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import tempfile

def generate_docx(text: str) -> str:
    doc = DocxDocument()
    for para in text.split("\n"):
        doc.add_paragraph(para)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(tmp.name)
    return tmp.name

def generate_pdf(text: str) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(tmp.name, pagesize=A4)
    width, height = A4
    y = height - 40
    for line in text.split("\n"):
        c.drawString(40, y, line)
        y -= 16
        if y < 40:
            c.showPage()
            y = height - 40
    c.save()
    return tmp.name

