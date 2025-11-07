import httpx
from typing import List, Dict, Any, Optional
from application.interfaces.ai.llm_client import LLMClient
from core.config import settings

class OllamaClient(LLMClient):
    def __init__(self, model: str = "nomic-embed-text"):
        self.base = settings.ollama_base_url.rstrip("/")
        self.model = model

    async def chat(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None) -> str:
        async with httpx.AsyncClient(timeout=60, verify=False) as client:
            resp = await client.post(
                f"{self.base}/api/chat",
                json={"model": self.model, "messages": messages, "stream": False},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")

    async def embed(self, texts: List[str]) -> List[List[float]]:
        async with httpx.AsyncClient(timeout=60, verify=False) as client:
            out = []
            for t in texts:
                r = await client.post(
                    f"{self.base}/api/embeddings",
                    json={"model": self.model, "prompt": t},
                )
                r.raise_for_status()
                out.append(r.json().get("embedding", []))
            return out
