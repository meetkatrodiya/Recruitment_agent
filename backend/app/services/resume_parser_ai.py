import logging
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.models.jd import JobDescriptionParsed
from app.models.resume import ResumeParsed, ScoringResult, ResumeScoringResult
from langchain_core.output_parsers import PydanticOutputParser
from app.core.config import get_openai_chat_model, get_openai_temperature

logger = logging.getLogger(__name__)

class JDParserChain:
    """LangChain-based job description parsing chain"""
    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model=get_openai_chat_model(),
            temperature=get_openai_temperature(),
            api_key=openai_api_key
        )
    
    def _create_jd_parsing_prompt(self) -> ChatPromptTemplate:
        """Create the prompt template for job description parsing"""
        template = """
        You are an expert at extracting structured data from job descriptions.

        Parse the following job description into structured fields.

        Job Description:
        {jd_text}
        
        format the output in the following JSON structure:
        {format_instructions}
        """
        return ChatPromptTemplate.from_template(template)

    def parse_job_description(self, jd_text: str) -> JobDescriptionParsed:
        """Parse the job description and return the parsed JD"""
        try:
            prompt = self._create_jd_parsing_prompt()
            parser = PydanticOutputParser(pydantic_object=JobDescriptionParsed)
            chain = prompt | self.llm | parser
            return chain.invoke({"jd_text": jd_text, "format_instructions": parser.get_format_instructions()})
        except Exception as e:
            logger.error("Error parsing job description: %s", e)
            raise ValueError(f"Failed to parse job description: {e}")


class ResumeParserChain:
    """LangChain-based resume parsing chain"""
    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model=get_openai_chat_model(),
            temperature=get_openai_temperature(),
            api_key=openai_api_key
        )
    
    def _create_resume_parsing_prompt(self) -> ChatPromptTemplate:
        """Create the prompt template for resume parsing"""
        template = """
        You are an expert at extracting structured data from resumes.

        Resume:
        {resume_text}
        
        Important Guidelines:
        - Normalize skill names (e.g., "JS" -> "JavaScript", "React.js" -> "React")
        - Extract years of experience from job descriptions when possible
        - If information is not available, use null or empty string
        - Ensure all dates and durations are in a consistent format
        - Clean and normalize company names and institution names
        - Return ONLY valid JSON - no additional text or explanations
        - Handle missing sections gracefully (empty arrays or null values)
        - Preserve the original meaning and context of the information
        - For skills: Return as a simple array of strings (e.g., ["Python", "JavaScript", "React"]), NOT objects
        - For certifications: Only include name and issuer, do not include dates
        - Skills format example: ["Python", "JavaScript", "Docker", "AWS"] - just skill names as strings

        format the output in the following JSON structure:
        {format_instructions}
        """
        return ChatPromptTemplate.from_template(template)
    
    def parse_resume(self, resume_text: str) -> ResumeParsed:
        """Parse the resume and return the parsed resume"""
        try:
            prompt = self._create_resume_parsing_prompt()
            parser = PydanticOutputParser(pydantic_object=ResumeParsed)
            chain = prompt | self.llm | parser
            return chain.invoke({"resume_text": resume_text, "format_instructions": parser.get_format_instructions()})
        except Exception as e:
            logger.error("Error parsing resume: %s", e)
            raise ValueError(f"Failed to parse resume: {e}")


