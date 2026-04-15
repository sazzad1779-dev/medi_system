"""
Layer 5 Orchestrator: Prescription Processing Pipeline
Orchestrates all layers from image input to database matching and storage.
Designed to run in background jobs.
"""

import time
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import Prescription, ReviewQueue
from app.models.schemas import DoctorExtracted, MedicineExtracted, FinalResult, DoctorMatch, MedicineMatch
from app.core.preprocessing import preprocess_image
from app.services.vlm_service import VLMService
from app.services.cloud_fallback_service import CloudFallbackService
from app.core.normalisation import normalize_extraction
from app.services.embedding_service import EmbeddingService
from app.services.doctor_matcher import DoctorMatcher
from app.services.medicine_matcher import MedicineMatcher
from app.utils.confidence import compute_overall_confidence
from app.config import settings

class PrescriptionPipeline:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.vlm_service = VLMService()
        self.cloud_service = CloudFallbackService()
        self.embedding_service = EmbeddingService()
        self.doctor_matcher = DoctorMatcher(db_session, self.embedding_service)
        self.medicine_matcher = MedicineMatcher(db_session, self.embedding_service)

    async def process(self, prescription_id: UUID):
        start_time = time.time()
        logging.info(f"Starting pipeline for prescription {prescription_id}")

        try:
            # 1. Load record
            query = select(Prescription).where(Prescription.id == prescription_id)
            result = await self.db.execute(query)
            prescription = result.scalar_one_or_none()
            if not prescription:
                logging.error(f"Prescription {prescription_id} not found in DB")
                return

            prescription.status = "processing"
            await self.db.commit()

            # 2. Preprocessing
            pre_res = preprocess_image(prescription.image_path)

            # 3. VLM Extraction
            raw_data, vlm_conf = await self.vlm_service.extract(pre_res.preprocessed_path)
            model_used = settings.VLLM_MODEL_NAME

            # 4. Cloud Fallback if needed
            if vlm_conf < settings.CLOUD_FALLBACK_THRESHOLD and settings.CLOUD_FALLBACK_ENABLED:
                raw_data, fallback_conf = await self.cloud_service.extract(pre_res.preprocessed_path)
                vlm_conf = fallback_conf
                model_used = settings.OPENAI_MODEL

            # 5. Normalization
            norm_data = normalize_extraction(raw_data)
            
            # 6. Database Matching
            doctor_extracted = DoctorExtracted(**norm_data["doctor"])
            medicines_extracted = [MedicineExtracted(**m) for m in norm_data["medicines"]]
            
            doctor_match = await self.doctor_matcher.match(doctor_extracted)
            medicine_matches = await self.medicine_matcher.match_all(medicines_extracted)
            
            # 7. Overall Confidence
            overall_conf = compute_overall_confidence(
                extraction_conf=vlm_conf,
                doctor_conf=doctor_match.confidence,
                medicine_confs=[m.confidence for m in medicine_matches]
            )

            # 8. Human Review Flagging
            needs_review = False
            review_reason = None
            
            if overall_conf < settings.HUMAN_REVIEW_THRESHOLD:
                needs_review = True
                review_reason = f"Low overall confidence: {overall_conf:.2f}"
            elif any(not m.matched for m in medicine_matches):
                needs_review = True
                review_reason = "Unmatched medicines found"
            elif not doctor_match.matched and vlm_conf < 0.80:
                needs_review = True
                review_reason = "Doctor not found with low extraction confidence"

            # 9. Assembly
            res_medicines = []
            for ext, match in zip(medicines_extracted, medicine_matches):
                merged = ext.model_dump()
                merged.update(match.model_dump())
                res_medicines.append(merged)

            final_result = {
                "prescription_id": str(prescription_id),
                "doctor_extraction": doctor_extracted.model_dump(),
                "doctor_match": doctor_match.model_dump(),
                "medicines": res_medicines,
                "overall_confidence": overall_conf,
                "needs_review": needs_review,
                "review_reason": review_reason,
                "model_used": model_used,
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }

            # 10. Persist results
            prescription.raw_vlm_output = raw_data
            prescription.extracted_data = norm_data
            prescription.final_result = final_result
            prescription.overall_confidence = overall_conf
            prescription.needs_review = needs_review
            prescription.model_used = model_used
            prescription.processing_time_ms = final_result["processing_time_ms"]
            prescription.status = "review_required" if needs_review else "completed"
            
            if needs_review:
                review_entry = ReviewQueue(
                    prescription_id=prescription_id,
                    reason=review_reason,
                    confidence_score=overall_conf,
                    status="pending"
                )
                self.db.add(review_entry)

            await self.db.commit()
            logging.info(f"Pipeline completed for {prescription_id} in {final_result['processing_time_ms']}ms")

        except Exception as e:
            logging.error(f"Pipeline failed for {prescription_id}: {str(e)}", exc_info=True)
            if 'prescription' in locals():
                prescription.status = "failed"
                prescription.error_message = str(e)
                await self.db.commit()

async def run_pipeline(prescription_id: UUID):
    from app.dependencies import async_session
    async with async_session() as db:
        pipeline = PrescriptionPipeline(db)
        await pipeline.process(prescription_id)
