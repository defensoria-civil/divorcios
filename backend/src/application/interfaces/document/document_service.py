from abc import ABC, abstractmethod
from typing import Protocol

class DocumentService(ABC):
    @abstractmethod
    def generate_divorce_petition_pdf(self, case_data: dict) -> bytes:
        """Genera una petición de divorcio en PDF con datos del caso."""
        raise NotImplementedError
