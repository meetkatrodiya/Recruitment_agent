import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Set
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
        # Sync LLM (kept for compatibility)
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

    async def aparse_job_description(self, jd_text: str) -> JobDescriptionParsed:
        """Async parse for JD"""
        try:
            prompt = self._create_jd_parsing_prompt()
            parser = PydanticOutputParser(pydantic_object=JobDescriptionParsed)
            chain = prompt | self.llm | parser
            return await chain.ainvoke({"jd_text": jd_text, "format_instructions": parser.get_format_instructions()})
        except Exception as e:
            logger.error("Error parsing job description (async): %s", e)
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

    async def aparse_resume(self, resume_text: str) -> ResumeParsed:
        """Async parse the resume"""
        try:
            prompt = self._create_resume_parsing_prompt()
            parser = PydanticOutputParser(pydantic_object=ResumeParsed)
            chain = prompt | self.llm | parser
            return await chain.ainvoke({"resume_text": resume_text, "format_instructions": parser.get_format_instructions()})
        except Exception as e:
            logger.error("Error parsing resume (async): %s", e)
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

    PRECOMPUTED FEATURES (ground-truth style metrics to anchor scoring):
    {precomputed_features}

    IMPORTANT SCORING GUIDANCE (SEMANTIC/INTENT MATCHING):
    - Prioritize overall semantic similarity and intent alignment between the JD and the resume.
    - Consider synonyms and paraphrases as matches even if exact keywords differ.
    - Base Skills Match and Experience Relevance primarily on semantic similarity between JD responsibilities/requirements and the resume's experience/skills.
    - Do not penalize for minor wording differences or missing exact phrases if the underlying capability is evidenced.
    - Missing NICE-TO-HAVE items should minimally impact Skills Match if REQUIRED items are covered reasonably; focus more on experience evidence.
    - When listing keyword_matches and missing_keywords, use short human-readable phrases (max 5 each), preserve spaces, and avoid any token normalization.

    Provide a concise Responsibilities-to-Experience Evidence Map (for your internal reasoning), e.g.:
    - "Develop REST APIs" ↔ "Built REST APIs with FastAPI at TechNova (2022–present)" – STRONG MATCH
    - "TensorFlow model training" ↔ "Trained NLP models with TensorFlow/Keras" – MATCH
    Use this mapping to justify Skills Match and Experience Relevance.

    EVALUATION APPROACH – DETAILED COMPARISON:

    You must evaluate the candidate across five categories, but **only three categories contribute to the overall score**:

    --------------------------------------------------
    1. BASIC ELIGIBILITY COMPARISON (35%):
    This is the most important category and has a strong impact on the final score.

    - **Years of Experience**:
        - If candidate has no experience → Score 0%
        - count the years of experience from the resume, if there is experince written as 2023-present, then count the years of experience as 2023- current year (for eg,2025-2023=2 years)
        - If candidate meets or exceeds role-specific experience → Score 100%
        - If candidate has ≤ 6 months shortfall → Score between 60–80% based on gap length
        - If shortfall > 6 months → Score 0%
    - **Education Level**: Match degree level and discipline (e.g., "B.Tech in CSE, 2020")
    - **Location/Authorization**: Must match job requirement (remote eligibility etc.)

    ➤ If Basic Eligibility Score ≤ 20%:
        - Still evaluate other areas (Skills, Experience, etc.)
        - But **cap total score to max 55**
        - Mark candidate as **NOT RECOMMENDED**

    --------------------------------------------------
    2. SKILLS MATCH COMPARISON (30%):
    - Required Skills: List each and whether the candidate has them (these matter most)
    - Nice-to-Have Skills: Identify extras present (missing here should not significantly reduce score)
    - Skill Proficiency: Estimate based on resume info
    - Certifications: Only consider if explicitly required

    Be specific:  
    "Job needs React, candidate has 3 years with React from XYZ project – MATCH"

    --------------------------------------------------
    3. EXPERIENCE RELEVANCE COMPARISON (35%):
    - Project Domains: Relevance to job description
    - Role Progression: Does it logically lead to this role?
    - Industry Background: Same or different industry?
    - Tech Stack: Compare directly
    - Role-Specific Tasks: Match vs job description

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
    - Basic Eligibility × 0.35
    - Skills Match × 0.30
    - Experience Relevance × 0.35

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
            # 1) Pre-compute deterministic anchors
            deterministic = _build_precomputed_features(job_description, resume)

            # 2) Invoke LLM with anchors
            prompt = self._create_scoring_prompt()
            parser = PydanticOutputParser(pydantic_object=ResumeScoringResult)
            chain = prompt | self.llm | parser
            llm_result: ResumeScoringResult = chain.invoke({
                "job_description": job_description,
                "resume": resume,
                "precomputed_features": deterministic,
                "format_instructions": parser.get_format_instructions()
            })

            # 3) Post-process to enforce caps, bounds, and consistent recommendations
            return _post_process_scoring(llm_result, deterministic)
        except Exception as e:
            logger.error("Error scoring resume: %s", e)
            raise ValueError(f"Failed to score resume: {e}")

    async def ascore_resume(self, resume: ResumeParsed, job_description: JobDescriptionParsed) -> ResumeScoringResult:
        """Async version of score_resume"""
        try:
            deterministic = _build_precomputed_features(job_description, resume)
            prompt = self._create_scoring_prompt()
            parser = PydanticOutputParser(pydantic_object=ResumeScoringResult)
            chain = prompt | self.llm | parser
            llm_result: ResumeScoringResult = await chain.ainvoke({
                "job_description": job_description,
                "resume": resume,
                "precomputed_features": deterministic,
                "format_instructions": parser.get_format_instructions()
            })
            return _post_process_scoring(llm_result, deterministic)
        except Exception as e:
            logger.error("Error scoring resume (async): %s", e)
            raise ValueError(f"Failed to score resume: {e}")


