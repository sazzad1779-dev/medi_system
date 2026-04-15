import os
import cv2
import numpy as np
from PIL import Image
from dataclasses import dataclass

@dataclass
class PreprocessingResult:
    original_path: str
    preprocessed_path: str
    success: bool

def preprocess_image(image_path: str) -> PreprocessingResult:
    """
    Cleans and optimizes the prescription image for VLM extraction.
    Currently: Basic resizing and contrast enhancement.
    """
    try:
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Could not read image")

        # Basic Preprocessing: Grayscale and Denoising
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Adaptive Thresholding for better text contrast if needed
        # (Using a simpler approach for the VLM to retain most details)
        
        # Generate output path
        dir_name = os.path.dirname(image_path)
        base_name = "pre_" + os.path.basename(image_path)
        output_path = os.path.join(dir_name, base_name)
        
        # Save preprocessed image
        cv2.imwrite(output_path, denoised)
        
        return PreprocessingResult(
            original_path=image_path,
            preprocessed_path=output_path,
            success=True
        )
    except Exception as e:
        # Fallback to original if processing fails
        return PreprocessingResult(
            original_path=image_path,
            preprocessed_path=image_path,
            success=False
        )
