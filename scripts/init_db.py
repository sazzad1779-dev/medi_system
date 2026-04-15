
import asyncio
import sys
from sqlalchemy import text
from app.dependencies import engine
from app.models.database import Base

async def init_db():
    print("Initializing database...")
    async with engine.begin() as conn:
        # 1. Enable extensions
        print("Enabling extensions (vector, pg_trgm)...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        
        # 2. Create tables
        print("Recreating tables (dropping first)...")
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    print("Database initialization complete.")

if __name__ == "__main__":
    asyncio.run(init_db())
