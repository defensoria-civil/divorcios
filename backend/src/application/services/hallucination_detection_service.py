import re
import structlog
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = structlog.get_logger()

@dataclass
class HallucinationCheckResult:
    """Resultado de verificación de alucinación"""
    is_valid: bool
    confidence: float
    flags: List[str]
    explanation: str

class HallucinationDetectionService:
    """
    Servicio para detectar alucinaciones en respuestas del LLM
    Valida que las respuestas sean apropiadas, factuales y no contengan información inventada
    """
    
    # Patrones que indican posible alucinación
    HALLUCINATION_PATTERNS = [
        r"según mi base de datos",
        r"en mi sistema",
        r"tengo acceso a",
        r"puedo ver que",
        r"según mis registros",
        r"he verificado que",
    ]
    
    # Palabras que indican incertidumbre (buenas en respuestas legales)
    UNCERTAINTY_INDICATORS = [
        "posible", "probable", "podría", "quizás", "tal vez",
        "en general", "usualmente", "depende", "puede variar"
    ]
    
    # Información específica que NO debería inventar
    SPECIFIC_DATA_PATTERNS = [
        r"\d{7,8}",  # DNI
        r"\d{2}/\d{2}/\d{4}",  # Fechas específicas
        r"expediente\s+n[úu]mero\s+\d+",  # Números de expediente
        r"juzgado\s+\d+",  # Juzgados específicos
    ]
    
    def __init__(self):
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.HALLUCINATION_PATTERNS]
        self.data_patterns = [re.compile(p, re.IGNORECASE) for p in self.SPECIFIC_DATA_PATTERNS]
    
    async def check_response(
        self, 
        response: str, 
        context: str, 
        question: str
    ) -> HallucinationCheckResult:
        """
        Verifica si una respuesta del LLM contiene alucinaciones
        
        Args:
            response: Respuesta generada por el LLM
            context: Contexto proporcionado al LLM
            question: Pregunta original del usuario
        """
        flags = []
        confidence = 1.0
        
        # 1. Verificar patrones sospechosos de alucinación
        for pattern in self.compiled_patterns:
            if pattern.search(response):
                flags.append("claims_system_access")
                confidence -= 0.3
        
        # 2. Verificar si menciona datos específicos no presentes en contexto
        for pattern in self.data_patterns:
            matches = pattern.findall(response)
            for match in matches:
                if match not in context:
                    flags.append(f"invents_specific_data:{match}")
                    confidence -= 0.4
        
        # 3. Verificar URLs o referencias inventadas
        url_pattern = re.compile(r"https?://[^\s]+")
        urls = url_pattern.findall(response)
        if urls:
            flags.append("mentions_urls")
            confidence -= 0.2
        
        # 4. Verificar nombres propios no en contexto (excepto lugares conocidos de Mendoza)
        known_places = ["san rafael", "mendoza", "argentina", "defensoría"]
        capitalized_words = re.findall(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b", response)
        for word in capitalized_words:
            if word.lower() not in known_places and word not in context:
                flags.append(f"unknown_proper_noun:{word}")
                confidence -= 0.1
        
        # 5. POSITIVO: Verificar indicadores de incertidumbre apropiada
        uncertainty_count = sum(1 for ind in self.UNCERTAINTY_INDICATORS if ind in response.lower())
        if uncertainty_count > 0:
            confidence += 0.1  # Bonus por expresar incertidumbre
        
        # 6. Verificar longitud excesiva (posible sobre-elaboración)
        if len(response.split()) > 300:
            flags.append("excessive_length")
            confidence -= 0.1
        
        # 7. Verificar si responde a pregunta que no puede responder
        impossible_questions = [
            r"cuánto (tiempo|demora|tarda)",
            r"cuándo (va a|se va a)",
            r"qué (día|fecha) exacta"
        ]
        for pattern_str in impossible_questions:
            if re.search(pattern_str, question.lower()):
                # Verificar si responde con fecha/tiempo específico sin datos
                if any(p.search(response) for p in self.data_patterns[:2]):
                    flags.append("answers_impossible_question")
                    confidence -= 0.5
        
        # Normalizar confidence
        confidence = max(0.0, min(1.0, confidence))
        
        is_valid = confidence >= 0.6 and not any("invents" in f for f in flags)
        
        explanation = self._generate_explanation(flags, confidence)
        
        logger.info(
            "hallucination_check",
            is_valid=is_valid,
            confidence=confidence,
            flags=flags
        )
        
        return HallucinationCheckResult(
            is_valid=is_valid,
            confidence=confidence,
            flags=flags,
            explanation=explanation
        )
    
    def _generate_explanation(self, flags: List[str], confidence: float) -> str:
        """Genera explicación legible del resultado"""
        if not flags:
            return "Respuesta válida sin indicadores de alucinación"
        
        explanations = {
            "claims_system_access": "La respuesta afirma tener acceso a sistemas/bases de datos",
            "invents_specific_data": "La respuesta menciona datos específicos no presentes en el contexto",
            "mentions_urls": "La respuesta incluye URLs que podrían no existir",
            "unknown_proper_noun": "Menciona nombres propios no verificables",
            "excessive_length": "Respuesta excesivamente larga (posible sobre-elaboración)",
            "answers_impossible_question": "Responde con certeza a pregunta que requiere información no disponible"
        }
        
        parts = []
        for flag in flags:
            key = flag.split(":")[0]
            if key in explanations:
                parts.append(explanations[key])
        
        return f"Confianza: {confidence:.0%}. " + "; ".join(parts)
    
    async def validate_legal_advice(self, response: str) -> HallucinationCheckResult:
        """
        Validación específica para asesoramiento legal
        Asegura que no se den consejos legales específicos fuera del alcance
        """
        flags = []
        confidence = 1.0
        
        # Patrones prohibidos en asesoramiento legal
        prohibited = [
            r"te garantizo",
            r"seguro que (va a|vas a)",
            r"siempre funciona",
            r"nunca (falla|pierde)",
            r"definitivamente",
            r"sin duda alguna"
        ]
        
        for pattern_str in prohibited:
            if re.search(pattern_str, response.lower()):
                flags.append("inappropriate_legal_certainty")
                confidence -= 0.5
        
        # Verificar que incluye disclaimers apropiados para casos sensibles
        sensitive_topics = ["violencia", "maltrato", "abuso", "menores"]
        has_sensitive = any(topic in response.lower() for topic in sensitive_topics)
        
        if has_sensitive:
            appropriate_phrases = ["recomiendo consultar", "es importante que", "deberías hablar con"]
            has_disclaimer = any(phrase in response.lower() for phrase in appropriate_phrases)
            
            if not has_disclaimer:
                flags.append("missing_sensitive_topic_disclaimer")
                confidence -= 0.3
        
        is_valid = confidence >= 0.7
        explanation = "Validación de asesoramiento legal: " + (
            "apropiado" if is_valid else "requiere revisión"
        )
        
        return HallucinationCheckResult(
            is_valid=is_valid,
            confidence=confidence,
            flags=flags,
            explanation=explanation
        )
