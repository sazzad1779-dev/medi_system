"""
Layer 4 Sub-layer B: Medicine Matching Service
Matches extracted medicine info against the DGDA record list.
"""

import asyncio
from typing import List
from sqlalchemy import select, func, text, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import Medicine
from app.models.schemas import MedicineExtracted, MedicineMatch
from app.services.embedding_service import EmbeddingService
from app.config import settings

class MedicineMatcher:
    def __init__(self, db_session: AsyncSession, embedding_service: EmbeddingService):
        self.db = db_session
        self.embedding_service = embedding_service

    async def match_one(self, extracted: MedicineExtracted) -> MedicineMatch:
        """
        Matches a single medicine: Exact -> Fuzzy -> Vector.
        """
        brand_name = extracted.brand_name
        if not brand_name:
            return MedicineMatch(matched=False, confidence=0.0, match_method="no_match")

        # Step 1: Exact Match (Case-insensitive)
        query = select(Medicine).where(
            func.lower(Medicine.brand_name) == brand_name.lower(),
            Medicine.is_active == True
        ).limit(1)
        
        result = await self.db.execute(query)
        medicine = result.scalar_one_or_none()
        if medicine:
            return self._build_match(medicine, "exact", 1.0, extracted)

        # Step 2: Fuzzy Match (pg_trgm) on Brand or Generic Name
        query = select(
            Medicine, 
            func.greatest(
                func.similarity(Medicine.brand_name, brand_name),
                func.similarity(Medicine.generic_name, brand_name)
            ).label("sim")
        ).where(
            or_(
                func.similarity(Medicine.brand_name, brand_name) >= 0.80,
                func.similarity(Medicine.generic_name, brand_name) >= 0.80
            ),
            Medicine.is_active == True
        ).order_by(text("sim DESC")).limit(1)
        
        result = await self.db.execute(query)
        row = result.first()
        if row:
            medicine, sim = row
            return self._build_match(medicine, "fuzzy", float(sim), extracted)

        # Step 3: Vector Similarity
        embed_query = brand_name
        if extracted.generic_name:
            embed_query += f" {extracted.generic_name}"
            
        embedding = await self.embedding_service.embed(embed_query)
        query = select(Medicine, Medicine.name_embedding.cosine_distance(embedding).label("dist")).where(
            Medicine.is_active == True
        ).order_by(text("dist")).limit(1)
        
        result = await self.db.execute(query)
        row = result.first()
        if row:
            medicine, dist = row
            confidence = 1.0 - float(dist)
            if confidence >= 0.75:
                return self._build_match(medicine, "vector", confidence, extracted)

        return MedicineMatch(matched=False, confidence=0.0, match_method="no_match")

    async def match_all(self, medicines: List[MedicineExtracted]) -> List[MedicineMatch]:
        """
        Consistently matches all medicines concurrently.
        """
        tasks = [self.match_one(m) for m in medicines]
        return await asyncio.gather(*tasks)

    def _build_match(self, med: Medicine, method: str, confidence: float, extracted: MedicineExtracted) -> MedicineMatch:
        """
        Internal helper to construct match result and cross-check dosage form.
        """
        # Cross-check dosage form if present
        final_conf = confidence
        if extracted.dosage_form and med.dosage_form:
            if extracted.dosage_form.lower() not in med.dosage_form.lower():
                final_conf -= 0.15
                
        return MedicineMatch(
            matched=True,
            medicine_id=med.id,
            dgda_id=med.dgda_id,
            brand_name=med.brand_name,
            generic_name=med.generic_name,
            atc_code=med.atc_code,
            dosage_form=med.dosage_form,
            strength=med.strength,
            match_method=method,
            confidence=max(0.0, final_conf)
        )
