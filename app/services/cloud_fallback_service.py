import base64
import json
import logging
from typing import Tuple, Dict, Any
from openai import AsyncOpenAI
from app.config import settings

class CloudFallbackService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

    async def extract(self, image_path: str) -> Tuple[Dict[str, Any], float]:
        """
        Calls OpenAI GPT-4o Vision as a high-accuracy fallback.
        """
        if not self.client:
            logging.warning("Cloud fallback triggered but no API key configured.")
            raise ValueError("OpenAI API key missing")

        try:
            # 1. Prepare image
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")

            # 2. Call OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract all data from this medical prescription into structured JSON format. Include doctor details and a list of medicines with brand, generic, strength, dosage for and instructions."},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ],
                    }
                ],
                max_tokens=2000,
                response_format={"type": "json_object"}
            )

            # 3. Parse and return
            content = response.choices[0].message.content
            raw_data = json.loads(content)
            
            # OpenAI is generally highly confident for clear images
            return raw_data, 0.95

        except Exception as e:
            logging.error(f"Cloud fallback failed: {str(e)}")
            raise e
