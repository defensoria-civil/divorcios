from abc import ABC, abstractmethod
from application.dtos.validation_results import ResponseValidationResult

class ResponseValidationService(ABC):
    @abstractmethod
    def validate_user_response(self, response_text: str, field_name: str, question_context: str) -> ResponseValidationResult:
        """
        Valida respuestas de usuarios para detectar:
         - Bromas o inapropiadas
         - Respuestas vacías o irrelevantes
         - Contenido fuera de contexto
        """
        raise NotImplementedError
