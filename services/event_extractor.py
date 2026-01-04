import json
import logging
from google import genai

logger = logging.getLogger("event-extractor")


def extract_event_with_llm(
    client: genai.Client,
    model: str,
    message: str,
    current_event: dict
) -> dict:
    """
    Usa il LLM come parser strutturato.
    Deve restituire SOLO JSON valido.
    """

    prompt = f"""
Sei un parser automatico per eventi di un sistema di biglietteria.

⚠️ REGOLE ASSOLUTE:
- Rispondi SOLO con JSON valido
- NON scrivere testo prima o dopo
- NON usare markdown
- NON spiegare nulla
- L'output viene passato direttamente a json.loads()

Stato attuale evento (JSON):
{json.dumps(current_event, ensure_ascii=False)}

Messaggio utente:
"{message}"

Formato JSON di riferimento:
{{
  "name": "string",
  "date": "YYYY-MM-DD",
  "venue": {{
    "address": "string",
    "city": "string"
  }},
  "tickets": [
    {{
      "name": "string",
      "price": 0,
      "currency": "EUR"
    }}
  ]
}}

Istruzioni:
- Estrai SOLO i campi presenti nel messaggio
- Non inventare nulla
- Prezzi come numeri
- Valuta sempre EUR
- Se non trovi informazioni utili, restituisci {{}}

JSON:
"""

    response = client.models.generate_content(
        model=model,
        contents=[prompt]
    )

    raw_text = response.text or ""

    # 🔍 LOG FONDAMENTALE
    logger.info("🧩 RAW LLM OUTPUT:")
    logger.info(raw_text)

    try:
        parsed = json.loads(raw_text)
        logger.info("✅ JSON parsato correttamente")
        return parsed
    except Exception as e:
        logger.error(f"❌ Errore parsing JSON: {e}")
        return {}
