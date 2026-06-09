"""FastAPI server for the teaching-assistant RAG bot.

Students pick their year / subject / course on the frontend; the API scopes
retrieval to those textbooks and returns a grounded, citation-checked answer.

Heavy resources (Weaviate client, BM25 index, embedding model) are initialized
once at startup and reused across requests — rebuilding them per request would
make each query take many seconds.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config.settings import LLM_MODEL, VECTOR_DB
from src.ingestion.embedder import get_vector_client
from src.retrieval.bm25_retriever import BM25Retriever
from src.pipeline import query as run_query


# ----- Request / response models -------------------------------------------------

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    year: int | None = None
    subject: str | None = None
    course: str | None = None
    verify: bool = True


class Source(BaseModel):
    file: str = ""
    page: int = 0
    year: int = 0
    subject: str = ""
    course: str = ""
    chapter: int = 0
    chapter_title: str = ""
    section: str = ""
    label: str = ""


class AskResponse(BaseModel):
    answer: str
    sources: list[Source] = []
    is_supported: bool | None = None
    confidence: str | None = None


# ----- App lifecycle -------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm the active embedding model and open shared resources once.
    if VECTOR_DB == "qdrant":
        from src.ingestion.embeddings import embed_query
        embed_query("warmup")
    else:
        from src.retrieval.vector_retriever import get_embeddings_model
        get_embeddings_model()
    app.state.client = get_vector_client()
    app.state.bm25 = BM25Retriever(app.state.client)
    try:
        yield
    finally:
        app.state.client.close()


app = FastAPI(title="Teaching Assistant Bot", version="1.0.0", lifespan=lifespan)

# CORS: set FRONTEND_ORIGIN (comma-separated) to the Vercel domain in production.
_origins = [o.strip() for o in os.getenv("FRONTEND_ORIGIN", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----- Endpoints -----------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model": LLM_MODEL}


@app.get("/catalog")
def catalog() -> dict:
    """Available year / subject / course combinations for the student picker.

    Derived from the in-memory BM25 corpus (already loaded at startup), so this
    is free — no extra Weaviate calls.
    """
    combos = {
        (d["metadata"].get("year", 0),
         d["metadata"].get("subject", ""),
         d["metadata"].get("course", ""))
        for d in app.state.bm25.documents
    }
    items = [
        {"year": y, "subject": s, "course": c}
        for (y, s, c) in sorted(combos)
        if s
    ]
    return {"catalog": items}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    filters = {"year": req.year, "subject": req.subject, "course": req.course}
    result = run_query(
        req.question,
        verify=req.verify,
        filters=filters,
        client=app.state.client,
        bm25=app.state.bm25,
    )
    verification = result.get("verification") or {}
    return AskResponse(
        answer=result["answer"],
        sources=result.get("sources", []),
        is_supported=verification.get("is_supported"),
        confidence=verification.get("confidence"),
    )
