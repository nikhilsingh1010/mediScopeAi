from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from ..auth.route import authenticate
from .vectorstore import load_vectorstore
import uuid
from typing import List
from ..config.db import reports_collection
import logging

logger = logging.getLogger(__name__)

router=APIRouter(prefix="/reports",tags=["reports"])

@router.post("/upload")
async def upload_reports(user=Depends(authenticate),files:List[UploadFile]=File(...)):
    if user["role"] !="patient":
        raise HTTPException(status_code=403,detail="Only patients can upload reports for diagnosis")
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Validate file types
    for file in files:
        if not file.filename:
            raise HTTPException(status_code=400, detail="One or more files have no filename")
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF file")
    
    doc_id = str(uuid.uuid4())
    
    try:
        await load_vectorstore(files, uploaded=user["username"], doc_id=doc_id)
        return {
            "message": "Uploaded and indexed successfully",
            "doc_id": doc_id,
            "files_uploaded": len(files)
        }
    except ValueError as e:
        logger.error(f"Upload validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to upload and process files: {str(e)}"
        )