# ------------------------------
# Deterministic helpers
# ------------------------------

def _normalize_token(token: str) -> str:
    return re.sub(r"[^a-z0-9+#.]", "", token.lower())


def _tokenize_skills(skills: Optional[List[str]]) -> Set[str]:
    if not skills:
        return set()
    return { _normalize_token(s) for s in skills if isinstance(s, str) and s.strip() }


def _estimate_years_from_ranges(experiences: Optional[List[str]]) -> float:
    if not experiences:
        return 0.0
    # Heuristics: detect patterns like "2020-2023", "2019–Present", "Jan 2022 – Mar 2024"
    current_year = datetime.utcnow().year
    month_to_num = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'sept': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }

    def add_range(start_year: int, start_month: int, end_year: int, end_month: int) -> float:
        months = (end_year - start_year) * 12 + (end_month - start_month)
        return max(0.0, months / 12.0)

    total_years = 0.0
    for line in experiences:
        text = line.strip()

        # Pattern A: YYYY – (YYYY|Present)
        for m in re.finditer(r"(?P<sY>(19|20)\d{2})\s*[–-]\s*(?P<eY>(19|20)\d{2}|present)", text, flags=re.I):
            sY = int(m.group('sY'))
            eY_str = m.group('eY')
            eY = current_year if re.match(r"present", eY_str, flags=re.I) else int(eY_str)
            if eY >= sY:
                total_years += add_range(sY, 1, eY, 12)

        # Pattern B: (Mon YYYY) – (Mon YYYY|Present)
        for m in re.finditer(r"(?P<sM>[A-Za-z]{3,9})\s+(?P<sY2>(19|20)\d{2})\s*[–-]\s*(?:(?P<eM>[A-Za-z]{3,9})\s+(?P<eY2>(19|20)\d{2})|(?P<present>present))", text, flags=re.I):
            sM = month_to_num.get(m.group('sM').lower()[:3], 1)
            sY2 = int(m.group('sY2'))
            if m.group('present'):
                eM = datetime.utcnow().month
                eY2 = current_year
            else:
                eM = month_to_num.get(m.group('eM').lower()[:3], 12)
                eY2 = int(m.group('eY2'))
            if (eY2 > sY2) or (eY2 == sY2 and eM >= sM):
                total_years += add_range(sY2, sM, eY2, eM)

    return max(0.0, round(total_years, 2))


def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    if union == 0:
        return 0.0
    return round(inter / union * 100.0, 2)


