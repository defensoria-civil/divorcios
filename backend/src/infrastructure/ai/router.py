from typing import List, Dict, Any, Optional
from application.interfaces.ai.llm_client import LLMClient
from .gemini_client import GeminiClient
from .ollama_client import OllamaClient

class LLMRouter(LLMClient):
    def __init__(self):
        self.primary = GeminiClient()
        self.fallback = OllamaClient()

    async def chat(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None) -> str:
        try:
            return await self.primary.chat(messages, tools)
        except Exception:
            return await self.fallback.chat(messages, tools)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        try:
            return await self.primary.embed(texts)
        except Exception:
            return await self.fallback.embed(texts)
