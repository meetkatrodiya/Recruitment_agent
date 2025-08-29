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
        "Follow the exact structure, tone, and formatting of the sample below.\n"
        "Populate the content using the provided inputs. If a field is unknown, omit it or use an em dash (—).\n"
        "Do not add extra sections or headings beyond what the sample shows.\n"
        "Output must be plain text (no Markdown). Use the '· ' bullet character for lists.\n\n"
        f"Inputs to use:\n"
        f"- Company: {req.company_name}\n"
        f"- Job Title: {req.job_title}\n"
        f"- Employment Type: {req.employment_type}\n"
        f"- Industry: {req.industry}\n"
        f"- Location: {req.location}\n"
        f"- Required Years of Experience: {req.years_of_experience}+\n"
        f"- Must-have Skills: {', '.join(req.skills_list)}\n\n"
        "Formatting requirements (strict):\n"
        "1) Start with six single-line headers in this exact order: Company, Job Title, Division/Department (use — if unknown), Required Experience as 'X+', Employment Type (e.g., FullTime), Location (UPPERCASE).\n"
        "2) Add a concise 2–3 line company blurb.\n"
        "3) Add the heading 'Role Overview:' and one concise paragraph.\n"
        "4) Add the heading 'Key Responsibilities:' followed by 6–9 bullets prefixed with '· '.\n"
        "5) Add the heading 'Required Skills & Qualifications:' followed by 6–9 bullets prefixed with '· ' and include years and listed skills where relevant.\n"
        "6) Keep language inclusive, specific, and actionable. No placeholders.\n\n"
        "Sample to imitate (do not copy verbatim; adapt to the provided inputs):\n"
        "E2M SOLUTIONS PRIVATE LIMITED\n"
        "AI Developer\n"
        "AI Division\n"
        "2+\n"
        "FullTime\n"
        "AHMEDABAD\n"
        "E2M is not your regular digital marketing firm. We're an equal opportunity provider, founded on strong\n"
        "business ethics and driven by more than 300 experienced professionals.\n"
        "Our client base is made up of digital agencies that rely on us to solve bandwidth issues, reduce\n"
        "overheads, and boost profitability. We need driven, tech-savvy professionals like you to help us deliver\n"
        "next-gen solutions. If you're someone who dreams big and thrives in innovation, E2M has a place for\n"
        "you.\n"
        "Role Overview:\n"
        "As an AI Developer/Python Developer – AI Implementation Specialist/AI Executor, you will be\n"
        "responsible for designing and integrating AI capabilities into production systems using Python and key\n"
        "ML libraries. This role requires a strong backend development foundation and a proven track record of\n"
        "deploying AI use cases using tools like TensorFlow, Keras, or OpenAI APIs. You'll work cross-\n"
        "functionally to deliver scalable AI-driven solutions.\n"
        "Key Responsibilities:\n"
        "· Design and develop backend solutions using Python, with a focus on AI-driven features.\n"
        "· Implement and integrate AI/ML models using tools like OpenAI, Hugging Face, or Lang Chain.\n"
        "· Use core Python libraries (NumPy, Pandas, TensorFlow, Keras) to process data, train, or implement models.\n"
        "· Translate business needs into AI use cases and deliver working solutions.\n"
        "· Collaborate with product, engineering, and data teams to define integration workflows.\n"
        "· Develop REST APIs and micro services to deploy AI components within applications.\n"
        "· Maintain and optimize AI systems for scalability, performance, and reliability.\n"
        "· Keep pace with advancements in the AI/ML landscape and evaluate tools for continuous improvement.\n"
        "Required Skills & Qualifications:\n"
        "· Minimum 2+ years of overall experience, including at least 1 year in AI/ML integration and strong hands-on expertise in Python for backend development.\n"
        "· Proficiency in libraries such as NumPy, Pandas, TensorFlow, and Keras\n"
        "· Practical exposure to AI platforms/APIs (e.g., OpenAI, LangChain, Hugging Face)\n"
        "· Solid understanding of REST APIs, microservices, and integration practices\n"
        "· Ability to work independently in a remote setup with strong communication and ownership\n"
        "· Excellent problem-solving and debugging capabilities\n"
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