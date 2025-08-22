from fastapi import HTTPException
from app.models.jd import JDGenerationRequest
from app.core.config import get_async_openai_client
import os
from dotenv import load_dotenv

load_dotenv()

SYSTEM_MESSAGE = (
    "You are an expert HR recruiter and technical writer. "
    "Produce concise, clear, and inclusive job descriptions. "
    "Use bullet points for Responsibilities and Requirements. "
    "Avoid biased language and keep to one page."
)

MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")


async def generate_job_description(req: JDGenerationRequest) -> str:
    client = get_async_openai_client()

    prompt = (
        f"Create a professional Job Description in {req.language}.\n\n"
        f"Company: {req.company_name}\n"
        f"Job Title: {req.job_title}\n"
        f"Employment Type: {req.employment_type}\n"
        f"Industry: {req.industry}\n"
        f"Location: {req.location}\n"
        f"Required Years of Experience: {req.years_of_experience}+\n"
        f"Must-have Skills: {', '.join(req.skills_list)}\n\n"
        "Structure the output with these sections: \n"
        "- Role Summary\n"
        "- Key Responsibilities (5-8 bullets)\n"
        "- Required Qualifications (5-8 bullets; include years and listed skills)\n"
        "- Nice-to-have (optional)\n"
        "- Benefits/Perks (generic if not specified)\n"
        "- Work Location & Type\n"
    )

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=800,
        )
        content = response.choices[0].message.content if response.choices else ""
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"AI generation failed: {exc}")

    if not content:
        raise HTTPException(status_code=502, detail="AI returned empty content")

    return content.strip() 