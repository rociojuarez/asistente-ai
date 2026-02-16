"""
Asistente de soporte al cliente: recibe una pregunta del usuario y devuelve JSON + métricas.
Carga el prompt desde prompts/main_prompt.md y añade cada ejecución a metrics/metrics.json.
"""

import os
import json
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_COST_PER_1M = 0.15
OUTPUT_COST_PER_1M = 0.60


def load_system_prompt() -> str:
    """Carga el prompt principal desde prompts/main_prompt.md."""
    path = PROJECT_ROOT / "prompts" / "main_prompt.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def get_client() -> OpenAI:
    """Carga .env y devuelve el cliente OpenAI configurado."""
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Copy .env.example to .env and set your key.")
    return OpenAI(api_key=api_key)


def ask(question: str) -> dict:
    """
    Ejecuta una pregunta: llama a la API de OpenAI y devuelve el JSON de respuesta y métricas.

    Returns:
        dict con "response" (JSON parseado) y "metrics" (tokens, latencia, costo).
    """
    client = get_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    system_prompt = load_system_prompt()

    start = time.perf_counter()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    latency_ms = (time.perf_counter() - start) * 1000

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Model returned empty content")
    response_json = json.loads(content)

    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0
    total_tokens = usage.total_tokens if usage else (prompt_tokens + completion_tokens)
    estimated_cost_usd = (
        (prompt_tokens / 1_000_000) * INPUT_COST_PER_1M
        + (completion_tokens / 1_000_000) * OUTPUT_COST_PER_1M
    )

    metrics = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "latency_ms": round(latency_ms, 2),
        "estimated_cost_usd": round(estimated_cost_usd, 6),
    }
    return {"response": response_json, "metrics": metrics}


def append_metrics(metrics: dict) -> None:
    """Añade una ejecución a metrics/metrics.json (crea archivo y directorio si no existen)."""
    metrics_dir = PROJECT_ROOT / "metrics"
    metrics_dir.mkdir(exist_ok=True)
    path = metrics_dir / "metrics.json"
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tokens_prompt": metrics["prompt_tokens"],
        "tokens_completion": metrics["completion_tokens"],
        "total_tokens": metrics["total_tokens"],
        "latency_ms": metrics["latency_ms"],
        "estimated_cost_usd": metrics["estimated_cost_usd"],
    }
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = []
    data.append(record)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Asistente de soporte al cliente – consulta y obtén JSON + métricas")
    parser.add_argument("-q", "--question", type=str, required=True, help="Pregunta del usuario")
    args = parser.parse_args()

    result = ask(args.question)

    print("=== RESPUESTA JSON ===")
    print(json.dumps(result["response"], ensure_ascii=False, indent=2))
    print("\n=== MÉTRICAS ===")
    for k, v in result["metrics"].items():
        print(f"  {k}: {v}")

    append_metrics(result["metrics"])
    print("\n(Métricas añadidas a metrics/metrics.json)")
