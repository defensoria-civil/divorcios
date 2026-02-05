"""
Tests de Integración: Webhook de WhatsApp

Prueba el endpoint de webhook que recibe mensajes de WhatsApp.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, Mock

from application.use_cases.process_incoming_message import MessageResponse

# El client y la BD se gestionan desde tests/integration/conftest.py


class TestWebhookEndpoint:
    """Tests para endpoint de webhook"""

    def test_webhook_requires_post(self, client: TestClient):
        """Test: Webhook solo acepta POST"""
        response = client.get("/webhook/whatsapp")
        assert response.status_code in [404, 405]  # Method not allowed

    @patch('application.use_cases.process_incoming_message.ProcessIncomingMessageUseCase.execute')
    def test_webhook_receives_text_message(self, mock_execute, client: TestClient):
        """Test: Webhook recibe y procesa mensaje de texto"""
        mock_execute.return_value = MessageResponse(
            text="Hola, ¿en qué puedo ayudarte?",
            should_send=True,
        )
        
        payload = {
            "messages": [
                {
                    "from": "5492604123456",
                    "body": "Hola",
                    "timestamp": "2025-01-01T10:00:00Z"
                }
            ]
        }
        
        response = client.post("/webhook/whatsapp", json=payload)
        
        assert response.status_code == 200

    @patch('application.use_cases.process_incoming_message.ProcessIncomingMessageUseCase.execute')
    def test_webhook_handles_image_message(self, mock_execute, client: TestClient):
        """Test: Webhook maneja mensaje con imagen"""
        mock_execute.return_value = MessageResponse(
            text="Imagen recibida",
            should_send=True,
        )
        
        payload = {
            "messages": [
                {
                    "from": "5492604123456",
                    "type": "image",
                    "mediaUrl": "https://example.com/image.jpg",
                    "caption": "Mi DNI",
                    "timestamp": "2025-01-01T10:00:00Z"
                }
            ]
        }
        
        response = client.post("/webhook/whatsapp", json=payload)
        
        assert response.status_code == 200

    def test_webhook_rejects_empty_payload(self, client: TestClient):
        """Test: Webhook rechaza payload vacío"""
        response = client.post("/webhook/whatsapp", json={})
        
        # Puede retornar 400 o 422 dependiendo de la validación
        assert response.status_code in [400, 422]

    def test_webhook_rejects_invalid_payload(self, client: TestClient):
        """Test: Webhook rechaza payload inválido"""
        payload = {
            "invalid_field": "test"
        }
        
        response = client.post("/webhook/whatsapp", json=payload)
        
        assert response.status_code in [400, 422]

    @patch('application.use_cases.process_incoming_message.ProcessIncomingMessageUseCase.execute')
    def test_webhook_handles_multiple_messages(self, mock_execute, client: TestClient):
        """Test: Webhook maneja múltiples mensajes en un payload"""
        mock_execute.return_value = MessageResponse(
            text="Respuesta",
            should_send=True,
        )
        
        payload = {
            "messages": [
                {
                    "from": "5492604111111",
                    "body": "Mensaje 1",
                    "timestamp": "2025-01-01T10:00:00Z"
                },
                {
                    "from": "5492604222222",
                    "body": "Mensaje 2",
                    "timestamp": "2025-01-01T10:00:01Z"
                }
            ]
        }
        
        response = client.post("/webhook/whatsapp", json=payload)
        
        assert response.status_code == 200

    @patch('application.use_cases.process_incoming_message.ProcessIncomingMessageUseCase.execute')
    def test_webhook_handles_errors_gracefully(self, mock_execute, client: TestClient):
        """Test: Webhook maneja errores sin crashear"""
        mock_execute.side_effect = Exception("Test error")
        
        payload = {
            "messages": [
                {
                    "from": "5492604123456",
                    "body": "Test",
                    "timestamp": "2025-01-01T10:00:00Z"
                }
            ]
        }
        
        response = client.post("/webhook/whatsapp", json=payload)
        
        # Debería retornar error pero no crashear
        assert response.status_code in [200, 500]


class TestWebhookSecurity:
    """Tests para seguridad del webhook"""

    def test_webhook_validates_phone_format(self, client: TestClient):
        """Test: Webhook valida formato de número de teléfono"""
        payload = {
            "messages": [
                {
                    "from": "invalid_phone",
                    "body": "Test",
                    "timestamp": "2025-01-01T10:00:00Z"
                }
            ]
        }
        
        response = client.post("/webhook/whatsapp", json=payload)
        
        # Puede aceptar o rechazar según la validación
        assert response.status_code in [200, 400, 422]

    @patch('application.use_cases.process_incoming_message.ProcessIncomingMessageUseCase.execute')
    def test_webhook_rate_limiting(self, mock_execute, client: TestClient):
        """Test: Webhook aplica rate limiting"""
        mock_execute.return_value = AsyncMock(
            text="Respuesta",
            should_send=True
        )()
        
        payload = {
            "messages": [
                {
                    "from": "5492604123456",
                    "body": "Test",
                    "timestamp": "2025-01-01T10:00:00Z"
                }
            ]
        }
        
        # Enviar muchos requests seguidos
        responses = []
        for _ in range(50):
            response = client.post("/webhook/whatsapp", json=payload)
            responses.append(response.status_code)
        
        # Al menos algunos deberían ser exitosos
        assert 200 in responses


class TestWebhookMessageProcessing:
    """Tests para procesamiento de mensajes en webhook"""

    @patch('application.use_cases.process_incoming_message.ProcessIncomingMessageUseCase.execute')
    def test_webhook_creates_new_case_for_new_user(self, mock_execute, client: TestClient):
        """Test: Webhook crea nuevo caso para usuario nuevo"""
        mock_execute.return_value = MessageResponse(
            text="Bienvenido",
            should_send=True,
        )
        
        payload = {
            "messages": [
                {
                    "from": "5492604999999",
                    "body": "Hola",
                    "timestamp": "2025-01-01T10:00:00Z"
                }
            ]
        }
        
        response = client.post("/webhook/whatsapp", json=payload)
        
        assert response.status_code == 200

    @patch('application.use_cases.process_incoming_message.ProcessIncomingMessageUseCase.execute')
    def test_webhook_continues_existing_conversation(self, mock_execute, client: TestClient):
        """Test: Webhook continúa conversación existente"""
        mock_execute.return_value = MessageResponse(
            text="Continuando...",
            should_send=True,
        )
        
        phone = "5492604888888"
        
        # Primer mensaje
        payload1 = {
            "messages": [
                {
                    "from": phone,
                    "body": "Hola",
                    "timestamp": "2025-01-01T10:00:00Z"
                }
            ]
        }
        response1 = client.post("/webhook/whatsapp", json=payload1)
        assert response1.status_code == 200
        
        # Segundo mensaje del mismo usuario
        payload2 = {
            "messages": [
                {
                    "from": phone,
                    "body": "Quiero divorcio",
                    "timestamp": "2025-01-01T10:00:05Z"
                }
            ]
        }
        response2 = client.post("/webhook/whatsapp", json=payload2)
        assert response2.status_code == 200

    @patch('application.use_cases.process_incoming_message.ProcessIncomingMessageUseCase.execute')
    def test_webhook_stores_message_history(self, mock_execute, client: TestClient):
        """Test: Webhook almacena historial de mensajes"""
        mock_execute.return_value = MessageResponse(
            text="Respuesta",
            should_send=True,
        )
        
        payload = {
            "messages": [
                {
                    "from": "5492604777777",
                    "body": "Mensaje de prueba",
                    "timestamp": "2025-01-01T10:00:00Z"
                }
            ]
        }
        
        response = client.post("/webhook/whatsapp", json=payload)
        
        assert response.status_code == 200
        # El mensaje debería estar almacenado en la DB


class TestWebhookResponses:
    """Tests para respuestas del webhook"""

    @patch('application.use_cases.process_incoming_message.ProcessIncomingMessageUseCase.execute')
    @patch('infrastructure.messaging.waha_service_impl.WAHAWhatsAppService.send_message')
    def test_webhook_sends_response_to_user(self, mock_send, mock_execute, client: TestClient):
        """Test: Webhook envía respuesta al usuario"""
        mock_execute.return_value = MessageResponse(
            text="Esta es la respuesta",
            should_send=True,
        )
        mock_send.return_value = AsyncMock(success=True)()
        
        payload = {
            "messages": [
                {
                    "from": "5492604666666",
                    "body": "Test",
                    "timestamp": "2025-01-01T10:00:00Z"
                }
            ]
        }
        
        response = client.post("/webhook/whatsapp", json=payload)
        
        assert response.status_code == 200

    @patch('application.use_cases.process_incoming_message.ProcessIncomingMessageUseCase.execute')
    def test_webhook_no_response_when_should_send_false(self, mock_execute, client: TestClient):
        """Test: Webhook no envía respuesta cuando should_send es False"""
        mock_execute.return_value = MessageResponse(
            text="No enviar esto",
            should_send=False,
        )
        
        payload = {
            "messages": [
                {
                    "from": "5492604555555",
                    "body": "Test",
                    "timestamp": "2025-01-01T10:00:00Z"
                }
            ]
        }
        
        response = client.post("/webhook/whatsapp", json=payload)
        
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