def _build_precomputed_features(jd: JobDescriptionParsed, resume: ResumeParsed) -> Dict[str, object]:
    jd_required = set()
    if jd and jd.requirements and jd.requirements.required_skills and jd.requirements.required_skills.required:
        jd_required = _tokenize_skills(jd.requirements.required_skills.required)

    jd_nice = set()
    if jd and jd.requirements and jd.requirements.required_skills and jd.requirements.required_skills.nice_to_have:
        jd_nice = _tokenize_skills(jd.requirements.required_skills.nice_to_have)

    resume_skills = _tokenize_skills(resume.skills)

    # Years
    resume_total_years = resume.years_of_experience or 0.0
    estimated_years = _estimate_years_from_ranges(resume.work_experience)
    effective_years = max(resume_total_years, estimated_years)

    # JD required years
    jd_required_years = 0
    if jd and jd.requirements and jd.requirements.required_years_of_experience is not None:
        jd_required_years = int(jd.requirements.required_years_of_experience or 0)

    # Location proximity (basic exact compare)
    jd_location = (jd.job_information.location or "").strip().lower() if jd and jd.job_information else ""
    resume_location = (resume.location or "").strip().lower()
    location_match = 100.0 if jd_location and resume_location and (jd_location in resume_location or resume_location in jd_location) else 0.0

    return {
        "effective_years": effective_years,
        "jd_required_years": jd_required_years,
        "years_gap_months": max(0, int((jd_required_years - effective_years) * 12)),
        "location_match": location_match,
        # Keep features minimal; rely on semantic/intent evaluation within the LLM for skill/experience matching
        "resume_total_skills": len(resume_skills),
        "required_count": len(jd_required),
        "nice_to_have_count": len(jd_nice),
        "required_hits": len(jd_required & resume_skills),
    }


def _cap(value: float, low: float, high: float) -> float:
    return float(min(max(value, low), high))


def _derive_recommendation(overall: float) -> str:
    if overall >= 85:
        return "STRONG HIRE"
    if overall >= 70:
        return "RECOMMENDED"
    if overall >= 60:
        return "CONSIDER"
    return "NOT RECOMMENDED"


def _post_process_scoring(result: ResumeScoringResult, features: Dict[str, object]) -> ResumeScoringResult:
    try:
        basic = _cap(result.scoring_result.basic_eligibility_score, 0, 100)
        skills = _cap(result.scoring_result.skills_match_score, 0, 100)
        exp = _cap(result.scoring_result.experience_contextualization_score, 0, 100)
        formatting = _cap(result.scoring_result.formatting_completeness_score, 0, 100)

        # Enforce deterministic adjustments
        # Years of experience rule
        if isinstance(features.get("years_gap_months"), int):
            gap = features["years_gap_months"]
            if gap > 6:
                basic = 0.0
            elif gap > 0:
                basic = min(basic, 80.0)

        # Leniency: if REQUIRED coverage is strong, ensure a minimum floor for skills
        try:
            req = int(features.get("required_count", 0))
            hits = int(features.get("required_hits", 0))
            coverage = (hits / req) if req > 0 else 0.0
            if coverage >= 0.6:  # 60%+ required covered
                skills = max(skills, 60.0)
            if coverage >= 0.8:  # 80%+ required covered
                skills = max(skills, 70.0)
        except Exception:
            pass

        # Recompute overall with weights (aligned with prompt: 0.35/0.30/0.35)
        overall = round(basic * 0.35 + skills * 0.30 + exp * 0.35, 2)

        # Apply cap if basic <= 20
        if basic <= 20:
            overall = min(overall, 55.0)

        # Update result
        result.scoring_result.basic_eligibility_score = round(basic, 2)
        result.scoring_result.skills_match_score = round(skills, 2)
        result.scoring_result.experience_contextualization_score = round(exp, 2)
        result.scoring_result.formatting_completeness_score = round(formatting, 2)
        result.scoring_result.overall_score = overall
        result.scoring_result.hiring_decision = _derive_recommendation(overall)

        # Ensure keyword lists are short, readable, unique, and max 5 items
        def _clean_list(values: Optional[List[str]]) -> List[str]:
            if not isinstance(values, list):
                return []
            seen = set()
            cleaned: List[str] = []
            for v in values:
                if not isinstance(v, str):
                    continue
                item = v.strip()
                if not item or item in seen:
                    continue
                seen.add(item)
                cleaned.append(item)
                if len(cleaned) >= 5:
                    break
            return cleaned

        result.scoring_result.keyword_matches = _clean_list(result.scoring_result.keyword_matches)
        result.scoring_result.missing_keywords = _clean_list(result.scoring_result.missing_keywords)

        return result
    except Exception:
        return result
