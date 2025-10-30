from application.interfaces.user_recognition_service import UserRecognitionService

class SimpleUserRecognitionService(UserRecognitionService):
    def should_recognize_user(self, case_data: dict) -> bool:
        completed = case_data.get("phases", {}).get("datos_personales") == "completado"
        return bool(case_data.get("nombre")) and completed

    def generate_recognition_message(self, collected_data: dict) -> str:
        nombre = collected_data.get("nombre", "¡Hola!")
        fases = collected_data.get("phases", {})
        f1 = "✅ Completado" if fases.get("datos_personales") == "completado" else "⏳ Pendiente"
        f2 = "✅ Completado" if fases.get("documentacion") == "completado" else "⏳ Pendiente"
        return (
            f"¡Hola {nombre}! Te recuerdo de tu trámite de divorcio.\n\n"
            f"📋 Estado actual:\n"
            f"• Fase 1: Datos personales {f1}\n"
            f"• Fase 2: Documentación {f2}\n\n"
            f"¿Querés continuar enviando los documentos o tenés alguna consulta?"
        )
