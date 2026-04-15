"""
Unit tests for the Normalisation module.
"""

import pytest
from app.core.normalisation import normalize_extraction

def test_frequency_normalization():
    raw_data = {
        "doctor": {"raw_name": "Dr. Rahim"},
        "medicines": [
            {"brand_name": "Napa", "frequency": "twice daily", "dosage_form": "tab"},
            {"brand_name": "Seclo", "frequency": "once a day", "dosage_form": "cap"}
        ]
    }
    
    normalized = normalize_extraction(raw_data)
    
    assert normalized["medicines"][0]["frequency"] == "BD"
    assert normalized["medicines"][0]["frequency_per_day"] == 2
    assert normalized["medicines"][0]["dosage_form"] == "Tablet"
    
    assert normalized["medicines"][1]["frequency"] == "OD"
    assert normalized["medicines"][1]["frequency_per_day"] == 1
    assert normalized["medicines"][1]["dosage_form"] == "Capsule"

def test_doctor_name_normalization():
    raw_data = {
        "doctor": {"raw_name": "Prof. Dr. Karim Ahmed", "bmdc_reg": "A-12345"},
        "medicines": []
    }
    
    normalized = normalize_extraction(raw_data)
    
    # Prefix removed, title cased
    assert normalized["doctor"]["normalized_name"] == "Karim Ahmed"
    assert normalized["doctor"]["bmdc_reg"] == "A-12345"

def test_script_detection():
    raw_data = {
        "doctor": {"raw_name": "ডাঃ কুদ্দুস (Dr. Kuddus)"},
        "medicines": []
    }
    
    normalized = normalize_extraction(raw_data)
    assert normalized["doctor"]["script_detected"] == "bangla"
