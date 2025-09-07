
# ChatApp-MCP

A Model Context Protocol (MCP) server for CV/resume chat and email notifications, built with FastAPI and a simple HTML frontend.

## Features
- CV/Resume parsing (PDF, DOCX, TXT formats)
- Natural language Q&A about CV content using spaCy
- Email notification endpoint (SendGrid or SMTP)
- Responsive HTML frontend (Tailwind CSS)
- RESTful API endpoints
- Secure environment variable management with `.env` and `python-dotenv`

## Project Structure
```
├── main.py                 # Main FastAPI server
├── cv_parser.py            # CV parsing and NLP functionality
├── email_service.py        # Email sending service
├── serve_frontend.py       # Simple frontend server
├── sample_cv.txt           # Sample CV for testing
├── frontend/
│   └── index.html          # Frontend interface
├── .env                    # Environment variables (not in GitHub)
├── .gitignore              # Git ignore file
```

## Setup Instructions
1. Clone the repository.
2. Create a `.env` file with your credentials:
	```
	SENDGRID_API_KEY=your_sendgrid_api_key
	SMTP_SERVER=smtp.gmail.com
	SMTP_PORT=587
	SMTP_USERNAME=your_email@gmail.com
	SMTP_PASSWORD=your_email_password_or_app_password
	FROM_EMAIL=your_email@gmail.com
	```
3. Add `.env` to `.gitignore` to keep credentials private.

4. Install python packages:
	```
    pip install PyPDF2
	pip install fastapi uvicorn pydantic PyPDF2 pdfplumber python-docx spacy nltk sendgrid

	```
5. Run the backend server:
	```
	python main.py
	```
6. Open the index.html file in the browser

## API Endpoints
- `GET /` - Server status
- `POST /upload-cv` - Upload CV file
- `POST /chat` - Ask questions about CV
- `POST /send-email` - Send email notifications
- `GET /cv-info` - Get CV summary

## Security
- All sensitive credentials are stored in `.env` and never pushed to GitHub.
- Uses `python-dotenv` to load environment variables.