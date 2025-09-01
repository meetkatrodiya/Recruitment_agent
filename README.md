# Recruitment AI Agent

End-to-end recruitment assistant that lets HR: 
- Input Job Descriptions (upload/manual/generate)
- Upload multiple resumes (PDF/DOC/DOCX) and score them against the JD
- Review detailed per-candidate analysis
- Generate and send personalized interview/rejection emails
- Use a polished React (TypeScript) UI powered by a FastAPI backend

---

## Tech Stack
- Backend: FastAPI, Pydantic v2, LangChain, OpenAI SDK, PyPDF2, python-docx
- Frontend: React + TypeScript + Vite, Material UI
- Email: SMTP (configurable), AI-generated email content with OpenAI

---

## Repository Structure
```
backend/
  app/
    controllers/           # FastAPI routes
      email.py
      job_description.py
      resume_parser.py
    core/
      config.py            # Env & client helpers
    helpers/               # Shared helpers
      common_utils.py      # fail() response helper
      parsing_utils.py     # (reserved for parsing helpers)
    models/                # Pydantic models
      email.py
      jd.py
      resume.py
      common.py            # ApiResponse[T]
    services/              # Business logic
      file_extractor.py
      jd_ai.py
      email_ai.py
      email_smtp.py
      resume_parser_ai.py  # JD/Resume parsing & scoring chains
  requirements.txt
frontend/
  src/
    lib/api.ts             # Axios client & typed helpers
    pages/                 # Workflow, JD and Resumes pages
    store/JDContext.tsx    # JD state across pages
  package.json
  vite.config.ts
README.md
```

---

## Prerequisites
- Python 3.11+
- Node.js 18+
- Valid OpenAI API key

---

## Backend Setup
1) Create and activate venv, install deps
```bash
cd backend
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

2) Configure environment
- Create a `.env` file in `backend/` (or export in your shell):
```bash
# Required
OPENAI_API_KEY=sk-...your-valid-key...

# Optional (sensible defaults are used if omitted)
OPENAI_CHAT_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.1
# Max concurrent LLM tasks when parsing/scoring multiple resumes (1–16)
MAX_PARALLEL_TASKS=4

# Email (to enable sending)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your@gmail.com
SMTP_PASSWORD=app_password
SMTP_FROM=your@gmail.com
```

3) Run the server
```bash
PYTHONPATH=$(pwd) venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4) API docs
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Frontend Setup
```bash
cd frontend
npm i
# Optionally configure API base for non-local backends
# echo 'VITE_API_BASE=https://your-api-host/api/v1' > .env
npm run dev
```
Open: `http://localhost:3000`

---

## Core Features & Flow
1) Job Description (JD)
- Upload PDF/DOC/DOCX → text extracted
- Manual input (textarea)
- Generate via AI using: Job Title, Experience, Skills, Company, Employment Type, Industry, Location
- Parse & Save JD: converts text into `JobDescriptionParsed` via OpenAI + LangChain

2) Resumes & Scoring
- Upload up to 10 resumes → text extracted
- Parse each resume
- Score against parsed JD with an AI chain (semantic/intent-first, experience‑focused) and structured output `ResumeScoringResult`:
  - `overall_score`, `hiring_decision`
  - Category scores & breakdowns
  - `keyword_matches`, `missing_keywords`, `key_strengths`, `areas_of_concern`, `next_steps`
- Scoring weights: Basic 0.35, Skills 0.30, Experience 0.35
- Batch processing runs in parallel; tune `MAX_PARALLEL_TASKS` to balance speed vs. rate limits

3) Results & Emails
- Best match highlighted
- Per-candidate details modal
- Generate Interview / Rejection email (AI-generated) and optionally send via SMTP

---

## API Overview
Base path: `/api/v1`

- Response envelope (applies to all endpoints):
```json
{
  "success": true,
  "message": null,
  "data": { /* endpoint-specific payload */ }
}
```
On errors:
```json
{
  "success": false,
  "message": "Human-readable error",
  "data": null
}
```

- JD
  - `POST /jd/upload` (multipart) → `ApiResponse<{ source, filename, text, length }>`
  - `POST /jd/manual` (json) → `ApiResponse<{ source, text, length }>`
  - `POST /jd/generate` (json) → `ApiResponse<{ job_description, length, inputs }>`
  - `POST /jd/parse` (json: {text}) → `ApiResponse<JobDescriptionParsed>`

- Resumes
  - `POST /resumes/parse` (multipart: `parsed_jd_json`, `files`) → `ApiResponse<ResumeScoringResult[]>`
  - `POST /resumes/parse-text` (form: `parsed_jd_json`, `resume_text`) → `ApiResponse<ResumeScoringResult>`

