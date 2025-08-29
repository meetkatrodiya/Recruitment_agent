from typing import Any, List
from fastapi import APIRouter, UploadFile, File, status, Form
import asyncio

from app.services.file_extractor import extract_text_from_upload
from app.models.resume import ScoringResult, ResumeScoringResult
from app.models.jd import JobDescriptionParsed
from app.models.common import ApiResponse

# Advanced chains
from app.services.resume_parser_ai import ResumeParserChain, SimpleScoringChain
from app.core.config import get_openai_api_key, get_max_parallel_tasks
from app.helpers.common_utils import fail

router = APIRouter()



@router.post("/resumes/parse", status_code=status.HTTP_200_OK, response_model=ApiResponse[List[ResumeScoringResult]])
async def parse_and_score_resumes(
    parsed_jd_json: str = Form(..., description="Parsed job description JSON (stringified)"),
    files: List[UploadFile] = File(..., description="Up to 10 resumes (PDF/DOCX)"),
) -> Any:
    if not files:
        return fail("At least one resume file is required", status_code=400)
    if len(files) > 10:
        return fail("You can upload up to 10 resumes only", status_code=400)

    try:
        parsed_jd = JobDescriptionParsed.model_validate_json(parsed_jd_json)
    except Exception as exc:  # noqa: BLE001
        return fail(f"Invalid parsed_jd JSON: {exc}", status_code=400)

    api_key = get_openai_api_key()
    resume_chain = ResumeParserChain(api_key)
    scorer = SimpleScoringChain(api_key)

    allowed_ext = {".pdf", ".docx"}
    results: List[ResumeScoringResult] = []

    sem = asyncio.Semaphore(get_max_parallel_tasks())

    async def process_file(upload: UploadFile) -> ResumeScoringResult:
        filename = upload.filename or ""
        parts = filename.lower().rsplit(".", 1)
        ext = f".{parts[1]}" if len(parts) == 2 else ""
        if ext not in allowed_ext:
            raise ValueError(f"Unsupported file type for {filename}. Only PDF and DOCX are allowed.")

        async with sem:
            text = await extract_text_from_upload(upload)
            if not text or not text.strip():
                raise ValueError(f"No readable text found in {filename}.")
            parsed_resume = await resume_chain.aparse_resume(text)
            scoring = await scorer.ascore_resume(parsed_resume, parsed_jd)
            return ResumeScoringResult(
                candidate=scoring.candidate,
                scoring_result=ScoringResult(
                    overall_score=scoring.scoring_result.overall_score,
                    basic_eligibility_score=scoring.scoring_result.basic_eligibility_score,
                    skills_match_score=scoring.scoring_result.skills_match_score,
                    experience_contextualization_score=scoring.scoring_result.experience_contextualization_score,
                    formatting_completeness_score=scoring.scoring_result.formatting_completeness_score,
                    recommendation=scoring.scoring_result.recommendation,
                    key_strengths=scoring.scoring_result.key_strengths,
                    areas_of_concern=scoring.scoring_result.areas_of_concern,
                    category_breakdown=scoring.scoring_result.category_breakdown,
                    role_specific_experience=scoring.scoring_result.role_specific_experience,
                    average_tenure_per_company=scoring.scoring_result.average_tenure_per_company,
                    highest_education_level=scoring.scoring_result.highest_education_level,
                    hiring_decision=scoring.scoring_result.hiring_decision,
                    keyword_matches=scoring.scoring_result.keyword_matches,
                    missing_keywords=scoring.scoring_result.missing_keywords,
                    alternative_keywords=scoring.scoring_result.alternative_keywords,
                    risk_factors=scoring.scoring_result.risk_factors,
                    next_steps=scoring.scoring_result.next_steps,
                )
            )

    # Run tasks concurrently but do not fail the entire batch if one fails
    gathered = await asyncio.gather(*(process_file(u) for u in files), return_exceptions=True)

    results: List[ResumeScoringResult] = []
    errors: List[str] = []
    for item in gathered:
        if isinstance(item, Exception):
            errors.append(str(item))
        else:
            results.append(item)

    if not results:
        # If everything failed, return a clear error
        joined = "; ".join(errors) if errors else "Unknown error"
        return fail(f"Failed to analyze all resumes: {joined}", status_code=502)

    # Otherwise return successes; frontend can decide how to surface partial errors
    return ApiResponse(success=True, data=results)


@router.post("/resumes/parse-text", status_code=status.HTTP_200_OK, response_model=ApiResponse[ResumeScoringResult])
async def parse_and_score_resume_text(
    parsed_jd_json: str = Form(..., description="Parsed job description JSON (stringified)"),
    resume_text: str = Form(..., description="Full resume text"),
) -> Any:
    if not resume_text or not resume_text.strip():
        return fail("Resume text is required", status_code=400)

    try:
        parsed_jd = JobDescriptionParsed.model_validate_json(parsed_jd_json)
    except Exception as exc:  # noqa: BLE001
        return fail(f"Invalid parsed_jd JSON: {exc}", status_code=400)

    api_key = get_openai_api_key()
    resume_chain = ResumeParserChain(api_key)
    scorer = SimpleScoringChain(api_key)

    try:
        parsed_resume = await resume_chain.aparse_resume(resume_text)
        scoring = await scorer.ascore_resume(parsed_resume, parsed_jd)
    except Exception as exc:  # noqa: BLE001
        return fail(f"Failed to analyze resume text: {exc}", status_code=502)

    return ApiResponse(success=True, data=scoring)