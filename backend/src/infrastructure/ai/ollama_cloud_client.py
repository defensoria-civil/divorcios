import httpx
import structlog
from typing import List, Dict, Any, Optional
from application.interfaces.ai.llm_client import LLMClient
from core.config import settings

logger = structlog.get_logger()


class OllamaCloudClient(LLMClient):
    """
    Cliente para Ollama Cloud API (https://ollama.com).
    
    Implementa la interfaz LLMClient para usar modelos cloud de Ollama,
    incluyendo modelos avanzados como minimax-m2, glm-4.6, deepseek-v3.1, etc.
    
    Responsabilidades:
    - Autenticación con API key de Ollama Cloud
    - Envío de requests de chat a modelos específicos
    - Generación de embeddings
    - Manejo de timeouts y errores de red
    """
    
    def __init__(self):
        self.base_url = settings.ollama_cloud_base_url.rstrip("/")
        self.api_key = settings.ollama_cloud_api_key
        self.timeout = 120  # Cloud puede tener mayor latencia
        self.default_chat_model = settings.llm_chat_model
        self.default_embedding_model = "nomic-embed-text"
    
    def _headers(self) -> Dict[str, str]:
        """Genera headers HTTP con autenticación Bearer"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Envía mensajes al modelo de chat de Ollama Cloud.
        
        Args:
            messages: Lista de mensajes en formato OpenAI [{"role": "user", "content": "..."}]
            tools: (Opcional) Lista de tools para function calling
            model: (Opcional) Modelo específico, por defecto usa llm_chat_model de config
        
        Returns:
            Contenido de la respuesta del modelo como string
        
        Raises:
            httpx.HTTPError: Si hay error en la request HTTP
        """
        model_name = model or self.default_chat_model
        
        payload = {
            'model': model_name,
            'messages': messages,
            'stream': False
        }
        
        if tools:
            payload['tools'] = tools
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                logger.info(
                    "ollama_cloud_chat_request",
                    model=model_name,
                    message_count=len(messages)
                )
                
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    headers=self._headers()
                )
                response.raise_for_status()
                
                data = response.json()
                content = data.get('message', {}).get('content', '')
                
                logger.info(
                    "ollama_cloud_chat_success",
                    model=model_name,
                    response_length=len(content)
                )
                
                return content
                
        except httpx.TimeoutException as e:
            logger.error("ollama_cloud_timeout", model=model_name, error=str(e))
            raise
        except httpx.HTTPError as e:
            logger.error("ollama_cloud_http_error", model=model_name, error=str(e))
            raise
        except Exception as e:
            logger.error("ollama_cloud_unexpected_error", model=model_name, error=str(e))
            raise
    
    async def embed(
        self, 
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Genera embeddings para una lista de textos.
        
        Args:
            texts: Lista de textos para generar embeddings
            model: (Opcional) Modelo de embeddings, por defecto usa nomic-embed-text
        
        Returns:
            Lista de vectores de embeddings
        
        Raises:
            httpx.HTTPError: Si hay error en la request HTTP
        """
        model_name = model or self.default_embedding_model
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                embeddings = []
                
                for text in texts:
                    logger.debug(
                        "ollama_cloud_embed_request",
                        model=model_name,
                        text_length=len(text)
                    )
                    
                    response = await client.post(
                        f"{self.base_url}/api/embed",
                        json={'model': model_name, 'input': text},
                        headers=self._headers()
                    )
                    response.raise_for_status()
                    
                    embedding = response.json().get('embedding', [])
                    embeddings.append(embedding)
                
                logger.info(
                    "ollama_cloud_embed_success",
                    model=model_name,
                    texts_count=len(texts)
                )
                
                return embeddings
                
        except httpx.TimeoutException as e:
            logger.error("ollama_cloud_embed_timeout", model=model_name, error=str(e))
            raise
        except httpx.HTTPError as e:
            logger.error("ollama_cloud_embed_http_error", model=model_name, error=str(e))
            raise
        except Exception as e:
            logger.error("ollama_cloud_embed_unexpected_error", model=model_name, error=str(e))
            raise
