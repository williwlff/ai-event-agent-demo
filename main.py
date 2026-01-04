from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import os
import uuid
import logging
from typing import Dict, Any, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from google import genai

# ---- MODELS ----
from models.event import EventPreview

# ---- SERVICES ----
from services.event_extractor import extract_event_with_llm
from services.event_merge import merge_event
from services.event_validator import validate_event
from services.event_questions import next_missing_question
from services.event_status import event_publication_status
from services.event_preview_renderer import (
    render_event_preview,
    render_event_preview_text
)

# ---- RAG ----
from rag.qdrant import qdrant_search

# -------------------------
# CONFIG
# -------------------------

QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
COLLECTION_NAME = "documents"
EMBEDDING_SIZE = 768
GEMINI_MODEL = "gemini-2.5-flash"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai-event-agent")

# -------------------------
# FASTAPI
# -------------------------

app = FastAPI(title="AI Event Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # per demo ok
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")

@app.get("/", include_in_schema=False)
def serve_frontend():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static"
)



# -------------------------
# API MODELS
# -------------------------

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    session_id: str
    agent_message: str
    event_preview: Dict[str, Any]
    rag_context: List[str]
    publication_status: Dict[str, Any]

# -------------------------
# CLIENTS
# -------------------------

qdrant_client = QdrantClient(url=QDRANT_URL)

genai_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# -------------------------
# INIT QDRANT
# -------------------------

def init_qdrant():
    collections = [
        c.name for c in qdrant_client.get_collections().collections
    ]

    if COLLECTION_NAME not in collections:
        logger.info("📦 Creo collezione Qdrant")
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_SIZE,
                distance=Distance.COSINE
            )
        )

init_qdrant()

# -------------------------
# SESSION STATE (in-memory)
# -------------------------

sessions: Dict[str, Dict[str, Any]] = {}

# -------------------------
# CHAT ENDPOINT
# -------------------------

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # 1️⃣ SESSIONE
    session_id = req.session_id or str(uuid.uuid4())

    if session_id not in sessions:
        sessions[session_id] = {
            "event_preview": {}
        }

    state = sessions[session_id]

    # 2️⃣ RAG (contesto documentale)
    rag_context = qdrant_search(
        qdrant_client,
        COLLECTION_NAME,
        req.message
    )

    # 3️⃣ ESTRAZIONE STRUTTURATA (LLM → JSON)
    extracted_data = extract_event_with_llm(
        client=genai_client,
        model=GEMINI_MODEL,
        message=req.message,
        current_event=state["event_preview"]
    )

    # 4️⃣ MERGE INCREMENTALE
    state["event_preview"] = merge_event(
        state["event_preview"],
        extracted_data
    )

    # 5️⃣ VALIDAZIONE
    errors: List[str] = []
    try:
        event = EventPreview(**state["event_preview"])
        publication = event_publication_status(event)
        preview_structured = render_event_preview(event)
        preview_text = render_event_preview_text(event)
        if publication["status"] == "READY":
            agent_message = (
                "✅ L’evento è pronto alla pubblicazione!\n\n"
                "Ecco il riepilogo finale:\n\n"
                f"{preview_text}\n\n"
                "Vuoi pubblicarlo?"
            )

        errors = validate_event(event)
        next_question = next_missing_question(event)
        if next_question:
            agent_message = next_question

    except Exception as e:
        errors.append(str(e))

    if errors:
        logger.info(f"⚠️ Errori validazione: {errors}")

    # 6️⃣ RISPOSTA CONVERSAZIONALE
    system_prompt = """
Sei un assistente che aiuta a creare eventi per un sistema di biglietteria.
Guida l’utente passo passo e chiedi le informazioni mancanti.
"""

    response = genai_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            system_prompt,
            req.message
        ]
    )

    agent_message = response.text or "Perfetto, continuiamo."

    # 7️⃣ RESPONSE
    return ChatResponse(
        session_id=session_id,
        agent_message=agent_message,
        event_preview=state["event_preview"],
        rag_context=rag_context,
        publication_status=publication
)

