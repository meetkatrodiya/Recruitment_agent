from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
from app.controllers import job_description
from app.controllers import resume_parser
from app.controllers import email as email_controller
from app.core.config import get_allowed_origins

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


app = FastAPI(title="Recruitment AI Agent")

# CORS so React can talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

app.include_router(job_description.router, prefix="/api/v1", tags=["Job Description"])
app.include_router(resume_parser.router, prefix="/api/v1", tags=["Resumes"]) 
app.include_router(email_controller.router, prefix="/api/v1", tags=["Email"]) 
