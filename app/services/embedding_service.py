import asyncio
from typing import List, Union, Optional
import google.generativeai as genai
import httpx
from app.config import settings

class EmbeddingService:
    def __init__(self, provider_type: Optional[str] = None):
        self.provider = provider_type or settings.EMBEDDING_PROVIDER
        
        if self.provider == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is required for gemini embedding provider")
            genai.configure(api_key=settings.GEMINI_API_KEY)

    async def embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generates embeddings for one or more strings using cloud providers.
        """
        if not text:
            return []

        if isinstance(text, str):
            texts = [text]
            is_single = True
        else:
            texts = text
            is_single = False

        if self.provider == "gemini" or self.provider == "local":
            # Use specific model and dimension from settings
            model = settings.EMBEDDING_MODEL
            
            # Using to_thread because genai is blocking
            responses = await asyncio.to_thread(
                genai.embed_content,
                model=model,
                content=texts,
                task_type="retrieval_document",
                output_dimensionality=settings.EMBEDDING_DIMENSION
            )
            embeddings = responses['embedding']
            return embeddings[0] if is_single else embeddings

        elif self.provider == "jina":
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.jina.ai/v1/embeddings",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {settings.JINA_API_KEY}"
                    },
                    json={
                        "model": "jina-embeddings-v2-base-en",
                        "input": texts
                    }
                )
                response.raise_for_status()
                data = response.json()
                embeddings = [item["embedding"] for item in data["data"]]
                return embeddings[0] if is_single else embeddings

        else:
            raise ValueError(f"Unknown embedding provider: {self.provider}")
