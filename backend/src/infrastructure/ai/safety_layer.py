"""Capa de seguridad básica para interacción con LLM.

Por ahora implementa:
- Detección muy simple de prompt injection basada en patrones.
- Hooks para filtro de entrada y salida que se pueden enriquecer más adelante.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Dict, List, Set

import re
import structlog


logger = structlog.get_logger()


INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "you are now",
    "act as",
    "SYSTEM:",
    "system:",
]


@dataclass
class SafetyResult:
    allowed: bool
    text: str
    reason: str | None = None


# Patrones muy simples para detección/redacción de PII.
# Nota: en un sistema real convendría usar una librería dedicada o
# integrar con un servicio de DLP; aquí mantenemos la lógica acotada.
PII_PATTERNS: Dict[str, re.Pattern[str]] = {
    "cuit": re.compile(r"\b\d{2}-?\d{7,8}-?\d\b"),
    "dni": re.compile(r"\b\d{7,8}\b"),
    # Teléfonos tipo +5492604..., o secuencias largas de dígitos
    "phone": re.compile(r"\+?\d{10,15}"),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
}


class SafetyLayer:
    """Safety layer mínima.

    La idea es poder evolucionarla hacia una integración con filtros
    de seguridad de Vertex AI u otros proveedores sin cambiar las
    llamadas desde el dominio de la aplicación.
    """

    def filter_input(self, text: str) -> SafetyResult:
        """Analiza el prompt de entrada para detectar intentos simples de prompt injection.

        Devuelve un SafetyResult con allowed=False si se detecta algo sospechoso.
        """

        lowered = text.lower()
        for pattern in INJECTION_PATTERNS:
            if pattern.lower() in lowered:
                logger.warning(
                    "safety_layer_prompt_injection_detected",
                    pattern=pattern,
                    text_preview=text[:200],
                )
                return SafetyResult(
                    allowed=False,
                    text=text,
                    reason=f"Posible prompt injection detectado: '{pattern}'",
                )

        # En esta primera versión no modificamos el texto
        return SafetyResult(allowed=True, text=text, reason=None)

    def _redact_pii(self, text: str) -> Tuple[str, Set[str]]:
        """Redacta PII básica (DNI, CUIT, teléfono, email) en el texto.

        Devuelve el texto redaccionado y el conjunto de tipos de PII encontrados.
        """
        found: Set[str] = set()
        redacted = text

        for name, pattern in PII_PATTERNS.items():
            if pattern.search(redacted):
                found.add(name)
                placeholder = f"<{name.upper()}>"
                redacted = pattern.sub(placeholder, redacted)

        if found:
            logger.info(
                "safety_layer_pii_redacted",
                types=sorted(found),
                preview=text[:200],
            )
        return redacted, found

    def filter_output(self, text: str) -> SafetyResult:
        """Filtra la salida del modelo.

        - Redacta PII evidente (DNI, CUIT, teléfono, email) para evitar
          que el modelo devuelva identificadores crudos.
        - En esta versión no bloquea contenido, solo redacciona y loguea.
        """

        redacted, found = self._redact_pii(text)
        reason = None
        if found:
            reason = f"PII redacted: {', '.join(sorted(found))}"
        return SafetyResult(allowed=True, text=redacted, reason=reason)
