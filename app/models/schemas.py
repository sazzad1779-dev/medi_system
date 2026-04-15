from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

# --- Extraction Part ---

class DoctorExtracted(BaseModel):
    full_name: Optional[str] = None
    normalized_name: Optional[str] = None
    bmdc_reg: Optional[str] = None
    specialty: Optional[str] = None
    institution: Optional[str] = None

class MedicineExtracted(BaseModel):
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    dosage_form: Optional[str] = None
    strength: Optional[str] = None
    dosage_instruction: Optional[str] = None
    duration: Optional[str] = None

class PrescriptionExtraction(BaseModel):
    doctor: DoctorExtracted
    medicines: List[MedicineExtracted]
    date: Optional[str] = None

# --- Matching Part ---

class DoctorMatch(BaseModel):
    matched: bool
    doctor_id: Optional[UUID] = None
    bmdc_reg: Optional[str] = None
    full_name: Optional[str] = None
    confidence: float
    match_method: str # exact, fuzzy, vector, manual

class MedicineMatch(BaseModel):
    matched: bool
    medicine_id: Optional[UUID] = None
    dgda_id: Optional[str] = None
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    atc_code: Optional[str] = None
    dosage_form: Optional[str] = None
    strength: Optional[str] = None
    confidence: float
    match_method: str # exact, fuzzy, vector, manual

# --- Response / UI Part ---

class FinalMedicine(MedicineExtracted, MedicineMatch):
    pass

class FinalResult(BaseModel):
    prescription_id: str
    doctor_extraction: DoctorExtracted
    doctor_match: DoctorMatch
    medicines: List[FinalMedicine]
    overall_confidence: float
    needs_review: bool
    review_reason: Optional[str] = None
    model_used: str
    processing_time_ms: int

class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

# --- Review Part ---

class ReviewResolveRequest(BaseModel):
    corrected_doctor: DoctorExtracted
    corrected_medicines: List[MedicineExtracted]

class ReviewQueueItem(BaseModel):
    id: UUID
    prescription_id: UUID
    status: str
    reason: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- API Request/Response ---

class PrescriptionSubmitResponse(BaseModel):
    prescription_id: str
    status: str
    message: str

class PrescriptionResponse(BaseModel):
    prescription_id: str
    status: str
    created_at: datetime

    
    class Config:
        from_attributes = True

class PrescriptionDetail(PrescriptionResponse):
    raw_vlm_output: Optional[Dict[str, Any]] = None
    extracted_data: Optional[Dict[str, Any]] = None
    final_result: Optional[Dict[str, Any]] = None
    overall_confidence: Optional[float] = None
    needs_review: bool
    error_message: Optional[str] = None
