import os
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import uvicorn

from cv_parser import CVParser
from email_service import EmailService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="MCP Server", description="CV Chat and Email Notification Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global services
cv_parser = CVParser()
email_service = EmailService()

# Load sample CV if no CV is uploaded
SAMPLE_CV_PATH = "sample_cv.txt"
if not cv_parser.is_cv_loaded():
    if os.path.exists(SAMPLE_CV_PATH):
        cv_parser.load_cv(SAMPLE_CV_PATH)

# Data models
class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    confidence: float
    source_sections: List[str]

class EmailRequest(BaseModel):
    recipient: EmailStr
    subject: str
    body: str

class EmailResponse(BaseModel):
    success: bool
    message: str

class MCPServerStatus(BaseModel):
    status: str
    cv_loaded: bool
    email_configured: bool

@app.get("/", response_model=MCPServerStatus)
async def root():
    """Root endpoint showing MCP server status"""
    return MCPServerStatus(
        status="running",
        cv_loaded=cv_parser.is_cv_loaded(),
        email_configured=email_service.is_configured()
    )

@app.post("/upload-cv")
async def upload_cv(file: UploadFile = File(...)):
    """Upload and parse a CV/resume file"""
    try:
        # Save uploaded file temporarily
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)
        
        # Parse the CV
        success = cv_parser.load_cv(temp_path)
        
        # Clean up temp file
        os.unlink(temp_path)
        
        if success:
            return {"message": "CV uploaded and parsed successfully", "filename": file.filename}
        else:
            raise HTTPException(status_code=400, detail="Failed to parse CV file")
            
    except Exception as e:
        logger.error(f"Error uploading CV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing CV: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat_about_cv(request: ChatRequest):
    """Chat about the uploaded CV"""
    try:
        if not cv_parser.is_cv_loaded():
            raise HTTPException(status_code=400, detail="No CV loaded. Please upload a CV first.")
        
        answer, confidence, sources = cv_parser.answer_question(request.question)
        
        return ChatResponse(
            answer=answer,
            confidence=confidence,
            source_sections=sources
        )
        
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.post("/send-email", response_model=EmailResponse)
async def send_email(request: EmailRequest):
    """Send an email notification"""
    try:
        success, message = email_service.send_email(
            recipient=request.recipient,
            subject=request.subject,
            body=request.body
        )
        
        return EmailResponse(success=success, message=message)
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")

@app.get("/cv-info")
async def get_cv_info():
    """Get information about the loaded CV"""
    try:
        if not cv_parser.is_cv_loaded():
            raise HTTPException(status_code=400, detail="No CV loaded")
        
        return cv_parser.get_cv_summary()
        
    except Exception as e:
        logger.error(f"Error getting CV info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting CV info: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)