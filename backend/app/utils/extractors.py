from PyPDF2 import PdfReader
from docx import Document
from PIL import Image
import pytesseract

def extract_text_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_text_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_txt(file):
    return file.read().decode("utf-8", errors="replace")

def extract_text_image(file):
    image = Image.open(file)
    return pytesseract.image_to_string(image, lang="eng+fra")

