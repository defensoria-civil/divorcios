import re
import json
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
    Servicio para detectar alucinaciones en respuestas del LLM.
    
    Utiliza dos estrategias:
    1. Validación basada en reglas (patterns, heurísticas)
    2. Validación con LLM especializado (glm-4.6:cloud) para análisis semántico
    
    Responsabilidades:
    - Detectar información inventada o fabricada
    - Validar consistencia con contexto proporcionado
    - Identificar respuestas inapropiadas para asesoramiento legal
    - Logging de decisiones para auditoría
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
    
    def __init__(self, llm_router=None):
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.HALLUCINATION_PATTERNS]
        self.data_patterns = [re.compile(p, re.IGNORECASE) for p in self.SPECIFIC_DATA_PATTERNS]
        
        # LLMRouter para validación semántica avanzada (opcional)
        self.llm_router = llm_router
        self.use_llm_validation = llm_router is not None
    
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
        
        # 2. Verificar si menciona datos específicos no presentes en contexto NI en la pregunta original
        for pattern in self.data_patterns:
            matches = pattern.findall(response)
            for match in matches:
                # Si el dato aparece en el contexto O en la pregunta del usuario,
                # asumimos que el asistente solo lo está reutilizando y NO lo marcamos como inventado.
                if match in context or match in question:
                    continue
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

    def _generate_explanation(self, flags: list[str], confidence: float) -> str:
        """Genera explicación legible del resultado"""
        if not flags:
            return f"Confianza: {confidence:.0%}. Respuesta válida sin indicadores de alucinación."
        explanations = {
            "claims_system_access": "La respuesta afirma tener acceso a sistemas/bases de datos",
            "invents_specific_data": "La respuesta menciona datos específicos no presentes en el contexto",
            "mentions_urls": "La respuesta incluye URLs que podrían no existir",
            "unknown_proper_noun": "Menciona nombres propios no verificables",
            "excessive_length": "Respuesta excesivamente larga (posible sobre-elaboración)",
            "answers_impossible_question": "Responde con certeza a pregunta que requiere información no disponible",
            "llm_detected_inconsistency": "El validador LLM detectó inconsistencias",
            "llm_detected_invented_data": "El validador LLM detectó datos inventados",
            "llm_detected_inappropriate_advice": "El validador LLM detectó consejo legal inapropiado",
        }
        parts = []
        for flag in flags:
            key = flag.split(":")[0]
            if key in explanations:
                parts.append(explanations[key])
        joined = "; ".join(parts) if parts else ", ".join(flags)
        return f"Confianza: {confidence:.0%}. {joined}"
    
    async def check_with_llm(
        self,
        response: str,
        context: str,
        question: str
    ) -> HallucinationCheckResult:
        """
        Validación semántica avanzada usando LLM especializado (glm-4.6:cloud).
        
        Complementa la validación basada en reglas con análisis de consistencia semántica.
        
        Args:
            response: Respuesta generada por el LLM
            context: Contexto proporcionado al LLM
            question: Pregunta original del usuario
            
        Returns:
            HallucinationCheckResult con validación semántica
        """
        if not self.use_llm_validation:
            logger.warning("llm_validation_not_available")
            # Fallback a validación basada en reglas
            return await self.check_response(response, context, question)
        
        validation_prompt = f"""Eres un experto en validar consistencia de respuestas de asistentes de IA.

Analiza si la siguiente RESPUESTA es consistente con el CONTEXTO proporcionado y si responde apropiadamente a la PREGUNTA.

CONTEXTO:
{context}

PREGUNTA DEL USUARIO:
{question}

RESPUESTA DEL ASISTENTE:
{response}

Evalúa los siguientes criterios y responde SOLO con un JSON:

{{
  "is_consistent": true/false,  // ¿La respuesta es consistente con el contexto?
  "invents_data": true/false,    // ¿La respuesta inventa datos específicos no presentes en el contexto?
  "appropriate": true/false,      // ¿La respuesta es apropiada para asesoramiento legal?
  "confidence": 0.0-1.0,          // Tu nivel de confianza en la validez de la respuesta
  "issues": ["lista de problemas detectados"],
  "explanation": "breve explicación"
}}

Criterios importantes:
- Si la respuesta menciona fechas, números, nombres que NO están en el contexto: invents_data=true
- Si la respuesta afirma tener acceso a sistemas/bases de datos: is_consistent=false
- Si da consejos legales muy específicos sin base: appropriate=false"""
        
        try:
            # Usar modelo especializado para validación (glm-4.6)
            llm_response = await self.llm_router.chat(
                messages=[{"role": "user", "content": validation_prompt}],
                task_type="hallucination_check"
            )
            
            # Parsear respuesta JSON
            json_text = llm_response.replace("```json", "").replace("```", "").strip()
            validation_data = json.loads(json_text)
            
            # Convertir a HallucinationCheckResult
            flags = []
            if not validation_data.get("is_consistent"):
                flags.append("llm_detected_inconsistency")
            if validation_data.get("invents_data"):
                flags.append("llm_detected_invented_data")
            if not validation_data.get("appropriate"):
                flags.append("llm_detected_inappropriate_advice")
            
            if validation_data.get("issues"):
                flags.extend([f"llm_issue:{issue}" for issue in validation_data["issues"]])
            
            confidence = float(validation_data.get("confidence", 0.5))
            is_valid = confidence >= 0.7 and validation_data.get("is_consistent", False)
            explanation = validation_data.get("explanation", "Validación LLM completada")
            
            logger.info(
                "llm_hallucination_check",
                is_valid=is_valid,
                confidence=confidence,
                flags=flags,
                model="glm-4.6:cloud"
            )
            
            return HallucinationCheckResult(
                is_valid=is_valid,
                confidence=confidence,
                flags=flags,
                explanation=f"Validación LLM: {explanation}"
            )
            
        except Exception as e:
            logger.error("llm_validation_error", error=str(e))
            # Fallback a validación basada en reglas
            return await self.check_response(response, context, question)
    
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
