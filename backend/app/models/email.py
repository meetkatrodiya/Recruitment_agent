from typing import Optional, Literal
from pydantic import BaseModel, Field, EmailStr


EmailType = Literal["interview", "rejection"]


class CandidateBrief(BaseModel):
    name: Optional[str] = None
    email: EmailStr


class EmailGenerateRequest(BaseModel):
    type: EmailType
    candidate: CandidateBrief
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    jd_summary: Optional[str] = None
    score: Optional[int] = Field(default=None, ge=0, le=100)
    remarks: Optional[str] = None
    language: Optional[str] = Field(default="English")


class EmailContent(BaseModel):
    subject: str
    body_text: str


class EmailSendRequest(BaseModel):
    to_email: EmailStr
    subject: str
    body_text: str
    from_name: Optional[str] = None 