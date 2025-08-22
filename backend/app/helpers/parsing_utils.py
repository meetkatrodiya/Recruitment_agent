from PyPDF2 import PdfReader
from docx import Document
from fastapi import UploadFile, HTTPException
from io import BytesIO

def extract_text_from_pdf(file_path: BytesIO) -> str:
    reader = PdfReader(file_path)
    pages_text = []
    for page in reader.pages:
        extracted = page.extract_text() or ""
        pages_text.append(extracted)
    return "\n".join(pages_text).strip()

def extract_text_from_docx(file_path: BytesIO) -> str: 
    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs]
    return "\n".join(paragraphs).strip()

def extract_text_from_upload(file: UploadFile) -> str:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    