import time
import redis
import structlog
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from core.config import settings

logger = structlog.get_logger()

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de rate limiting usando Redis
    Implementa límites por IP y por usuario autenticado
    """
    
    def __init__(self, app, redis_client: redis.Redis = None):
        super().__init__(app)
        self.redis = redis_client or redis.from_url(settings.redis_url, decode_responses=True)
        
        # Límites configurables
        self.limits = {
            "webhook": {"requests": 60, "window": 60},  # 60 req/min para webhooks
            "api": {"requests": 100, "window": 60},     # 100 req/min para API
            "anonymous": {"requests": 30, "window": 60}, # 30 req/min sin auth
        }
    
    async def dispatch(self, request: Request, call_next):
        # Bypass de rate limiting para TestClient de FastAPI (host 'testclient')
        # para evitar flaquezas en tests de integración.
        if request.client and request.client.host == "testclient":
            return await call_next(request)

        # Desactivar rate limiting para webhooks de WhatsApp.
        # WAHA puede enviar múltiples eventos "message.any" por cada mensaje (incluyendo los que
        # envía el propio bot), lo que genera ráfagas que disparan fácilmente el límite por IP.
        # En este entorno preferimos no rate‑limitar /webhook para evitar errores 429 hacia WAHA.
        if request.url.path.startswith("/webhook"):
            return await call_next(request)

        # Extraer identificador (IP o user)
        identifier = self._get_identifier(request)
        
        # Determinar tipo de límite
        limit_type = self._get_limit_type(request)
        limit_config = self.limits.get(limit_type, self.limits["anonymous"])
        
        # Verificar límite
        is_allowed, remaining = self._check_rate_limit(
            identifier,
            limit_type,
            limit_config["requests"],
            limit_config["window"]
        )
        
        if not is_allowed:
            logger.warning(
                "rate_limit_exceeded",
                identifier=identifier,
                limit_type=limit_type
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"Límite excedido: {limit_config['requests']} solicitudes por {limit_config['window']} segundos",
                    "retry_after": limit_config["window"]
                },
                headers={"Retry-After": str(limit_config["window"])}
            )
        
        # Continuar con la request
        response = await call_next(request)
        
        # Agregar headers informativos
        response.headers["X-RateLimit-Limit"] = str(limit_config["requests"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + limit_config["window"])
        
        return response
    
    def _get_identifier(self, request: Request) -> str:
        """Obtiene identificador único para rate limiting"""
        # Preferir user autenticado
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.get('sub', 'unknown')}"
        
        # Fallback a IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"
    
    def _get_limit_type(self, request: Request) -> str:
        """Determina tipo de límite según la ruta"""
        path = request.url.path
        
        if path.startswith("/webhook"):
            return "webhook"
        elif path.startswith("/api"):
            return "api"
        else:
            return "anonymous"
    
    def _check_rate_limit(self, identifier: str, limit_type: str, max_requests: int, window: int) -> tuple[bool, int]:
        """
        Verifica rate limit usando sliding window en Redis
        Retorna (is_allowed, remaining_requests)
        """
        key = f"ratelimit:{limit_type}:{identifier}"
        now = time.time()
        window_start = now - window
        
        try:
            # Usar pipeline para atomicidad
            pipe = self.redis.pipeline()
            
            # Remover requests viejas del window
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Contar requests en el window actual
            pipe.zcard(key)
            
            # Agregar request actual
            pipe.zadd(key, {str(now): now})
            
            # Setear TTL
            pipe.expire(key, window)
            
            results = pipe.execute()
            current_count = results[1]
            
            remaining = max(0, max_requests - current_count - 1)
            is_allowed = current_count < max_requests
            
            return is_allowed, remaining
            
        except Exception as e:
            logger.error("rate_limit_redis_error", error=str(e))
            # En caso de error de Redis, permitir request (fail-open)
            return True, max_requests
    
    def reset_limit(self, identifier: str, limit_type: str):
        """Resetea límite para un identificador (útil para testing)"""
        key = f"ratelimit:{limit_type}:{identifier}"
        try:
            self.redis.delete(key)
        except Exception as e:
            logger.error("reset_limit_error", error=str(e))


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware que agrega headers de seguridad a todas las respuestas.
    
    Nota: La documentación automática de FastAPI (Swagger UI/Redoc) carga assets desde CDN
    y ejecuta scripts inline. Con una CSP estricta (default-src 'self') esos recursos quedan
    bloqueados, resultando en una página en blanco en /docs. Para evitarlo, relajamos la CSP
    únicamente en /docs y /redoc, manteniendo una política estricta para el resto de rutas.
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Headers de seguridad estándar
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        path = request.url.path
        if path.startswith("/docs") or path.startswith("/redoc"):
            # Permitir assets de Swagger UI desde jsdelivr y ejecución inline que requiere el HTML generado.
            # También permitir imágenes data: y favicon de la doc de FastAPI.
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "font-src 'self' data:; "
                "worker-src 'self' blob:"
            )
        else:
            # Política estricta para API y demás rutas
            response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging estructurado de requests"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            "request_start",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown"
        )
        
        # Procesar request
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                "request_complete",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=int(duration * 1000)
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "request_error",
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration_ms=int(duration * 1000)
            )
            raise
