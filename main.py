import os
import uuid
import logging
from typing import Dict, Any, List, Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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

# ---- RAG (DISABLED) ----
from rag.qdrant import qdrant_search

# -------------------------
# CONFIG
# -------------------------

GEMINI_MODEL = "gemini-2.5-flash"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai-event-agent")

# -------------------------
# FASTAPI
# -------------------------

app = FastAPI(title="AI Event Agent – Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# FRONTEND (STATIC)
# -------------------------

BASE_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

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
    publication_status: Dict[str, Any]

# -------------------------
# CLIENTS
# -------------------------

genai_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# Qdrant COMPLETAMENTE DISABILITATO
qdrant_client = None
COLLECTION_NAME = "documents"

# -------------------------
# SESSION STATE (IN-MEMORY)
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

    # 2️⃣ RAG (DISABILITATO → [] )
    _ = qdrant_search(
        qdrant_client,
        COLLECTION_NAME,
        req.message
    )

    # 3️⃣ ESTRAZIONE STRUTTURATA (LLM → JSON)
    extracted = extract_event_with_llm(
        client=genai_client,
        model=GEMINI_MODEL,
        message=req.message,
        current_event=state["event_preview"]
    )

    # 4️⃣ MERGE INCREMENTALE
    state["event_preview"] = merge_event(
        state["event_preview"],
        extracted
    )

    # 5️⃣ VALIDAZIONE + STATUS
    event = EventPreview(**state["event_preview"])
    publication = event_publication_status(event)

    # 6️⃣ DOMANDE AUTOMATICHE
    next_question = next_missing_question(event)

    # 7️⃣ PREVIEW FINALE
    preview_text = render_event_preview_text(event)

    # 8️⃣ MESSAGGIO AGENTE
    if publication["status"] == "READY":
        agent_message = (
            "✅ L’evento è pronto alla pubblicazione!\n\n"
            "Ecco il riepilogo finale:\n\n"
            f"{preview_text}\n\n"
            "Vuoi pubblicarlo?"
        )
    elif next_question:
        agent_message = next_question
    else:
        agent_message = "Perfetto, continuiamo."

    logger.info(f"🧠 Sessione {session_id}")
    logger.info(f"📄 Event preview: {state['event_preview']}")

    return ChatResponse(
        session_id=session_id,
        agent_message=agent_message,
        event_preview=state["event_preview"],
        publication_status=publication
    )
