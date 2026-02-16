# M1 – Asistente de soporte al cliente

CLI que envía una pregunta del usuario a la API de OpenAI y devuelve una respuesta en JSON estructurado (`answer`, `confidence`, `actions`) más métricas por ejecución. El repositorio es autocontenido; el único requisito externo es una API key de OpenAI.

## Setup

1. Clonar el repositorio.
2. Crear un entorno virtual e instalar dependencias:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Copiar la plantilla de entorno y configurar tu API key:

   ```bash
   cp .env.example .env
   # Editar .env y poner OPENAI_API_KEY=tu-key-aquí
   ```

## Variables de entorno

| Variable | Obligatoria | Descripción |
|----------|-------------|-------------|
| `OPENAI_API_KEY` | Sí | Tu API key de OpenAI. Configúrala en `.env` (no subas `.env` al repo). |
| `OPENAI_MODEL` | No | Nombre del modelo; por defecto `gpt-4o-mini`. |

Ver `.env.example` como plantilla. No subas nunca `.env` ni claves reales.

## Comandos de ejecución

Desde la raíz del proyecto con el venv activado:

```bash
python src/run_query.py -q "¿Cómo restablezco mi contraseña?"
```

- `-q` / `--question`: pregunta del usuario (obligatorio).
- Salida: se imprime el JSON de respuesta por stdout, luego las métricas y una nota de que la ejecución se añadió a `metrics/metrics.json`.

## Reproducir métricas

- Cada ejecución de `python src/run_query.py -q "..."` añade un registro a `metrics/metrics.json`.
- Campos por registro: `timestamp`, `tokens_prompt`, `tokens_completion`, `total_tokens`, `latency_ms`, `estimated_cost_usd`.
- Para obtener tu propia muestra: ejecuta una o dos consultas como arriba y abre `metrics/metrics.json` o revisa el bloque “METRICS” en la salida del script.
- El repo incluye un registro de ejemplo para cumplir “al menos una ejecución registrada” sin tener que ejecutar el script.

## Tests

Desde la raíz del proyecto:

```bash
pytest tests/ -v
```

- Requiere `OPENAI_API_KEY` en `.env`. Los tests que llaman a la API consumen unos pocos tokens.
- `tests/test_core.py` incluye: (1) validación del esquema JSON (la respuesta tiene `answer`, `confidence`, `actions` con tipos correctos; `confidence` en [0, 1]), (2) comprobación de que las métricas tengan las claves requeridas.

## Limitaciones conocidas

- Depende de la API de OpenAI; no hay modo offline.
- No hay RAG ni base de conocimiento propia; las respuestas dependen solo del modelo y del prompt.
- No hay capa de moderación ni seguridad; las entradas inapropiadas o adversarias no se filtran.
- Los tests de integración llaman a la API real y consumen tokens; ejecutarlos solo cuando haga falta.

## Estructura del proyecto

- `src/run_query.py` – script principal (carga prompt, llama API, registra métricas).
- `prompts/main_prompt.md` – prompt de sistema (instrucciones, esquema JSON, ejemplos few-shot).
- `metrics/metrics.json` – registro de ejecuciones (timestamp + tokens + latencia + costo).
- `reports/PI_report_en.md` – informe breve (arquitectura, prompting, métricas, desafíos).
- `tests/test_core.py` – tests del esquema de respuesta y de las métricas.

Para más detalle, ver `reports/PI_report_en.md`.
