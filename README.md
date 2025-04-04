# Resume Roaster API

[![Organization](https://img.shields.io/badge/Organization-LucknowAILabs-blue?style=for-the-badge&logo=github)](https://github.com/LucknowAI)

A FastAPI application for analyzing resumes using Google's Gemini vision models. This API provides functionalities to upload, process, and analyze PDF resumes with AI-powered feedback.

## Features implemented here

- PDF resume upload and processing
- Text extraction from PDFs
- PDF-to-image conversion for visual analysis
- Resume analysis using Google's Gemini 2.0 Flash vision model (currently, may change in future)
- Session management for tracking user interactions
- Customizable analysis prompts

## Requirements

- Python 3.7+
- pydantic
- PyMuPDF
- PyPDF2
- google-genai
- uvicorn
- python-dotenv
- fastapi
- python-multipart


## Installation

1. Clone the repository:
   ```
   git clone <paste_repository_URL>
   cd resume_roaster
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with your Google Gemini API key:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

## Usage

### Starting the Server

Run the application with uvicorn:

```
python main.py
```

The API will be available at `http://localhost:8000`.

Open the `index.html` file for the UI or you can make yours using following API docs.

### API Endpoints

#### Health Check
```
GET /
```
Returns the status of the API.

#### Upload Resume
```
POST /upload
```
Upload a PDF resume for processing. It extracts text and converts the PDF to images.

**Required**: PDF file in the request body.

**Optional**: `session_id` header to associate with an existing session.

**Returns**: Session ID, number of pages, and extracted text.

#### Analyze Resume
```
POST /analyze
```
Analyzes a previously uploaded resume using the Gemini vision model.

**Optional**: 
- `prompt` parameter to customize the analysis request (A default prompt is given to generate responce in Bhojpuri.)
- `session_id` header to specify which session to analyze

**Returns**: Session ID and detailed analysis of the resume.

#### Get Session Information
```
GET /session
```
Retrieves information about the current session.

**Optional**: `session_id` header to specify which session to check.

**Returns**: Session details including creation time and processing status.

## Project Structure

```
resume-analyzer-api/
├── main.py        # Main application file
├── index.html     # basic UI for using the API
├── .env           # Environment variables (API keys)
├── app.log        # Application logs
├── uploads/       # Directory for storing uploaded files
│   └── [session_id]/
│       ├── resume.pdf
│       └── images/
│           ├── page_1.png
│           ├── page_2.png
│           └── ...
```

## Default Analysis Prompt

The default analysis prompt is configured to provide feedback in a humorous Bhojpuri-Hindi style, but you can customize this when making API calls to the `/analyze` endpoint.

## Error Handling

The API implements comprehensive error handling and logging for troubleshooting issues with file uploads, processing, and analysis.

## Security Considerations

- For production use, replace the CORS `allow_origins=["*"]` with specific allowed origins
- Implement proper authentication mechanisms before deployment
- Consider adding rate limiting for the API endpoints
- No database is used to store session details, you can configure one if you want

## License

Apache-2.0 license

## Contributing

This is an open project so, you can contribute whatever you want, whether it is UI improvement or any functionality addition.