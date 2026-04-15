"""
API Routes for Human Review Queue.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List
from datetime import datetime

from app.models.database import ReviewQueue, Prescription, ExtractionFeedback
from app.models.schemas import ReviewResolveRequest, ReviewQueueItem
from app.dependencies import get_db

router = APIRouter(prefix="/review", tags=["review"])

@router.get("/queue")
async def get_review_queue(
    status: str = "pending",
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    query = select(ReviewQueue).where(ReviewQueue.status == status).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    return items

@router.post("/{review_id}/resolve")
async def resolve_review(
    review_id: int,
    request: ReviewResolveRequest,
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch review entry
    query = select(ReviewQueue).where(ReviewQueue.id == review_id)
    result = await db.execute(query)
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review entry not found")

    # 2. Update Prescription Data
    p_query = select(Prescription).where(Prescription.id == review.prescription_id)
    p_result = await db.execute(p_query)
    prescription = p_result.scalar_one_or_none()
    
    if prescription:
        # Simplified: Update final_result with corrected data
        new_result = prescription.final_result.copy() if prescription.final_result else {}
        new_result["doctor_extraction"] = request.corrected_doctor.model_dump()
        
        # Merge medicines is more complex, here we just replace for simplicity
        # A production system would track field-level diffs
        new_result["medicines"] = [m.model_dump() for m in request.corrected_medicines]
        new_result["needs_review"] = False
        
        prescription.final_result = new_result
        prescription.status = "completed"
        
        # 3. Insert Feedback for training/analytics
        # (Compare old vs new and insert into extraction_feedback)
        # For brevity, we just log the resolution
        feedback = ExtractionFeedback(
            prescription_id=review.prescription_id,
            field_name="manual_resolution",
            correct_value="resolved"
        )
        db.add(feedback)

    # 4. Finalize review entry
    review.status = "resolved"
    review.resolved_at = datetime.now()
    review.resolution = request.model_dump()

    await db.commit()
    return {"message": "resolved"}
