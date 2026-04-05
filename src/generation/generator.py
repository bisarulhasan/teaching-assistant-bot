"""Generate answers from retrieved context using an LLM with citation enforcement."""

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from src.config.settings import get_system_prompt, get_query_template, LLM_MODEL


def format_context(retrieved_chunks: list[dict]) -> str:
    """Format retrieved chunks into a context string for the LLM."""
    template = get_query_template("format_context")
    context_parts = []
    
    for i, chunk in enumerate(retrieved_chunks, 1):
        formatted = template.format(
            chunk_number=i,
            source_file=chunk["metadata"].get("source_file", "Unknown"),
            page=chunk["metadata"].get("page", "?"),
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
    
    # llm = ChatOllama(model="qwen2.5:7b", temperature=0)
    llm = ChatOllama(model="gemma4", temperature=0)
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ])
    
    # Extract unique sources used
    sources = []
    seen = set()
    for chunk in retrieved_chunks:
        source_key = (
            chunk["metadata"].get("source_file", ""),
            chunk["metadata"].get("page", 0),
        )
        if source_key not in seen:
            seen.add(source_key)
            sources.append({
                "file": source_key[0],
                "page": source_key[1],
            })
    
    return {
        "answer": response.content,
        "sources": sources,
        "context_used": retrieved_chunks,
    }