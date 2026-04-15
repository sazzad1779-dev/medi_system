from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, UUID, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid
import datetime

class Base(DeclarativeBase):
    pass

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bmdc_reg = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    full_name_bangla = Column(String(255))
    degree = Column(Text)
    specialty = Column(String(255))
    institution = Column(String(255))
    phone = Column(String(50))
    address = Column(Text)
    
    # Vector column for name search (3072 dimensions for Gemini Large)
    name_embedding = Column(Vector(3072))
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dgda_id = Column(String(100), unique=True, index=True)
    brand_name = Column(String(255), nullable=False, index=True)
    generic_name = Column(String(255), index=True)
    atc_code = Column(String(50))
    dosage_form = Column(String(100))
    strength = Column(String(100))
    
    # Vector column for brand/generic search
    name_embedding = Column(Vector(3072))
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_path = Column(String(511), nullable=False)
    image_hash = Column(String(64), index=True)
    status = Column(String(50), default="pending", index=True) # pending, processing, completed, review_required, failed
    
    # Results
    raw_vlm_output = Column(JSON)
    extracted_data = Column(JSON) # Structured Pydantic data
    final_result = Column(JSON) # Fully matched data
    
    overall_confidence = Column(Float)
    model_used = Column(String(100))
    processing_time_ms = Column(Integer)
    error_message = Column(Text)
    needs_review = Column(Boolean, default=False)
    
    priority = Column(String(20), default="normal")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class ReviewQueue(Base):
    __tablename__ = "review_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prescription_id = Column(UUID(as_uuid=True), ForeignKey("prescriptions.id"))
    status = Column(String(20), default="pending") # pending, reviewed, dismissed
    reason = Column(Text)
    confidence_score = Column(Float)
    
    assigned_to = Column(String(100))
    resolved_at = Column(DateTime)
    resolution = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    
    prescription = relationship("Prescription")

class ExtractionFeedback(Base):
    __tablename__ = "extraction_feedback"

    id = Column(Integer, primary_key=True)
    prescription_id = Column(UUID(as_uuid=True), ForeignKey("prescriptions.id"))
    field_name = Column(String(100))
    raw_value = Column(Text)
    correct_value = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

