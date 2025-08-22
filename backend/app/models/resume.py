from typing import List, Optional, Union
from pydantic import BaseModel, Field


class CandidateInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    location: Optional[str] = None

    


# Structured resume model for parsing/scoring chains
class ResumeParsed(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    location: Optional[str] = None
    years_of_experience: Optional[float] = None
    education: List[str] = []
    skills: List[str] = []
    certifications: List[str] = []
    work_experience: List[str] = []

class BasicEligibilityBreakdown(BaseModel):
    years_of_experience: Optional[float] = None
    years_of_experience_reasoning: Optional[str] = None  # JD requirement vs candidate experience
    education: Optional[Union[float, str]] = None
    education_reasoning: Optional[str] = None  # JD requirement vs candidate education
    location: Optional[Union[float, str]] = None
    location_reasoning: Optional[str] = None  # JD requirement vs candidate location

class SkillsMatchBreakdown(BaseModel):
    hard_skills: Optional[float] = None
    hard_skills_reasoning: Optional[str] = None  # Required skills vs candidate skills
    soft_skills: Optional[Union[float, str]] = None
    soft_skills_reasoning: Optional[str] = None  # Required soft skills vs candidate soft skills
    certifications: Optional[Union[float, str]] = None
    certifications_reasoning: Optional[str] = None  # Required certs vs candidate certs
    skill_proficiency: Optional[float] = None
    skill_proficiency_reasoning: Optional[str] = None  # Skill level assessment

class ExperienceContextualizationBreakdown(BaseModel):
    project_relevance: Optional[float] = None
    project_relevance_reasoning: Optional[str] = None  # Relevant projects analysis
    role_titles_progression: Optional[Union[float, str]] = None
    role_titles_progression_reasoning: Optional[str] = None  # Career progression analysis
    industry_experience: Optional[float] = None
    industry_experience_reasoning: Optional[str] = None  # Industry relevance
    domain_knowledge: Optional[Union[float, str]] = None
    domain_knowledge_reasoning: Optional[str] = None  # Domain expertise assessment

class FormattingCompletenessBreakdown(BaseModel):
    structure: Optional[float] = None
    structure_reasoning: Optional[str] = None  # Resume structure analysis
    completeness: Optional[Union[float, str]] = None
    completeness_reasoning: Optional[str] = None  # Missing information analysis
    presentation: Optional[float] = None
    presentation_reasoning: Optional[str] = None  # Professional presentation assessment
    red_flags: Optional[Union[float, str]] = None
    red_flags_reasoning: Optional[str] = None  # Red flags identification and explanation



class CategoryBreakdown(BaseModel):
    basic_eligibility_score: BasicEligibilityBreakdown
    skills_match_score: SkillsMatchBreakdown
    experience_contextualization_score: ExperienceContextualizationBreakdown
    formatting_completeness_score: FormattingCompletenessBreakdown



class ScoringResult(BaseModel):
    overall_score: float = Field(..., ge=0, le=100, description="Overall match score (0-100)")
    basic_eligibility_score: float = Field(..., ge=0, le=100, description="Basic eligibility score (0-100)")
    skills_match_score: float = Field(..., ge=0, le=100, description="Skills match score (0-100)")
    experience_contextualization_score: float = Field(..., ge=0, le=100, description="Experience contextualization score (0-100)")
    formatting_completeness_score: float = Field(..., ge=0, le=100, description="Formatting completeness score (0-100)")
    recommendation: str = Field(..., description="Overall recommendation for the candidate")
    key_strengths: List[str] = Field(..., description="List of candidate's key strengths")
    areas_of_concern: List[str] = Field(..., description="List of areas of concern or improvement")
    category_breakdown: CategoryBreakdown
    role_specific_experience: float = Field(..., description="Role specific experience duration in years")
    average_tenure_per_company: float = Field(..., description="Average tenure per company duration in years")
    highest_education_level: str = Field(..., description="Highest education level of the candidate with exact degree name and year of graduation")
    # Decision-making fields - required with proper defaults
    hiring_decision: str = Field(..., description="Hiring decision: STRONG HIRE, RECOMMENDED, CONSIDER, NOT RECOMMENDED")
    keyword_matches: List[str] = Field(default_factory=list, description="List of exact keyword matches found in resume")
    missing_keywords: List[str] = Field(default_factory=list, description="List of missing keywords from job requirements")
    alternative_keywords: List[str] = Field(default_factory=list, description="List of alternative keywords that could substitute")
    risk_factors: List[str] = Field(default_factory=list, description="List of risk factors or red flags")
    next_steps: List[str] = Field(default_factory=list, description="Recommended next steps for hiring process")
    
    
class ResumeScoringResult(BaseModel):
    candidate: CandidateInfo
    scoring_result: ScoringResult
    
    
    
    