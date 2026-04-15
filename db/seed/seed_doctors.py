"""
Seed script to load BMDC doctor data from a CSV file.
Accepts a CSV path and populates the database with embeddings.
"""

import asyncio
import csv
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update

# Add parent dir to path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.models.database import Doctor, Base
from app.services.embedding_service import EmbeddingService
from app.config import settings

async def seed_doctors(csv_path: str):
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    embedding_service = EmbeddingService(provider_type="local") # Local for seeding usually better
    
    # Ensure tables exist (optional if using alembic)
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    count = 0
    async with async_session() as session:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                reg = row.get('bmdc_reg')
                name = row.get('full_name')
                
                # Generate embedding
                embedding = await embedding_service.embed(name)
                
                # Check for existing
                query = select(Doctor).where(Doctor.bmdc_reg == reg)
                result = await session.execute(query)
                existing = result.scalar_one_or_none()
                
                if existing:
                    # Update
                    existing.full_name = name
                    existing.full_name_bangla = row.get('full_name_bangla')
                    existing.degree = row.get('degree')
                    existing.specialty = row.get('specialty')
                    existing.institution = row.get('institution')
                    existing.phone = row.get('phone')
                    existing.address = row.get('address')
                    existing.name_embedding = embedding
                else:
                    # Insert
                    new_doc = Doctor(
                        bmdc_reg=reg,
                        full_name=name,
                        full_name_bangla=row.get('full_name_bangla'),
                        degree=row.get('degree'),
                        specialty=row.get('specialty'),
                        institution=row.get('institution'),
                        phone=row.get('phone'),
                        address=row.get('address'),
                        name_embedding=embedding
                    )
                    session.add(new_doc)
                
                count += 1
                if count % 100 == 0:
                    print(f"Processed {count} doctors...")
                    await session.commit()
            
            await session.commit()
            print(f"Done! Seeded {count} doctors.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python seed_doctors.py <path_to_csv>")
    else:
        asyncio.run(seed_doctors(sys.argv[1]))
