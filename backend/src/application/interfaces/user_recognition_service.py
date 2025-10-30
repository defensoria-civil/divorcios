from abc import ABC, abstractmethod

class UserRecognitionService(ABC):
    @abstractmethod
    def should_recognize_user(self, case_data: dict) -> bool:
        """Determina si reconocer al usuario que retoma trámite"""
        raise NotImplementedError

    @abstractmethod
    def generate_recognition_message(self, collected_data: dict) -> str:
        """Genera mensaje personalizado para usuario reconocido"""
        raise NotImplementedError
