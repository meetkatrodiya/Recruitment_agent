from pydantic import BaseModel, Field
from pydantic import field_validator
from typing import List, Optional


class ManualJDInput(BaseModel):
    text: str = Field(min_length=1, description="Full job description text")

    @field_validator("text")
    @classmethod
    def validate_text_not_empty(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Text must not be empty")
        return trimmed


class JDGenerationRequest(BaseModel):
    job_title: str = Field(min_length=1)
    years_of_experience: int = Field(ge=0, le=60)
    must_have_skills: str = Field(min_length=1, description="Comma-separated skills")
    company_name: str = Field(min_length=1)
    employment_type: str = Field(min_length=1, description="e.g., Full-time, Part-time, Contract")
    industry: str = Field(min_length=1)
    location: str = Field(min_length=1)
    language: Optional[str] = Field(default="English")

    @property
    def skills_list(self) -> List[str]:
        parts = [s.strip() for s in self.must_have_skills.split(",")]
        return [s for s in parts if s]


# Structured JD model for parsing/scoring chains
class JobInformation(BaseModel):
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str]

class RequiredSkills(BaseModel):
    required: Optional[List[str]] = None
    nice_to_have: Optional[List[str]] = None

class Requirements(BaseModel):
    required_skills: RequiredSkills
    required_years_of_experience: Optional[int]
    required_education_level: Optional[str]

class AdditionalInformation(BaseModel):
    benefits: Optional[List[str]] = None
    salary_range: Optional[str]

class JobDescriptionParsed(BaseModel):
    job_information: JobInformation
    requirements: Requirements
    responsibilities: List[str]
    additional_information: AdditionalInformation

    