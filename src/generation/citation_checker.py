"""Citation enforcement — decline to answer if context doesn't support the response."""

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage



VERIFICATION_PROMPT = """You are a citation verification system. Your job is to determine 
whether a generated answer is fully supported by the provided context chunks.

Analyze the answer and for each claim, check if it is directly supported by the context.

Respond in this exact format:
SUPPORTED: yes/no
CONFIDENCE: high/medium/low  
UNSUPPORTED_CLAIMS: [list any claims not found in context, or "none"]
REASONING: [brief explanation]"""


def verify_answer_against_context(
    question: str,
    answer: str,
    context_chunks: list[dict],
) -> dict:
    """
    Verify that the generated answer is supported by the retrieved context.
    
    This implements citation enforcement: if the answer contains claims
    not supported by the context, flag it and suggest declining to answer.
    
    Returns:
        Dict with 'is_supported', 'confidence', 'unsupported_claims', 'reasoning'.
    """
    context_text = "\n\n".join(
        f"[Chunk {i+1}]: {chunk['content']}" 
        for i, chunk in enumerate(context_chunks)
    )
    
    llm = ChatOllama(model="qwen2.5:7b", temperature=0)
    
    response = llm.invoke([
        SystemMessage(content=VERIFICATION_PROMPT),
        HumanMessage(content=f"""
Context Chunks:
{context_text}

Question: {question}

Generated Answer: {answer}

Verify whether the answer is fully supported by the context."""),
    ])
    
    # Parse the response
    text = response.content
    result = {
        "is_supported": "SUPPORTED: yes" in text.lower() or "supported: yes" in text.lower(),
        "confidence": "high" if "CONFIDENCE: high" in text else 
                     "medium" if "CONFIDENCE: medium" in text else "low",
        "raw_verification": text,
    }
    
    return result