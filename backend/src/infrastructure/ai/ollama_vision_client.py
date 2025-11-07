import base64
import httpx
import structlog
from typing import List, Dict, Optional
from core.config import settings

logger = structlog.get_logger()


class OllamaVisionClient:
    """
    Cliente especializado para modelos de visión en Ollama Cloud.
    
    Proporciona métodos para análisis de imágenes usando modelos multimodales
    como qwen3-vl, que combinan capacidades de visión y lenguaje.
    
    Responsabilidades:
    - Conversión de imágenes a formato base64
    - Envío de requests multimodales (texto + imágenes)
    - Análisis estructurado de documentos visuales
    - Manejo específico de errores de modelos de visión
    """
    
    def __init__(self):
        self.base_url = settings.ollama_cloud_base_url.rstrip("/")
        self.api_key = settings.ollama_cloud_api_key
        self.timeout = 120  # Modelos de visión requieren más tiempo
        self.default_vision_model = settings.llm_vision_model
    
    def _headers(self) -> Dict[str, str]:
        """Genera headers HTTP con autenticación Bearer"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def _encode_image(self, image_bytes: bytes) -> str:
        """
        Convierte bytes de imagen a base64 string.
        
        Args:
            image_bytes: Bytes de la imagen
            
        Returns:
            String base64 de la imagen
        """
        return base64.b64encode(image_bytes).decode('utf-8')
    
    async def analyze_image(
        self,
        image_bytes: bytes,
        prompt: str,
        model: Optional[str] = None
    ) -> str:
        """
        Analiza una imagen con un prompt específico.
        
        Args:
            image_bytes: Bytes de la imagen a analizar
            prompt: Prompt describiendo qué extraer/analizar de la imagen
            model: (Opcional) Modelo de visión a usar, por defecto qwen3-vl:cloud
        
        Returns:
            Respuesta del modelo como string
        
        Raises:
            httpx.HTTPError: Si hay error en la request HTTP
        """
        model_name = model or self.default_vision_model
        
        # Convertir imagen a base64
        image_b64 = self._encode_image(image_bytes)
        
        messages = [{
            'role': 'user',
            'content': prompt,
            'images': [image_b64]
        }]
        
        payload = {
            'model': model_name,
            'messages': messages,
            'stream': False
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                logger.info(
                    "ollama_vision_analyze_request",
                    model=model_name,
                    image_size=len(image_bytes),
                    prompt_length=len(prompt)
                )
                
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    headers=self._headers()
                )
                response.raise_for_status()
                
                data = response.json()
                content = data['message']['content']
                
                logger.info(
                    "ollama_vision_analyze_success",
                    model=model_name,
                    response_length=len(content)
                )
                
                return content
                
        except httpx.TimeoutException as e:
            logger.error("ollama_vision_timeout", model=model_name, error=str(e))
            raise
        except httpx.HTTPError as e:
            logger.error("ollama_vision_http_error", model=model_name, error=str(e))
            raise
        except Exception as e:
            logger.error("ollama_vision_unexpected_error", model=model_name, error=str(e))
            raise
    
    async def analyze_multiple_images(
        self,
        images_bytes: List[bytes],
        prompt: str,
        model: Optional[str] = None
    ) -> str:
        """
        Analiza múltiples imágenes simultáneamente con un prompt.
        
        Útil para comparar documentos o extraer información de múltiples páginas.
        
        Args:
            images_bytes: Lista de bytes de las imágenes a analizar
            prompt: Prompt describiendo qué extraer/analizar
            model: (Opcional) Modelo de visión a usar
        
        Returns:
            Respuesta del modelo como string
        
        Raises:
            httpx.HTTPError: Si hay error en la request HTTP
        """
        model_name = model or self.default_vision_model
        
        # Convertir todas las imágenes a base64
        images_b64 = [self._encode_image(img) for img in images_bytes]
        
        messages = [{
            'role': 'user',
            'content': prompt,
            'images': images_b64
        }]
        
        payload = {
            'model': model_name,
            'messages': messages,
            'stream': False
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                logger.info(
                    "ollama_vision_multi_analyze_request",
                    model=model_name,
                    images_count=len(images_bytes),
                    total_size=sum(len(img) for img in images_bytes)
                )
                
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    headers=self._headers()
                )
                response.raise_for_status()
                
                data = response.json()
                content = data['message']['content']
                
                logger.info(
                    "ollama_vision_multi_analyze_success",
                    model=model_name,
                    images_count=len(images_bytes),
                    response_length=len(content)
                )
                
                return content
                
        except httpx.TimeoutException as e:
            logger.error("ollama_vision_multi_timeout", model=model_name, error=str(e))
            raise
        except httpx.HTTPError as e:
            logger.error("ollama_vision_multi_http_error", model=model_name, error=str(e))
            raise
        except Exception as e:
            logger.error("ollama_vision_multi_unexpected_error", model=model_name, error=str(e))
            raise
