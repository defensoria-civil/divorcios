import structlog
from typing import List, Dict, Any, Optional, Literal
from application.interfaces.ai.llm_client import LLMClient
from .ollama_cloud_client import OllamaCloudClient
from .ollama_client import OllamaClient
from .gemini_client import GeminiClient
from core.config import settings

logger = structlog.get_logger()

# Tipos de tareas soportadas
TaskType = Literal['chat', 'reasoning', 'hallucination_check', 'vision_ocr', 'embeddings']


class LLMRouter(LLMClient):
    """
    Router inteligente de LLMs con Strategy Pattern.
    
    Selecciona el proveedor y modelo óptimo según el tipo de tarea,
    con fallback automático en caso de fallos.
    
    Responsabilidades:
    - Mapear tipos de tarea a modelos específicos
    - Gestionar cascada de fallbacks (Ollama Cloud → Local → Gemini)
    - Logging de proveedor usado y latencia
    - Manejo centralizado de errores
    """
    
    def __init__(self):
        # Inicializar proveedores disponibles (orden de prioridad)
        self.providers = {
            'ollama_cloud': OllamaCloudClient(),
            'ollama_local': OllamaClient(),
            'gemini': GeminiClient()
        }
        
        # Mapeo de tipo de tarea a modelo específico de Ollama Cloud
        self.model_map = {
            'chat': settings.llm_chat_model,
            'reasoning': settings.llm_reasoning_model,
            'hallucination_check': settings.llm_hallucination_model,
            'vision_ocr': settings.llm_vision_model,
            'embeddings': settings.llm_embedding_model
        }
        
        # Orden de fallback por defecto
        self.fallback_order = ['ollama_cloud', 'ollama_local', 'gemini']
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        task_type: TaskType = 'chat'
    ) -> str:
        """
        Envía mensajes al LLM apropiado según el tipo de tarea.
        
        Args:
            messages: Lista de mensajes en formato OpenAI
            tools: (Opcional) Tools para function calling
            task_type: Tipo de tarea para seleccionar modelo óptimo
        
        Returns:
            Respuesta del modelo como string
        """
        model = self.model_map.get(task_type, settings.llm_chat_model)
        
        # Intentar con cada proveedor en orden hasta que uno funcione
        for provider_name in self.fallback_order:
            try:
                provider = self.providers[provider_name]
                
                logger.info(
                    "llm_router_attempt",
                    provider=provider_name,
                    task_type=task_type,
                    model=model
                )
                
                # Ollama Cloud usa parámetro model, otros no
                if provider_name == 'ollama_cloud':
                    response = await provider.chat(messages, tools=tools, model=model)
                else:
                    response = await provider.chat(messages, tools=tools)
                
                logger.info(
                    "llm_router_success",
                    provider=provider_name,
                    task_type=task_type
                )
                
                return response
                
            except Exception as e:
                logger.warning(
                    "llm_router_provider_failed",
                    provider=provider_name,
                    task_type=task_type,
                    error=str(e)
                )
                
                # Si es el último proveedor, re-raise el error
                if provider_name == self.fallback_order[-1]:
                    logger.error(
                        "llm_router_all_providers_failed",
                        task_type=task_type
                    )
                    raise
                
                # Si no, continuar con siguiente proveedor
                continue
        
        # Este código no debería alcanzarse, pero por seguridad
        raise Exception("Todos los proveedores de LLM fallaron")
    
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Genera embeddings para una lista de textos.
        
        Args:
            texts: Lista de textos para generar embeddings
            model: (Opcional) Modelo específico de embeddings
        
        Returns:
            Lista de vectores de embeddings
        """
        embedding_model = model or self.model_map['embeddings']
        
        # Para embeddings, preferir local por velocidad y evitar depender de cuotas externas.
        # En este entorno, si Ollama Local no está disponible, degradamos silenciosamente
        # (sin lanzar excepción) y desactivamos las búsquedas semánticas que lo usan.
        #
        # Orden actual: solo Ollama Local. Si falla, devolvemos lista vacía.
        embed_fallback_order = ['ollama_local']
        
        for provider_name in embed_fallback_order:
            try:
                provider = self.providers[provider_name]
                
                logger.info(
                    "llm_router_embed_attempt",
                    provider=provider_name,
                    model=embedding_model,
                    texts_count=len(texts)
                )
                
                # Ollama Cloud soporta parámetro model
                if provider_name == 'ollama_cloud':
                    embeddings = await provider.embed(texts, model=embedding_model)
                else:
                    embeddings = await provider.embed(texts)
                
                logger.info(
                    "llm_router_embed_success",
                    provider=provider_name,
                    texts_count=len(texts)
                )
                
                return embeddings
                
            except Exception as e:
                logger.warning(
                    "llm_router_embed_provider_failed",
                    provider=provider_name,
                    error=str(e)
                )
                
                # Si este era el último proveedor de la lista, no propagamos la excepción.
                # Devolvemos lista vacía para que los consumidores degraden a modo sin embeddings.
                if provider_name == embed_fallback_order[-1]:
                    logger.error("llm_router_embed_all_providers_failed")
                    return []
                
                continue
        
        # Seguridad extra: si por alguna razón se sale del bucle, devolver lista vacía.
        return []
