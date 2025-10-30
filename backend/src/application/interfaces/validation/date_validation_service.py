from abc import ABC, abstractmethod
from application.dtos.validation_results import DateValidationResult

class DateValidationService(ABC):
    @abstractmethod
    def validate_birth_date(self, date_str: str) -> DateValidationResult:
        """Valida fecha de nacimiento con reglas legales (edad mínima 18 años)"""
        raise NotImplementedError

    @abstractmethod
    def validate_marriage_date(self, date_str: str, birth_date_solicitante: str, birth_date_conyuge: str) -> DateValidationResult:
        """Valida fecha de matrimonio con secuencia lógica"""
        raise NotImplementedError

    @abstractmethod
    def validate_separation_date(self, date_str: str, marriage_date: str) -> DateValidationResult:
        """Valida fecha de separación con secuencia lógica"""
        raise NotImplementedError
