# MCP Server Project

# Overview
A Model Context Protocol (MCP) server that provides CV/resume chat functionality and email notifications through a FastAPI backend with a simple HTML frontend.

# Features Completed
✅ CV/Resume parsing (PDF, DOCX, TXT formats)
✅ Natural language Q&A about CV content
✅ Email notification endpoint (configurable)
✅ Simple HTML frontend with real-time interaction
✅ RESTful API endpoints


## Project Structure
├── main.py                 # Main FastAPI server
├── cv_parser.py            # CV parsing and NLP functionality
├── email_service.py        # Email sending service
├── serve_frontend.py       # Simple frontend server
├── sample_cv.txt          # Sample CV for testing
├── frontend/
│   └── index.html         # Frontend interface
├── pyproject.toml         # Python dependencies
└── uv.lock               # Dependency lock file

## Current Status
Server: Running on port 5000
CV Processing: Working with sample CV loaded
Email Service: Functional but requires configuration
Frontend: HTML interface created and working
API Endpoints
GET / - Server status
POST /upload-cv - Upload CV file
POST /chat - Ask questions about CV
POST /send-email - Send email notifications
GET /cv-info - Get CV summary


## Recent Changes
Installed all required Python dependencies
Created complete MCP server with FastAPI
Implemented CV parsing with spaCy and NLTK
Added email service with SendGrid/SMTP support
Built responsive HTML frontend with Tailwind CSS
Configured workflow for auto-restart


## User Preferences
Uses Python FastAPI for backend
Includes comprehensive error handling
Responsive frontend design
Modular code structure


## Next Steps (Optional)
Configure email credentials for live email sending
Add more sophisticated NLP for better CV understanding
Implement user authentication
Add database for storing CV data