- Email
  - `POST /email/generate` (json) → `ApiResponse<{ subject, body_text }>`
  - `POST /email/send` (json) → `ApiResponse<{ status: "sent" }>`

Example: Parse JD
```bash
curl -s -X POST http://localhost:8000/api/v1/jd/parse \
  -H 'Content-Type: application/json' \
  -d '{"text":"We need a Data Scientist with Python and SQL."}' | jq
```

Example: Parse resumes
```bash
# First, capture the parsed JD JSON from /jd/parse into $JD

curl -s -X POST http://localhost:8000/api/v1/resumes/parse \
  -F "parsed_jd_json=$JD" \
  -F 'files=@/path/resume1.pdf' -F 'files=@/path/resume2.docx' | jq

# Or test a single resume as plain text
curl -s -X POST http://localhost:8000/api/v1/resumes/parse-text \
  -H 'Expect:' \
  -F "parsed_jd_json=$JD" \
  --form-string "resume_text=$(cat /path/resume.txt)" | jq
```

---

## AI Models & Rationale
- OpenAI GPT-4o (configurable via `OPENAI_CHAT_MODEL`)
  - JD generation/parse: accurate, clean outputs for downstream use
  - Resume parsing: robust extraction from noisy text
  - Scoring: semantic/intent‑focused, experience‑weighted evaluation returning structured fields
  - Email generation: concise, professional tone and personalization
- Temperature kept low (`~0.1`) for determinism on structured tasks; can be adjusted per your needs.

### Why GPT‑4o for this project
- Balanced capability vs. latency/cost: GPT‑4o offers strong reasoning and extraction quality with better throughput and cost than prior GPT‑4-class models, ideal for multi-file resume parsing and batch scoring.
- Structured outputs reliability: Lower temperature with GPT‑4o yields consistent JSON-like responses, improving downstream parsing for `JobDescriptionParsed` and `ResumeScoringResult`.
- Robust to noisy inputs: Handles varied resume formats, fragmented sections, and OCR-like text more gracefully than smaller models.
- Versatile across tasks: One model covers JD generation, JD parsing, resume parsing, scoring, and email drafting, simplifying ops/config.
- Future-proofing: Widely supported in tooling (OpenAI SDK, LangChain) with frequent updates and good model availability.

---

## Error Handling & Conventions
- All endpoints return `ApiResponse<T>` (see envelope above)
- Unified failure helper: `app/helpers/common_utils.py::fail(message, status_code)`
- Common validations
  - File types restricted to PDF/DOCX (HTTP 415 on mismatch)
  - Required fields must be non-empty (HTTP 400)
  - JD text length capped for safety (HTTP 413)
  - Extraction/AI/SMTP issues surfaced as 4xx/5xx with helpful `message`

---

## Troubleshooting
- 401 Invalid OpenAI API key
  - Ensure `OPENAI_API_KEY` is valid, set in the same shell as uvicorn, no quotes/spaces
  - Restart backend after changes

- 422 on `/email/generate`
  - Candidate email must be valid; frontend validates before calling
  - `score` is sent as integer; ensure payload matches required fields

- Missing `email-validator`
  - Install via backend requirements; if missing, run:
```bash
venv/bin/pip install email-validator
```

- File parsing issues
  - Only PDF and DOCX are supported; `.doc` is rejected with HTTP 415

- CORS errors
  - Set `BACKEND_CORS_ORIGINS` (comma-separated) in `.env` and restart backend

- Slow batch scoring or 502 on `/resumes/parse`
  - Reduce/increase `MAX_PARALLEL_TASKS` to fit your OpenAI rate limits and instance size
  - Very large resumes can increase latency; consider truncating less relevant sections upstream

---

## Quality & Configurability
- Centralized config in `app/core/config.py` (OpenAI model, temperature, CORS)
- Defensive error handling and consistent HTTP errors via `fail()` helper
- Strongly-typed Pydantic models for all request/response bodies
- UI uses environment-based API base (`VITE_API_BASE`) and typed API helpers
- Frontend unwraps the `ApiResponse<T>` envelope in `src/lib/api.ts`

---

## Run All (Quickstart)
```bash
# Backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cat > .env <<'EOF'
OPENAI_API_KEY=sk-...your-key...
BACKEND_CORS_ORIGINS=http://localhost:3000
EOF
PYTHONPATH=$(pwd) venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
```bash
# Frontend (in a new terminal)
cd frontend
npm i
npm run dev
```

Open `http://localhost:3000` and follow the workflow.

---

## Future Enhancements
- Persist projects/candidates to a database (Postgres + SQLAlchemy)
- Authentication & role-based access
- Model cost tracking & caching
- Export reports (PDF/CSV)

---

## License
MIT (or your preferred license) – update as appropriate.
$$