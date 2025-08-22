from typing import Any
from fastapi import APIRouter, status
from app.models.email import EmailGenerateRequest, EmailContent, EmailSendRequest
from app.models.common import ApiResponse
from app.services.email_ai import generate_email_content
from app.services.email_smtp import send_email_smtp
from app.helpers.common_utils import fail

router = APIRouter()



@router.post("/email/generate", status_code=status.HTTP_200_OK, response_model=ApiResponse[EmailContent])
async def generate_email(payload: EmailGenerateRequest) -> Any:
    try:
        content = await generate_email_content(payload)
        return ApiResponse(success=True, data=content)
    except Exception as exc:  # noqa: BLE001
        return fail(f"Failed to generate email: {exc}", status_code=502)


@router.post("/email/send", status_code=status.HTTP_202_ACCEPTED, response_model=ApiResponse[dict])
async def send_email(payload: EmailSendRequest) -> Any:
    try:
        send_email_smtp(
            to_email=payload.to_email,
            subject=payload.subject,
            body_text=payload.body_text,
            from_name=payload.from_name,
        )
        return ApiResponse(success=True, data={"status": "sent"})
    except Exception as exc:  # noqa: BLE001
        return fail(f"Failed to send email: {exc}", status_code=502) 