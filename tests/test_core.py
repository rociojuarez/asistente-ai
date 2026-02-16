"""
Tests del asistente de soporte al cliente.
Ejecutar desde la raíz del proyecto: pytest tests/ -v
Requiere OPENAI_API_KEY en .env (los tests que llaman a la API consumen tokens).
"""

import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from src.run_query import ask


def test_response_json_schema():
    """
    Llama a ask() con una pregunta fija y verifica la estructura del resultado y el esquema JSON.
    Requiere OPENAI_API_KEY en .env (consume tokens).
    """
    result = ask("¿Cómo restablezco mi contraseña?")

    assert isinstance(result, dict), "El resultado debe ser un diccionario"
    assert "response" in result, "Debe existir la clave 'response'"
    assert "metrics" in result, "Debe existir la clave 'metrics'"

    resp = result["response"]
    assert isinstance(resp, dict), "response debe ser un diccionario JSON parseado"

    assert "answer" in resp, "response debe contener 'answer'"
    assert "confidence" in resp, "response debe contener 'confidence'"
    assert "actions" in resp, "response debe contener 'actions'"

    assert isinstance(resp["answer"], str), "answer debe ser string"
    assert isinstance(resp["actions"], list), "actions debe ser lista"
    assert all(isinstance(a, str) for a in resp["actions"]), "cada action debe ser string"
    assert 0 <= resp["confidence"] <= 1, "confidence debe estar entre 0 y 1"


def test_metrics_has_required_keys():
    """Comprueba que las métricas incluyan todos los campos requeridos."""
    result = ask("¿Dónde cambio mi correo?")

    metrics = result["metrics"]
    required = {"prompt_tokens", "completion_tokens", "total_tokens", "latency_ms", "estimated_cost_usd"}
    assert required <= set(metrics.keys()), f"Las métricas deben incluir {required}"
    assert metrics["prompt_tokens"] >= 0
    assert metrics["completion_tokens"] >= 0
    assert metrics["latency_ms"] >= 0
    assert metrics["estimated_cost_usd"] >= 0
