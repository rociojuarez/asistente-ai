# Informe breve – Asistente de soporte al cliente (M1)

## 1. Visión de arquitectura

El proyecto ofrece un asistente de soporte al cliente que recibe una pregunta del usuario y devuelve una respuesta en JSON más métricas de uso (tokens, latencia, costo estimado). El repositorio es autocontenido: la plantilla del prompt y el código están versionados; la única dependencia externa es la API de OpenAI (mediante `OPENAI_API_KEY`).

**Estructura**

| Ruta | Rol |
|------|------|
| `src/run_query.py` | Script principal: carga el prompt desde `prompts/main_prompt.md`, llama a la API de OpenAI, devuelve JSON y métricas, y añade cada ejecución a `metrics/metrics.json`. |
| `prompts/main_prompt.md` | Prompt basado en instrucciones con Chain-of-Thought, esquema JSON y ejemplos few-shot. |
| `metrics/metrics.json` | Registro por ejecución: timestamp, tokens_prompt, tokens_completion, total_tokens, latency_ms, estimated_cost_usd. |
| `tests/test_core.py` | Tests del esquema JSON de la respuesta y de las claves de métricas (ejecutar con `pytest tests/ -v` desde la raíz del proyecto). |
| `.env` | Configuración local: `OPENAI_API_KEY`, `OPENAI_MODEL` (no se versiona). |

**Flujo**

1. El usuario ejecuta `python src/run_query.py -q "pregunta"`.
2. El script carga `.env` y el prompt de sistema desde `prompts/main_prompt.md`.
3. Una sola llamada a la API con `response_format=json_object`; se mide la latencia alrededor de la llamada.
4. Se parsea la respuesta; tokens y costo se calculan a partir de `usage`.
5. Se imprimen el JSON y las métricas; se añade un registro a `metrics/metrics.json`.

---

## 2. Técnica(s) de prompting y por qué

**Elección:** Chain-of-Thought (CoT) con ejemplos few-shot en la plantilla del prompt.

**Qué hacemos:** El prompt de sistema (en `prompts/main_prompt.md`) indica al modelo que (1) razone en 2–3 pasos breves antes de responder y (2) devuelva un objeto JSON con `chain_of_thought`, `answer`, `confidence` y `actions`. La plantilla incluye dos ejemplos few-shot completos (restablecer contraseña, cambiar correo) y un tercero de referencia de formato, para que el modelo vea el esquema y estilo exactos que queremos.

**Por qué CoT:** Hacer explícito el razonamiento mejora la consistencia y facilita depurar o mejorar respuestas inspeccionando `chain_of_thought`. Además fomenta respuestas de soporte más estructuradas.

**Por qué few-shot aquí:** El entregable exigía al menos algunos ejemplos few-shot en el prompt. Añadimos dos ejemplos pregunta→JSON completos para reducir la deriva de formato y anclar el asistente en flujos de soporte típicos. El trade-off es un prompt más largo (más tokens de entrada por petición).

---

## 3. Resumen de métricas y resultados de muestra

Cada ejecución registra:

- **tokens_prompt** / **tokens_completion** / **total_tokens**: del objeto `usage` de la API.
- **latency_ms**: tiempo real de la llamada a la API.
- **estimated_cost_usd**: calculado con precios de gpt-4o-mini (input ~0,15 USD/1M, output ~0,60 USD/1M).

**Registro de ejemplo** (en `metrics/metrics.json` o tras una ejecución):

| Métrica | Valor de ejemplo |
|--------|-------------------|
| timestamp | 2025-02-16T12:00:00+00:00 |
| tokens_prompt | 312 |
| tokens_completion | 89 |
| total_tokens | 401 |
| latency_ms | 1245.32 |
| estimated_cost_usd | 0.000089 |

Para reproducir: desde la raíz del proyecto con el venv activado, ejecutar `python src/run_query.py -q "¿Cómo restablezco mi contraseña?"` y revisar las métricas impresas y la nueva entrada en `metrics/metrics.json`.

---

## 4. Desafíos y posibles mejoras

**Limitaciones actuales**

- No hay RAG ni base de conocimiento interna: las respuestas dependen solo del conocimiento previo del modelo y del prompt.
- No hay capa de moderación ni seguridad: las entradas adversarias o fuera de tema no se filtran antes de la llamada a la API.
- Los tests que llaman a la API consumen tokens y requieren un `OPENAI_API_KEY` válido.
- Coste y latencia dependen de la longitud del prompt (los ejemplos few-shot aumentan los tokens de entrada).

**Posibles mejoras**

- **Seguridad / moderación (bonus):** Añadir un paso (p. ej. `src/safety.py`) para detectar consultas adversarias o fuera de alcance y devolver un JSON fijo o rechazar, con registro (logging) de las decisiones.
- **RAG:** Conectar un paso de recuperación para que el asistente pueda usar documentación propia del proyecto o actualizada.
- **Caché:** Cachear respuestas para preguntas repetidas o similares y reducir coste y latencia.
- **Validación más estricta:** Validar la salida del modelo contra un esquema JSON (p. ej. Pydantic) antes de devolverla y reintentar o usar fallback en caso de fallo.
