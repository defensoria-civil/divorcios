import google.generativeai as genai
from typing import List, Dict, Any, Optional
from application.interfaces.ai.llm_client import LLMClient
from core.config import settings

class GeminiClient(LLMClient):
    def __init__(self):
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
        # Usar gemini-2.5-flash (modelo disponible actualmente)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        # Modelo de embeddings actualizado (text-embedding-004 está deprecado)
        # Importante: la API espera el nombre completo "models/gemini-embedding-001"
        # Ver: https://ai.google.dev/api/embeddings
        self.embed_model = "models/gemini-embedding-001"

    async def chat(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None) -> str:
        # Simple adapter; messages -> single prompt with roles
        parts = []
        for m in messages:
            parts.append(f"{m['role'].upper()}: {m['content']}")
        prompt = "\n".join(parts)
        resp = await self.model.generate_content_async(prompt)
        return resp.text or ""

    async def embed(self, texts: List[str]) -> List[List[float]]:
        # La API de Gemini no tiene método asíncrono para embeddings
        resp = genai.embed_content(model=self.embed_model, content=texts)
        
        # API retorna un dict con clave 'embedding' que contiene una lista de floats
        if isinstance(resp, dict) and 'embedding' in resp:
            # Para un solo texto, retorna [embedding]
            # Para múltiples textos, verificar si es lista de listas
            embedding = resp['embedding']
            if len(texts) == 1:
                return [embedding]  # Wrap single embedding
            else:
                return embedding if isinstance(embedding[0], list) else [embedding]
        
        # Si no hay embeddings, fallar en lugar de retornar vacíos
        raise Exception(f"Gemini retornó formato inesperado: {type(resp)}")