class SimpleScoringChain:
    """
    Simple and generic AI-powered resume scoring chain.
    Evaluates resume relevance against job description using AI.
    Supports both Pydantic models and JSON inputs.
    """
    
    def __init__(self, openai_api_key: str, model: str | None = None):
        """
        Initialize the scoring chain.
        
        Args:
            openai_api_key: OpenAI API key
            model: Model to use for scoring (default: env OPENAI_CHAT_MODEL)
        """
        self.llm = ChatOpenAI(
            model=model or get_openai_chat_model(),
            temperature=get_openai_temperature(),
            api_key=openai_api_key
        )
    
    def _create_scoring_prompt(self) -> ChatPromptTemplate:
        """Create a comprehensive scoring prompt with strict format requirements"""
        template = """
        You are an AI recruiter evaluating a candidate's resume against a job description.
    Focus on providing detailed comparisons between job requirements and candidate qualifications, and apply thoughtful, non-uniform score logic. Avoid generic scores like 78, 82, 68 unless truly justified.

    PARSED JOB DESCRIPTION:
    {job_description}

    PARSED RESUME:
    {resume}

    EVALUATION APPROACH – DETAILED COMPARISON:

    You must evaluate the candidate across five categories, but **only three categories contribute to the overall score**:

    --------------------------------------------------
    1. BASIC ELIGIBILITY COMPARISON (45%):
    This is the most important category and has a strong impact on the final score.

    - **Years of Experience**:
        - If candidate has no experience → Score 0%
        - count the years of experience from the resume, if there is experince written as 2023-present, then count the years of experience as 2023- current year (for eg,2025-2023=2 years)
        - If candidate meets or exceeds role-specific experience → Score 100%
        - If candidate has ≤ 6 months shortfall → Score between 60–80% based on gap length
        - If shortfall > 6 months → Score 0%
    - **Education Level**: Match degree level and discipline (e.g., "B.Tech in CSE, 2020")
    - **Location/Authorization**: Must match job requirement (remote eligibility, visa status, etc.)

    ➤ If Basic Eligibility Score ≤ 20%:
        - Still evaluate other areas (Skills, Experience, etc.)
        - But **cap total score to max 55**
        - Mark candidate as **NOT RECOMMENDED**

    --------------------------------------------------
    2. SKILLS MATCH COMPARISON (30%):
    - Required Skills: List each and whether the candidate has them
    - Nice-to-Have Skills: Identify extras present
    - Skill Proficiency: Estimate based on resume info
    - Certifications: Only consider if explicitly required

    Be specific:  
    "Job needs React, candidate has 3 years with React from XYZ project – MATCH"

    --------------------------------------------------
    3. EXPERIENCE RELEVANCE COMPARISON (25%):
    - Project Domains: Relevance to job description
    - Role Progression: Does it logically lead to this role?
    - Industry Background: Same or different industry?
    - Tech Stack: Compare directly
    - Role-Specific Tasks: Match vs job description
    - Tenure Stability: Avoid scoring internships

    --------------------------------------------------
    4. FORMATTING & COMPLETENESS (Display Only):
    - Structure, clarity, and professionalism
    - Major omissions, red flags, unclear content
    ➤ This section does **not** affect scoring.

    --------------------------------------------------
    5. OVERALL FIT & POTENTIAL (Display Only):
    - Culture fit, growth mindset, communication, etc.
    ➤ Display observations only – do **not** use for scoring.

    --------------------------------------------------
    SCORING & DECISION RULES:

    ➤ Score each of the following categories from 0–100:
    - Basic Eligibility × 0.45
    - Skills Match × 0.30
    - Experience Relevance × 0.25

    ➤ If Basic Eligibility Score ≤ 20%, apply score cap (max final score: 55)

    ➤ Recommendation Guidelines:
    - STRONG HIRE: 85–100
    - RECOMMENDED: 70–84
    - CONSIDER: 60–69
    - NOT RECOMMENDED: Below 60

    ➤ Do not round scores to neat multiples unless the evidence justifies it. Use your reasoning to dynamically assign scores.

    --------------------------------------------------
    FINAL OUTPUT INSTRUCTIONS:
    {format_instructions}
        """
        return ChatPromptTemplate.from_template(template)
    
    def score_resume(self, resume: ResumeParsed, job_description: JobDescriptionParsed) -> ResumeScoringResult:
        """
        Score a resume against a job description.
        
        Args:
            resume: Resume data as Pydantic model
            job_description: Job description data as Pydantic model
            
        Returns:
            ResumeScoringResult with detailed analysis
        """
        try:
            prompt = self._create_scoring_prompt()
            parser = PydanticOutputParser(pydantic_object=ResumeScoringResult)
            chain = prompt | self.llm | parser
            return chain.invoke({
                "job_description": job_description,
                "resume": resume,
                "format_instructions": parser.get_format_instructions()
            })
        except Exception as e:
            logger.error("Error scoring resume: %s", e)
            raise ValueError(f"Failed to score resume: {e}")
