import httpx
import json
import base64
import logging
import google.generativeai as genai
from typing import Tuple, Dict, Any
from app.config import settings
class VLMService:
    def __init__(self):
        self.provider = settings.VLM_PROVIDER
        self.base_url = settings.VLLM_BASE_URL
        self.model_name = settings.VLLM_MODEL_NAME
        self.api_key = settings.VLLM_API_KEY or settings.GEMINI_API_KEY
        
        # Always try to initialize Gemini as it's our primary fallback
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.gemini_model = genai.GenerativeModel("gemini-2.5-flash")
        elif self.provider == "gemini":
            raise ValueError("GEMINI_API_KEY is required for Gemini VLM provider")

    async def extract(self, image_path: str) -> Tuple[Dict[str, Any], float]:
        """
        Extracts data using the configured provider (Local vLLM or Gemini API).
        Falls back to Gemini if local vLLM is unreachable.
        """
        if self.provider == "local":
            try:
                return await self._extract_local(image_path)
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if hasattr(self, 'gemini_model'):
                    logging.warning(f"Local VLM unreachable at {self.base_url}. Falling back to Gemini. Error: {str(e)}")
                    return await self._extract_gemini(image_path)
                logging.error(f"Local VLM unreachable and no Gemini API key configured for fallback.")
                raise
        elif self.provider == "gemini":
            return await self._extract_gemini(image_path)
        else:
            raise ValueError(f"Unknown VLM provider: {self.provider}")

    async def _extract_local(self, image_path: str) -> Tuple[Dict[str, Any], float]:
        """Existing local vLLM logic (OpenAI compatible)"""
        try:
            with open(image_path, "rb") as f:
                base64_image = base64.b64encode(f.read()).decode("utf-8")

            prompt = (
                "Extract structured data from this medical prescription. "
                "Include doctor's full name, BMDC registration number, and a list of medicines. "
                "For each medicine, include brand name, generic name, dosage form, strength, "
                "dosage instructions, and duration. Return valid JSON only."
            )

            payload = {
                "model": self.model_name,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }],
                "max_tokens": settings.VLLM_MAX_TOKENS,
                "temperature": settings.VLLM_TEMPERATURE,
                "response_format": {"type": "json_object"}
            }

            async with httpx.AsyncClient(timeout=settings.VLLM_TIMEOUT_SECONDS) as client:
                response = await client.post(f"{self.base_url}/chat/completions", json=payload)
                response.raise_for_status()
                result = response.json()

            content = result["choices"][0]["message"]["content"]
            return json.loads(content), 0.85
        except Exception as e:
            logging.error(f"Local VLM failed: {str(e)}")
            raise

    async def _extract_gemini(self, image_path: str) -> Tuple[Dict[str, Any], float]:
        """Gemini 1.5 Flash Vision logic (RAM efficient)"""
        try:
            # 1. Prepare image
            with open(image_path, "rb") as f:
                img_data = f.read()
            
            # 2. Prepare payload
            img_part = {"mime_type": "image/jpeg", "data": img_data}
            prompt = (
                "Extract all details from this medical prescription into a JSON object. "
                "Schema: { 'doctor': { 'full_name', 'bmdc_reg', 'specialty', 'institution' }, "
                "'medicines': [ { 'brand_name', 'generic_name', 'dosage_form', 'strength', 'dosage_instruction', 'duration' } ] }"
            )

            # 3. Call Gemini (using to_thread as genai is mostly sync)
            import asyncio
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                [prompt, img_part],
                generation_config=genai.GenerationConfig(response_mime_type="application/json")
            )
            
            raw_data = json.loads(response.text)
            return raw_data, 0.98 # Gemini is highly reliable for OCR
            
        except Exception as e:
            logging.error(f"Gemini VLM failed: {str(e)}")
            raise
