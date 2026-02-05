import json
from pathlib import Path

import pytest

from application.services.conversation_engine import ConversationEngine


@pytest.mark.evaluation
@pytest.mark.asyncio
async def test_conversation_against_golden_dataset(db_session):
    """Evalúa el comportamiento del agente contra un golden dataset sencillo.

    Este test NO llama a LLMs externos: se limita a las primeras fases
    del flujo (inicio, tipo de divorcio, datos personales), de modo que
    es estable y puede correr en CI sin depender de API keys.
    """
    engine = ConversationEngine(db=db_session)

    dataset_path = Path(__file__).with_name("golden_dataset.json")
    data = json.loads(dataset_path.read_text(encoding="utf-8"))

    assert data, "El golden_dataset.json no debe estar vacío"

    for scenario in data:
        phone = scenario["phone"]
        steps = scenario["steps"]

        for step in steps:
            input_text = step["input"]
            expected_contains = step.get("expected_contains")
            prohibited = step.get("prohibited_substrings", [])

            response = await engine.handle_incoming(phone, input_text)

            if expected_contains:
                assert expected_contains.lower() in response.lower(), (
                    f"En el escenario '{scenario['name']}', se esperaba que la respuesta "
                    f"contuviera: '{expected_contains}', pero se obtuvo: '{response}'"
                )

            for bad in prohibited:
                assert bad.lower() not in response.lower(), (
                    f"En el escenario '{scenario['name']}', la respuesta contiene texto prohibido: "
                    f"'{bad}'. Respuesta: '{response}'"
                )
