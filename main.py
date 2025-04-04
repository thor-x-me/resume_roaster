import os
import fitz
import uuid
import shutil
import PyPDF2
import logging
import uvicorn
from typing import List
from pathlib import Path
from google import genai
from datetime import datetime
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(title="Resume Analyzer API", description="API for analyzing resumes using Gemini vision model")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a directory for storing session data
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# Define models
class SessionData(BaseModel):
    session_id: str
    pdf_path: str = None
    text_data: dict = None
    image_paths: List[str] = []
    created_at: datetime = None
    vision_response: str = None


# In-memory storage for sessions
sessions = {}



def get_data_from_pdf(pdf, session_id):
    """Extract text data from PDF"""
    logger.info(f"Extracting text from PDF for session {session_id}")
    try:
        with open(pdf, "rb") as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            result = {
                "pages": len(reader.pages),
                "text": text,
            }
            logger.info(f"Successfully extracted {len(reader.pages)} pages from PDF")
            return result
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise


def pdf_to_images(pdf_path, session_id):
    """Convert PDF pages to images"""
    logger.info(f"Converting PDF to images for session {session_id}")
    try:
        # Create the output folder if it doesn't exist
        session_dir = UPLOAD_DIR / session_id / "images"
        session_dir.mkdir(exist_ok=True, parents=True)

        # Open the PDF file
        doc = fitz.open(pdf_path)

        image_paths = []
        # Iterate through each page
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)  # Load the page
            pix = page.get_pixmap()  # Render the page as an image

            # Save the image
            image_path = str(session_dir / f"page_{page_num + 1}.png")
            pix.save(image_path)
            image_paths.append(image_path)
            logger.info(f"Saved image {image_path}")

        return image_paths
    except Exception as e:
        logger.error(f"Error converting PDF to images: {str(e)}")
        raise


def get_vision_response(session_id, pdf_path, prompt="Analyze this resume and provide detailed feedback"):
    """Get response from vision model"""
    logger.info(f"Getting vision response for session {session_id}")
    try:
        contents = [prompt]
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)  # Load the page
            pix = page.get_pixmap()  # Render the page as an image
            # Save the image
            image_path = os.path.join(f"uploads/{session_id}/images/", f"page_{page_num + 1}.png")
            pix.save(image_path)
            print(f"Saved {image_path}")
        png_files = [f'uploads/{session_id}/images' + f for f in os.listdir(f'uploads/{session_id}/images') if f.endswith('.png')]
        contents = contents + png_files

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents)

        logger.info(f"Successfully got vision response for session {session_id}")
        return response.text
    except Exception as e:
        logger.error(f"Error getting vision response: {str(e)}")
        raise


# Dependency to get session
async def get_session(session_id: str = Header(None)):
    if not session_id:
        # Create new session if none provided
        session_id = str(uuid.uuid4())
        sessions[session_id] = SessionData(
            session_id=session_id,
            created_at=datetime.now()
        )
        logger.info(f"Created new session: {session_id}")
    elif session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    return sessions[session_id]


# API Routes
@app.post("/upload")
async def upload_resume(
        file: UploadFile = File(...),
        session: SessionData = Depends(get_session)
):
    """Upload a PDF resume and process it"""
    logger.info(f"Processing resume upload for session {session.session_id}")

    if not file.filename.lower().endswith('.pdf'):
        logger.warning(f"Invalid file type uploaded: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        # Create session directory
        session_dir = UPLOAD_DIR / session.session_id
        session_dir.mkdir(exist_ok=True, parents=True)

        # Save the uploaded file
        pdf_path = str(session_dir / "resume.pdf")
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Saved PDF to {pdf_path}")

        # Update session data
        session.pdf_path = pdf_path
        session.created_at = datetime.now()

        # Extract text from PDF
        session.text_data = get_data_from_pdf(pdf_path, session.session_id)

        # Convert PDF to images
        session.image_paths = pdf_to_images(pdf_path, session.session_id)

        return {
            "message": "Resume uploaded and processed successfully",
            "session_id": session.session_id,
            "pages": session.text_data["pages"],
            "text": session.text_data["text"]
        }
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")


@app.post("/analyze")
async def analyze_resume(
        prompt: str = """System: You are a resume analysis expert who communicates in a humorous Bhojpuri-Hindi style. Your task is to analyze the resume text and image provided by the user and give detailed, actionable feedback while making the user laugh.
                    
                    User: I'm uploading my resume (text and image attached). Please analyze it carefully and provide the following in Bhojpuri-Hindi language with humor:
                    
                    1. Identify the major pain points in my resume (formatting, content gaps, weak descriptions, etc.)
                    2. Give specific improvement suggestions for each section
                    3. Point out what's missing that could make my resume stronger
                    4. Highlight any red flags that might make recruiters reject my application
                    5. Suggest better ways to present my skills and achievements
                    
                    Make your feedback entertaining with Bhojpuri idioms, expressions, and humor while still being professional enough that I can use your advice to improve my job prospects. Don't hold back on honest criticism but wrap it in humor so I can laugh while learning!""",

        session: SessionData = Depends(get_session)
):
    """Analyze the uploaded resume using vision model"""
    logger.info(f"Analyzing resume for session {session.session_id}")

    if not session.pdf_path:
        logger.warning(f"No resume found for session {session.session_id}")
        raise HTTPException(status_code=400, detail="Please upload a resume first")

    try:
        # Get vision model response
        session.vision_response = get_vision_response(session.session_id, session.pdf_path, prompt + session.text_data["text"])

        return {
            "session_id": session.session_id,
            "analysis": session.vision_response
        }
    except Exception as e:
        logger.error(f"Error analyzing resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing resume: {str(e)}")


@app.get("/session")
async def get_session_info(session: SessionData = Depends(get_session)):
    """Get information about the current session"""
    logger.info(f"Getting session info for {session.session_id}")

    return {
        "session_id": session.session_id,
        "created_at": session.created_at,
        "has_resume": session.pdf_path is not None,
        "pages": session.text_data["pages"] if session.text_data else None,
        "has_analysis": session.vision_response is not None
    }


@app.get("/")
async def root():
    """API health check endpoint"""
    return {"status": "ok", "message": "Resume Analyzer API is running"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)