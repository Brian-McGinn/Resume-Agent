from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from services.llm_service import LLMService
from services.rag_service import setEmbeddings
from services.orchestrator_agent import AgentService
from services.utilities.database_util import get_curated_resume
from pydantic import BaseModel
from pathlib import Path
import os
from dotenv import load_dotenv
import json
import logging
from typing import Generator
from weasyprint import HTML, CSS
from markdown import markdown

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)
app = FastAPI(title="AI Resume Agent", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

llm_service = LLMService()
agent_service = AgentService()

# Pydantic models for request/response
class MessageRequest(BaseModel):
    text: str

class MessageResponse(BaseModel):
    message: str

def generate_stream(response_generator: Generator[str, None, None]) -> Generator[str, None, None]:
    """
    Generate a stream of responses from the AI.
    Each response is formatted as a Server-Sent Event.
    """
    try:
        for chunk in response_generator:
            # Format as SSE
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        # Send done signal
        yield "data: [DONE]\n\n"
    except Exception as e:
        logger.error(f"Error in stream generation: {str(e)}", exc_info=True)
        error_msg = json.dumps({"error": str(e)})
        yield f"data: {error_msg}\n\n"
        yield "data: [DONE]\n\n"

@app.post("/api/send_message")
async def send_message(request: MessageRequest):
    """
    Send a job description and get AI comparison with uploaded resume.
    """
    try:
        text = request.text.replace('\r', '').replace('\n', '')
        response_generator = llm_service.send_message(text)
        
        return StreamingResponse(
            generate_stream(response_generator),
            media_type="text/event-stream",
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
            }
        )
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/revise_resume")
async def revise_resume():
    """
    Generate a revised resume based on previous comparison.
    """
    try:
        response_generator = llm_service.revise_resume()
        
        return StreamingResponse(
            generate_stream(response_generator),
            media_type="text/event-stream",
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
            }
        )
    except Exception as e:
        logger.error(f"Error in revise_resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/automate")
async def automate(
    search_term: str = "software engineer",
    location: str = "",
    results_wanted: int = 10,
    hours_old: int = 24,
    country_indeed: str = "USA",
    min_job_score: int = 60
):
    """
    Begin the automated resume agent.
    Accepts query parameters:
    - search_term
    - location
    - results_wanted
    - hours_old
    - country_indeed
    """
    try:
        result = await agent_service.automate(
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            country_indeed=country_indeed,
            min_job_score=min_job_score
        )
        return result
    except Exception as e:
        logger.error(f"Error in automate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    """
    Upload a resume PDF file for processing.
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Save the file
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process the file with RAG service
        # Note: We need to create a file-like object for the existing setEmbeddings function
        class FileWrapper:
            def __init__(self, filename):
                self.filename = filename
        
        file_wrapper = FileWrapper(file.filename)
        setEmbeddings(file_wrapper)
        
        return MessageResponse(message=f"{file.filename} uploaded successfully!")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download_curated_resume")
async def download_curated_resume(job_url: str, asPdf: bool = False):
    """
    Retrieve the curated resume for a specific job.
    If asPdf is True, return the resume as a PDF file.
    Otherwise, return the markdown content.
    """
    try:
        title, curated_resume = get_curated_resume(job_url)
        if not curated_resume:
            raise HTTPException(status_code=404, detail="Curated resume not found for the given job_url")
        
        if asPdf:
            css_style = """
            body { font-size: 8pt; }
            h1 { font-size: 12pt; }
            h2 { font-size: 10pt; }
            h3 { font-size: 10pt; }
            """

            output_pdf_path = "curated_resume.pdf"
            html_content = markdown(curated_resume)
            HTML(string=html_content).write_pdf(output_pdf_path, stylesheets=[CSS(string=css_style)])

            # Return the PDF file as a response
            return FileResponse(
                output_pdf_path,
                media_type="application/pdf",
                filename=f"{title}.pdf"
            )
        else:
            return curated_resume
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_curated_resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "AI Resume Curator API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/api/upload",
            "send_message": "/api/send_message", 
            "revise_resume": "/api/revise_resume",
            "get_curated_resume": "/api/get_curated_resume"
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("Server Starting...")
    uvicorn.run("main:app", host="0.0.0.0", port=3003, reload=True)