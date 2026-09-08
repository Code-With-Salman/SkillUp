# ---------------------------
# FILE: parser.py
# ---------------------------

import fitz # PyMuPDF
from docx import Document
import io # Required for docx to read content bytes as a stream
from fastapi import UploadFile # ADDED: Import UploadFile from fastapi


# Helper to extract text from uploaded job/resume file
async def parse_job_file(uploaded_file: UploadFile, manual_text: str): # Added type hint for uploaded_file
    """
    Extracts text from an uploaded file (PDF, DOCX, TXT) or uses manual text input.
    Prioritizes manual text if provided.
    """
    if manual_text and manual_text.strip():
        return manual_text.strip()

    if uploaded_file is None or not uploaded_file.filename:
        return "" # No file uploaded and no manual text

    ext = uploaded_file.filename.split(".")[-1].lower()
    content_bytes = await uploaded_file.read() # Read file content as bytes

    if ext == "pdf":
        return extract_text_from_pdf(content_bytes)
    elif ext == "docx":
        return extract_text_from_docx(content_bytes)
    elif ext == "txt":
        return content_bytes.decode('utf-8', errors='ignore') # Decode txt with utf-8
    else:
        print(f"Unsupported file type for job parsing: {ext}")
        return ""

async def parse_resume_file(resume_file: UploadFile):
    """
    Extracts text from an uploaded resume file (PDF, DOCX, TXT).
    Returns a dictionary with raw_text, suitable for LLM processing.
    """
    if resume_file is None or not resume_file.filename:
        return {"raw_text": ""}

    ext = resume_file.filename.split(".")[-1].lower()
    content_bytes = await resume_file.read()

    text_content = ""
    if ext == "pdf":
        text_content = extract_text_from_pdf(content_bytes)
    elif ext == "docx":
        text_content = extract_text_from_docx(content_bytes)
    elif ext == "txt":
        text_content = content_bytes.decode('utf-8', errors='ignore')
    else:
        print(f"Unsupported file type for resume parsing: {ext}")
        text_content = ""

    return {"raw_text": text_content}


# ---------------------------
# File Readers
# ---------------------------

def extract_text_from_pdf(content_bytes: bytes) -> str:
    """
    Extracts text from PDF content bytes using PyMuPDF (fitz).
    """
    text = ""
    try:
        with fitz.open(stream=content_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        print(f"Extracted {len(text)} characters from PDF.")
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        text = "" # Return empty string on error
    return text

def extract_text_from_docx(content_bytes: bytes) -> str:
    """
    Extracts text from DOCX content bytes using python-docx.
    """
    text = ""
    try:
        file_stream = io.BytesIO(content_bytes) # Wrap bytes in a BytesIO stream
        doc = Document(file_stream)
        text = "\n".join([para.text for para in doc.paragraphs])
        print(f"Extracted {len(text)} characters from DOCX.")
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        text = "" # Return empty string on error
    return text