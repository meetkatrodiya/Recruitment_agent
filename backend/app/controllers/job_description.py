from fastapi import APIRouter, status
from fastapi import UploadFile, File
from typing import Any
import logging

from app.models.jd import ManualJDInput, JDGenerationRequest, JobDescriptionParsed
from app.models.common import ApiResponse
from app.services.file_extractor import extract_text_from_upload
from app.services.jd_ai import generate_job_description
from app.services.resume_parser_ai import JDParserChain
from app.core.config import get_openai_api_key
from pydantic import BaseModel, Field
from app.helpers.common_utils import fail


logger = logging.getLogger(__name__)

# Create router
router = APIRouter()



class JDTextInput(BaseModel):
    text: str = Field(min_length=1)


@router.post("/jd/parse", status_code=status.HTTP_200_OK, response_model=ApiResponse[JobDescriptionParsed])
async def parse_jd_text(payload: JDTextInput) -> Any:
    if not payload.text or not payload.text.strip():
        return fail("Text is required.", status_code=400)
    if len(payload.text) > 50000:
        return fail("Text too long. Please provide up to 50,000 characters.", status_code=413)

    try:
        api_key = get_openai_api_key()
        chain = JDParserChain(api_key)
        parsed = chain.parse_job_description(payload.text)
        return ApiResponse(success=True, data=parsed)
    except Exception as exc:  # noqa: BLE001
        logger.exception("JD parse failed: %s", exc)
        return fail(f"Failed to parse JD: {exc}", status_code=502)


@router.post("/jd/upload", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[dict])
async def upload_jd_file(file: UploadFile = File(...)) -> Any:
    allowed_ext = {".pdf", ".docx"}
    filename = file.filename or ""
    parts = filename.lower().rsplit(".", 1)
    ext = f".{parts[1]}" if len(parts) == 2 else ""
    if ext not in allowed_ext:
        return fail("Unsupported file type. Only PDF and DOCX are allowed.", status_code=415)

    try:
        text = await extract_text_from_upload(file)
    except Exception as exc:  # noqa: BLE001
        logger.exception("File extract failed for %s: %s", filename, exc)
        return fail(f"Failed to extract text: {exc}", status_code=422)

    if not text or not text.strip():
        return fail("No readable text found in the uploaded file.", status_code=422)

    return ApiResponse(success=True, data={
        "source": "file",
        "filename": filename,
        "text": text,
        "length": len(text),
    })


@router.post("/jd/manual", status_code=status.HTTP_200_OK, response_model=ApiResponse[dict])
async def manual_jd_input(payload: ManualJDInput) -> Any:
    text = payload.text.strip()
    if not text:
        return fail("Text is required.", status_code=400)
    return ApiResponse(success=True, data={
        "source": "manual",
        "text": text,
        "length": len(text),
    })


@router.post("/jd/generate", status_code=status.HTTP_200_OK, response_model=ApiResponse[dict])
async def generate_jd(payload: JDGenerationRequest) -> Any:
    if not payload.job_title or not payload.job_title.strip():
        return fail("Job title is required to generate a JD.", status_code=400)
    if payload.years_of_experience is not None and payload.years_of_experience < 0:
        return fail("Years of experience cannot be negative.", status_code=400)

    try:
        jd_text = await generate_job_description(payload)
        if not jd_text or not jd_text.strip():
            return fail("Failed to generate a valid JD.", status_code=502)
    except Exception as exc:  # noqa: BLE001
        logger.exception("JD generation failed: %s", exc)
        return fail(f"Failed to generate JD: {exc}", status_code=502)

    return ApiResponse(success=True, data={
        "source": "generated",
        "inputs": {
            "job_title": payload.job_title,
            "years_of_experience": payload.years_of_experience,
            "must_have_skills": payload.skills_list,
            "company_name": payload.company_name,
            "employment_type": payload.employment_type,
            "industry": payload.industry,
            "location": payload.location,
            "language": payload.language,
        },
        "job_description": jd_text,
        "length": len(jd_text),
    })