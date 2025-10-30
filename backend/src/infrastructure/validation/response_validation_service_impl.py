import re
from application.interfaces.validation.response_validation_service import ResponseValidationService
from application.dtos.validation_results import ResponseValidationResult

JOKE_WORDS = ["jaja", "jeje", "jiji", "xd", "a molestar", "broma"]
INAPPROPRIATE = ["insulto", "tonto", "idiota", "mierda"]
INJECTION_PATTERNS = [
    r"\bignora\b", r"\bolvida\b", r"\basistente\b", r"\bsistema\b",
    r"^system:", r"^assistant:", r"^user:", r"```", r"###"
]

class SimpleResponseValidationService(ResponseValidationService):
    def validate_user_response(self, response_text: str, field_name: str, question_context: str) -> ResponseValidationResult:
        text = (response_text or "").strip()
        flags = []
        errors = []
        if not text:
            errors.append("Respuesta vacía.")
        low = text.lower()

        if any(w in low for w in JOKE_WORDS):
            flags.append("humor")
            errors.append("Respuesta no seria detectada.")

        if any(w in low for w in INAPPROPRIATE):
            flags.append("inapropiada")
            errors.append("Contenido inapropiado detectado.")

        if any(re.search(p, low) for p in INJECTION_PATTERNS):
            flags.append("posible_inyeccion")
            errors.append("Posible intento de inyección de prompt.")

        # Controles simples por contexto
        if field_name.lower() in ("dni", "documento"):
            if not re.search(r"\b\d{7,8}\b", low):
                errors.append("Se espera un DNI de 7-8 dígitos.")
        if field_name.lower() in ("fecha de nacimiento", "fecha_nacimiento"):
            if not re.search(r"\b\d{2}/\d{2}/\d{4}\b", low):
                errors.append("Se espera una fecha en formato DD/MM/AAAA.")
        if "domicilio" in field_name.lower():
            if not re.search(r"\d", low):
                errors.append("El domicilio debe incluir número de calle.")

        return ResponseValidationResult(len(errors) == 0, errors, flags)
