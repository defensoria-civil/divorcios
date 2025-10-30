import google.generativeai as genai
from typing import List, Dict, Any, Optional
from application.interfaces.ai.llm_client import LLMClient
from core.config import settings

class GeminiClient(LLMClient):
    def __init__(self):
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.embed_model = "text-embedding-004"

    async def chat(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None) -> str:
        # Simple adapter; messages -> single prompt with roles
        parts = []
        for m in messages:
            parts.append(f"{m['role'].upper()}: {m['content']}")
        prompt = "\n".join(parts)
        resp = await self.model.aGenerateContent(prompt)
        return resp.text or ""

    async def embed(self, texts: List[str]) -> List[List[float]]:
        resp = await genai.aembed_content(model=self.embed_model, content=texts)
        # API returns different shapes for batch/single; normalize
        if hasattr(resp, "embeddings"):
            return [e.values for e in resp.embeddings]
        if hasattr(resp, "embedding"):
            return [resp.embedding.values]
        return [[] for _ in texts]
