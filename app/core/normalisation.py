from typing import Dict, Any, List
import logging

def normalize_extraction(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standardizes the raw JSON from various VLM models into a consistent internal schema.
    Handles field name variations (e.g., 'doctor_name' vs 'doc_name').
    """
    # 1. Normalize Doctor
    doctor_raw = raw_data.get("doctor", {}) or {}
    doctor = {
        "full_name": doctor_raw.get("full_name") or doctor_raw.get("name") or doctor_raw.get("doctor_name"),
        "bmdc_reg": doctor_raw.get("bmdc_reg") or doctor_raw.get("registration_no") or doctor_raw.get("reg"),
        "specialty": doctor_raw.get("specialty"),
        "institution": doctor_raw.get("institution") or doctor_raw.get("hospital")
    }

    # 2. Normalize Medicines
    medicines_raw = raw_data.get("medicines") or raw_data.get("medications") or []
    medicines = []
    
    for med in medicines_raw:
        medicines.append({
            "brand_name": med.get("brand_name") or med.get("name") or med.get("brand"),
            "generic_name": med.get("generic_name") or med.get("generic"),
            "dosage_form": med.get("dosage_form") or med.get("type"),
            "strength": med.get("strength"),
            "dosage_instruction": med.get("dosage_instruction") or med.get("instructions") or med.get("dose"),
            "duration": med.get("duration") or med.get("days")
        })

    return {
        "doctor": doctor,
        "medicines": medicines,
        "date": raw_data.get("date")
    }
