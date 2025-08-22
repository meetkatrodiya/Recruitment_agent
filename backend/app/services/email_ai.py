from fastapi import HTTPException
from app.core.config import get_async_openai_client
from app.models.email import EmailGenerateRequest, EmailContent
import os
from dotenv import load_dotenv

load_dotenv()
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")


async def generate_email_content(req: EmailGenerateRequest) -> EmailContent:
    client = get_async_openai_client()

    tone = "warm and professional" if req.type == "interview" else "polite and appreciative"
    intent = (
        "Invite the candidate for an interview, propose flexible time slots, ask for availability, and include next steps."
        if req.type == "interview"
        else "Thank the candidate for their time, explain the decision briefly without discouraging, encourage staying in touch, and wish them well."
    )

    prompt = (
        f"Write a {req.language} {req.type} email to the candidate below.\n\n"
        f"Candidate: {req.candidate.name or 'Candidate'} <{req.candidate.email}>\n"
        f"Company: {req.company_name or 'Our Company'}\n"
        f"Job Title: {req.job_title or 'the role'}\n"
        f"JD Summary: {req.jd_summary or ''}\n"
        f"Candidate Score (if available): {req.score or ''}\n"
        f"Remarks (if available): {req.remarks or ''}\n\n"
        f"Tone: {tone}.\n"
        f"Task: {intent}\n\n"
        "Return subject and body only. Avoid placeholders for names if known."
    )

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an expert recruiter writing concise, clear emails."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=300,
        )
        content = response.choices[0].message.content or ""
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"AI email generation failed: {exc}")

    if not content:
        raise HTTPException(status_code=502, detail="AI returned empty content")

    # naive split: assume first line is subject if it starts with 'Subject:'
    subject = "Interview Invitation" if req.type == "interview" else "Application Update"
    body = content.strip()
    first_line, _, rest = body.partition("\n")
    if first_line.lower().startswith("subject:"):
        subject = first_line.split(":", 1)[1].strip() or subject
        body_text = rest.strip()
    else:
        body_text = body

    return EmailContent(subject=subject, body_text=body_text) 