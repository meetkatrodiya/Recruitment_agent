from typing import List
from io import BytesIO
import asyncio
from fastapi import UploadFile, HTTPException
from PyPDF2 import PdfReader
from docx import Document
from app.helpers.parsing_utils import extract_text_from_pdf, extract_text_from_docx

async def extract_text_from_upload(file: UploadFile) -> str:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    filename_lower = file.filename.lower()
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        if filename_lower.endswith(".pdf"):
            # Offload blocking PDF parsing to a thread to avoid blocking the event loop
            text = await asyncio.to_thread(extract_text_from_pdf, BytesIO(data))
        elif filename_lower.endswith(".docx"):
            # Offload blocking DOCX parsing to a thread
            text = await asyncio.to_thread(extract_text_from_docx, BytesIO(data))
        elif filename_lower.endswith(".doc"):
            raise HTTPException(
                status_code=415,
                detail=".doc is not supported. Please upload a PDF or DOCX file.",
            )
        else:
            raise HTTPException(
                status_code=415,
                detail="Unsupported file type. Please upload a PDF or DOCX file.",
            )
    except HTTPException:
        raise
    except Exception as exc:    
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {exc}")

    if not text:
        raise HTTPException(status_code=400, detail="No extractable text found in the file")

    return text 