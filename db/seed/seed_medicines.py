"""
Seed script to load DGDA medicine data from a CSV file.
Accepts a CSV path and populates the database with embeddings.
"""

import asyncio
import csv
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Add parent dir to path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.models.database import Medicine, Base
from app.services.embedding_service import EmbeddingService
from app.config import settings

async def seed_medicines(csv_path: str):
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    embedding_service = EmbeddingService(provider_type="local")
    
    count = 0
    async with async_session() as session:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                dgda_id = row.get('dgda_id')
                brand = row.get('brand_name')
                generic = row.get('generic_name')
                form = row.get('dosage_form')
                
                # Generate embedding for: brand + generic + form
                embed_text = f"{brand} {generic} {form}"
                embedding = await embedding_service.embed(embed_text)
                
                # Check for existing
                query = select(Medicine).where(Medicine.dgda_id == dgda_id)
                result = await session.execute(query)
                existing = result.scalar_one_or_none()
                
                if existing:
                    # Update
                    existing.brand_name = brand
                    existing.brand_name_bangla = row.get('brand_name_bangla')
                    existing.generic_name = generic
                    existing.atc_code = row.get('atc_code')
                    existing.dosage_form = form
                    existing.strength = row.get('strength')
                    existing.manufacturer = row.get('manufacturer')
                    existing.name_embedding = embedding
                else:
                    # Insert
                    new_med = Medicine(
                        dgda_id=dgda_id,
                        brand_name=brand,
                        brand_name_bangla=row.get('brand_name_bangla'),
                        generic_name=generic,
                        atc_code=row.get('atc_code'),
                        dosage_form=form,
                        strength=row.get('strength'),
                        manufacturer=row.get('manufacturer'),
                        name_embedding=embedding
                    )
                    session.add(new_med)
                
                count += 1
                if count % 100 == 0:
                    print(f"Processed {count} medicines...")
                    await session.commit()
            
            await session.commit()
            print(f"Done! Seeded {count} medicines.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python seed_medicines.py <path_to_csv>")
    else:
        asyncio.run(seed_medicines(sys.argv[1]))
