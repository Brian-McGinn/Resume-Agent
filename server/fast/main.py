from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from services.llm_service import LLMService
from services.rag_service import setEmbeddings
from services.agent import AgentService
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import json
import logging
from typing import Generator

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()
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
async def automate():
    """
    Begin the automated resume agent.
    """
    try:
        result = await agent_service.automate()
        if result:
            return MessageResponse(message="Automation completed successfully")
        else:
            return MessageResponse(message="Automation failed")
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
            "revise_resume": "/api/revise_resume"
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("Server Starting...")
    uvicorn.run("main:app", host="0.0.0.0", port=3003, reload=True)