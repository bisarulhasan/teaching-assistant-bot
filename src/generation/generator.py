"""Generate answers from retrieved context using an LLM with citation enforcement."""

from langchain_core.messages import SystemMessage, HumanMessage
from src.config.settings import get_system_prompt, get_query_template
from src.generation.llm_client import get_chat_llm


def source_label(metadata: dict) -> str:
    """Human-readable citation, e.g.
    'Mathematics Standard (Year 11), Ch 1 Earning money, §1G, p.38'."""
    subject = metadata.get("subject") or ""
    course = metadata.get("course") or ""
    year = metadata.get("year") or 0
    book = " ".join(p for p in (subject, course) if p) or metadata.get("source_file", "Unknown")
    if year:
        book = f"{book} (Year {year})"

    parts = [book]
    if metadata.get("chapter"):
        ch = f"Ch {metadata['chapter']}"
        if metadata.get("chapter_title"):
            ch += f" {metadata['chapter_title']}"
        parts.append(ch)
    if metadata.get("section"):
        parts.append(f"§{metadata['section']}")
    if metadata.get("page"):
        parts.append(f"p.{metadata['page']}")
    return ", ".join(parts)


def format_context(retrieved_chunks: list[dict]) -> str:
    """Format retrieved chunks into a context string for the LLM."""
    template = get_query_template("format_context")
    context_parts = []

    for i, chunk in enumerate(retrieved_chunks, 1):
        formatted = template.format(
            chunk_number=i,
            source=source_label(chunk["metadata"]),
            content=chunk["content"],
        )
        context_parts.append(formatted)

    return "\n".join(context_parts)


def generate_answer(
    query: str,
    retrieved_chunks: list[dict],
    prompt_key: str = "rag_answer",
) -> dict:
    """
    Generate an answer to the query using retrieved context.
    
    Args:
        query: The student's question.
        retrieved_chunks: List of relevant chunks from retrieval.
        prompt_key: Which system prompt to use from prompts.yaml.
        
    Returns:
        Dict with 'answer', 'sources', and 'context_used' keys.
    """
    if not retrieved_chunks:
        return {
            "answer": "I don't have enough information in the course materials to "
                      "answer this question. Please ask your teacher for clarification.",
            "sources": [],
            "context_used": [],
        }
    
    system_prompt = get_system_prompt(prompt_key)
    context_str = format_context(retrieved_chunks)
    
    user_message = f"""Context from course materials:

{context_str}

Student Question: {query}

Please answer the question based ONLY on the context above. Include citations."""
    
    llm = get_chat_llm(temperature=0)
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ])
    
    # Extract unique sources used (one per page), with rich citation metadata
    sources = []
    seen = set()
    for chunk in retrieved_chunks:
        m = chunk["metadata"]
        source_key = (m.get("source_file", ""), m.get("page", 0))
        if source_key not in seen:
            seen.add(source_key)
            sources.append({
                "file": m.get("source_file", ""),
                "page": m.get("page", 0),
                "year": m.get("year", 0),
                "subject": m.get("subject", ""),
                "course": m.get("course", ""),
                "chapter": m.get("chapter", 0),
                "chapter_title": m.get("chapter_title", ""),
                "section": m.get("section", ""),
                "label": source_label(m),
            })
    
    return {
        "answer": response.content,
        "sources": sources,
        "context_used": retrieved_chunks,
    }