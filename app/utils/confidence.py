"""
Utility for computing overall prescription confidence scores.
"""

from typing import List, Dict, Any

def compute_overall_confidence(
    extraction_conf: float,
    doctor_conf: float,
    medicine_confs: List[float]
) -> float:
    """
    Computes weighted average of all confidence components.
    Weights: extraction 40%, doctor 30%, medicines 30%.
    """
    if not medicine_confs:
        # If no medicines detected, redistribute medicine weight to extraction and doctor
        return (extraction_conf * 0.55) + (doctor_conf * 0.45)

    avg_med_conf = sum(medicine_confs) / len(medicine_confs)
    
    overall = (extraction_conf * 0.40) + (doctor_conf * 0.30) + (avg_med_conf * 0.30)
    return min(1.0, max(0.0, overall))
