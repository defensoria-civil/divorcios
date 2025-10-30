from abc import ABC, abstractmethod
from application.dtos.validation_results import AddressValidationResult

class AddressValidationService(ABC):
    @abstractmethod
    def validate_address(self, address_text: str, is_marital_address: bool = False) -> AddressValidationResult:
        """
        Valida una dirección completa con componentes necesarios
        Para domicilio conyugal, verifica jurisdicción (San Rafael/Mendoza)
        """
        raise NotImplementedError
