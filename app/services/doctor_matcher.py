"""
Layer 4 Sub-layer A: Doctor Matching Service
Matches extracted doctor info against the BMDC database.
"""

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import Doctor
from app.models.schemas import DoctorExtracted, DoctorMatch
from app.services.embedding_service import EmbeddingService
from app.config import settings

class DoctorMatcher:
    def __init__(self, db_session: AsyncSession, embedding_service: EmbeddingService):
        self.db = db_session
        self.embedding_service = embedding_service

    async def match(self, extracted: DoctorExtracted) -> DoctorMatch:
        """
        Orchestrates matching: Exact -> Fuzzy -> Vector.
        """
        # Step 1: Exact BMDC Match
        if extracted.bmdc_reg:
            query = select(Doctor).where(
                Doctor.bmdc_reg == extracted.bmdc_reg,
                Doctor.is_active == True
            )
            result = await self.db.execute(query)
            doctor = result.scalar_one_or_none()
            if doctor:
                return DoctorMatch(
                matched=True,
                doctor_id=doctor.id,
                bmdc_reg=doctor.bmdc_reg,
                full_name=doctor.full_name,
                degree=doctor.degree,
                specialty=doctor.specialty,
                match_method="exact_bmdc",
                confidence=1.0
            )

        # Step 2: Fuzzy Name Match (trgm)
        if extracted.normalized_name:
            # PostgreSQL pg_trgm similarity
            # SELECT *, similarity(full_name, :name) as sim FROM doctors ...
            query = select(Doctor, func.similarity(Doctor.full_name, extracted.normalized_name).label("sim")).where(
                func.similarity(Doctor.full_name, extracted.normalized_name) >= 0.75,
                Doctor.is_active == True
            ).order_by(text("sim DESC")).limit(1)
            
            result = await self.db.execute(query)
            row = result.first()
            if row:
                doctor, sim = row
                return DoctorMatch(
                    matched=True,
                    doctor_id=doctor.id,
                    bmdc_reg=doctor.bmdc_reg,
                    full_name=doctor.full_name,
                    degree=doctor.degree,
                    specialty=doctor.specialty,
                    match_method="fuzzy_name",
                    confidence=float(sim)
                )

        # Step 3: Vector Similarity Match
        if extracted.normalized_name:
            embedding = await self.embedding_service.embed(extracted.normalized_name)
            # PGVector cosine distance (<=>)
            query = select(Doctor, Doctor.name_embedding.cosine_distance(embedding).label("dist")).where(
                Doctor.is_active == True
            ).order_by(text("dist")).limit(1)
            
            result = await self.db.execute(query)
            row = result.first()
            if row:
                doctor, dist = row
                confidence = 1.0 - float(dist)
                if confidence >= 0.65:
                    return DoctorMatch(
                        matched=True,
                        doctor_id=doctor.id,
                        bmdc_reg=doctor.bmdc_reg,
                        full_name=doctor.full_name,
                        degree=doctor.degree,
                        specialty=doctor.specialty,
                        match_method="vector",
                        confidence=confidence
                    )

        # Fallback: No Match
        return DoctorMatch(
            matched=False,
            confidence=0.0,
            match_method="no_match"
        )
