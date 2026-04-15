"""
API Routes for Prescription Upload and Retrieval.
"""

import os
import hashlib
import aiofiles
from uuid import uuid4
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import Prescription
from app.models.schemas import PrescriptionSubmitResponse, FinalResult
from app.dependencies import get_db
from app.core.pipeline import run_pipeline
from app.config import settings

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])

async def calculate_hash(file: UploadFile) -> str:
    sha256 = hashlib.sha256()
    while content := await file.read(8192):
        sha256.update(content)
    await file.seek(0)
    return sha256.hexdigest()

@router.post("/", response_model=PrescriptionSubmitResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_prescription(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    priority: str = "normal",
    callback_url: str = None,
    db: AsyncSession = Depends(get_db)
):
    # 1. Validation
    if file.content_type not in ["image/jpeg", "image/png", "application/pdf"]:
        raise HTTPException(status_code=422, detail="Unsupported file type. Use JPEG, PNG or PDF.")
    
    # 2. Duplicate Check
    file_hash = await calculate_hash(file)
    query = select(Prescription).where(Prescription.image_hash == file_hash)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        return PrescriptionSubmitResponse(
            prescription_id=str(existing.id),
            status=existing.status,
            message="Duplicate prescription found. Returning existing record."
        )

    # 3. Save File
    p_id = uuid4()
    ext = file.filename.split(".")[-1]
    filename = f"{p_id}.{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    async with aiofiles.open(file_path, "wb") as buffer:
        while content := await file.read(8192):
            await buffer.write(content)

    # 4. Create DB Entry
    new_prescription = Prescription(
        id=p_id,
        image_path=file_path,
        image_hash=file_hash,
        status="pending"
    )
    db.add(new_prescription)
    await db.commit()

    # 5. Queue Background Task
    background_tasks.add_task(run_pipeline, p_id)

    return PrescriptionSubmitResponse(
        prescription_id=str(p_id),
        status="pending",
        message="Prescription queued for processing"
    )

@router.get("/{prescription_id}")
async def get_prescription(
    prescription_id: str,
    db: AsyncSession = Depends(get_db)
):
    query = select(Prescription).where(Prescription.id == prescription_id)
    result = await db.execute(query)
    prescription = result.scalar_one_or_none()
    
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    response = {
        "prescription_id": str(prescription.id),
        "status": prescription.status,
        "created_at": prescription.created_at.isoformat(),
        "processing_time_ms": prescription.processing_time_ms
    }

    if prescription.status in ["completed", "review_required"]:
        response["result"] = prescription.final_result
    elif prescription.status == "failed":
        response["error_message"] = prescription.error_message

    return response
