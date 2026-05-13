import os
import io
import json
import base64
import traceback
from typing import List, Optional, Dict, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
from langchain.tools import tool
from pydantic import BaseModel, Field
from pypdf import PdfReader
from docx import Document
from groq import Groq

def get_all_subfolder_ids(service, parent_id):
    """Recursively find all subfolder IDs under a parent folder."""
    folder_ids = [parent_id]
    try:
        results = service.files().list(
            q=f"'{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
            fields="files(id)"
        ).execute()
        for folder in results.get('files', []):
            folder_ids.extend(get_all_subfolder_ids(service, folder['id']))
    except Exception as e:
        print(f"Error fetching subfolders: {e}")
    return folder_ids

def get_drive_service():
    """Authenticates and returns the Google Drive service."""
    service_account_info = os.getenv("SERVICE_ACCOUNT_JSON")
    if service_account_info:
        info = json.loads(service_account_info)
        credentials = service_account.Credentials.from_service_account_info(info)
    else:
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "data/service-account.json")
        if not os.path.exists(creds_path):
            raise FileNotFoundError(f"Service account file not found at {creds_path}")
        credentials = service_account.Credentials.from_service_account_file(
            creds_path, scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )
    return build("drive", "v3", credentials=credentials)

class DriveSearchInput(BaseModel):
    search_query: str = Field(description="The Google Drive search string.")

@tool("search_drive", args_schema=DriveSearchInput)
def search_drive(search_query: str) -> str:
    """Find files by name, type, or content."""
    try:
        service = get_drive_service()
        folder_id = os.getenv("DRIVE_FOLDER_ID")
        # AI-Proofing: If the agent sends just a name (no operators), fix it for them
        if search_query and "contains" not in search_query and "=" not in search_query and "mimeType" not in search_query:
            search_query = f"name contains '{search_query}'"

        # Try folder-specific search first
        if folder_id:
            all_folders = get_all_subfolder_ids(service, folder_id)
            folder_filter = " or ".join([f"'{fid}' in parents" for fid in all_folders])
            if search_query:
                final_query = f"({folder_filter}) and ({search_query}) and trashed = false"
            else:
                final_query = f"({folder_filter}) and trashed = false"
        else:
            final_query = f"({search_query}) and trashed = false" if search_query else "trashed = false"
        
        results = service.files().list(
            q=final_query,
            spaces='drive',
            fields='files(id, name, mimeType, modifiedTime, webViewLink, size)',
            pageSize=20,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True
        ).execute()
        files = results.get('files', [])
        
        if not files and folder_id:
            global_query = f"({search_query}) and trashed = false" if search_query else "trashed = false"
            results = service.files().list(q=global_query, spaces='drive', fields='files(id, name, mimeType, modifiedTime, webViewLink, size)', pageSize=20, includeItemsFromAllDrives=True, supportsAllDrives=True).execute()
            files = results.get('files', [])
            
        if not files: return "No files found."
        
        output = "I found the following files:\n"
        for file in files:
            output += f"- **{file['name']}** (ID: {file['id']}, Type: {file['mimeType']})\n  Link: {file.get('webViewLink')}\n"
        return output
    except Exception as e: return f"Error: {str(e)}"

class FileInput(BaseModel):
    file_id: str = Field(description="The unique ID of the file.")
    mime_type: str = Field(description="The mimeType of the file.")

@tool("read_file_content", args_schema=FileInput)
def read_file_content(file_id: str, mime_type: str) -> str:
    """Read text from a Google Doc, Sheet, PDF, Word, or Text file."""
    try:
        service = get_drive_service()
        if "application/pdf" in mime_type:
            pdf_reader = PdfReader(io.BytesIO(service.files().get_media(fileId=file_id).execute()))
            content = "\n".join([p.extract_text() for p in pdf_reader.pages])
        elif "wordprocessingml.document" in mime_type:
            doc = Document(io.BytesIO(service.files().get_media(fileId=file_id).execute()))
            content = "\n".join([p.text for p in doc.paragraphs])
        elif "google-apps.document" in mime_type:
            content = service.files().export(fileId=file_id, mimeType="text/plain").execute().decode('utf-8')
        elif "google-apps.spreadsheet" in mime_type:
            content = service.files().export(fileId=file_id, mimeType="text/csv").execute().decode('utf-8')
        else:
            content = service.files().get_media(fileId=file_id).execute().decode('utf-8', errors='ignore')
        return f"Content:\n---\n{content[:5000]}"
    except Exception as e: return f"Error: {str(e)}"

class ImageInput(BaseModel):
    file_id: str = Field(description="The ID of the image to analyze.")

@tool("describe_image", args_schema=ImageInput)
def describe_image(file_id: str) -> str:
    """Describe what is in an image using Vision AI."""
    try:
        service = get_drive_service()
        # 1. Download image
        image_data = service.files().get_media(fileId=file_id).execute()
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # 2. Call Groq Vision
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image in detail."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            temperature=0,
            max_tokens=1024,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error analyzing image: {str(e)}"
