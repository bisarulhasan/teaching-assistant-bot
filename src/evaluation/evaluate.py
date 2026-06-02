"""Offline evaluation using RAGAS framework against the golden dataset."""

import json
import sys
from pathlib import Path
from datasets import Dataset
from ragas import evaluate
from ragas.run_config import RunConfig
from ragas.metrics._faithfulness import Faithfulness
from ragas.metrics._answer_relevance import AnswerRelevancy
from ragas.metrics._context_precision import ContextPrecision
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from src.pipeline import query as rag_query
from src.config.settings import (
    FAITHFULNESS_THRESHOLD,
    ANSWER_RELEVANCY_THRESHOLD,
    CONTEXT_PRECISION_THRESHOLD,
)


def load_golden_dataset(path: str = "data/eval/golden_dataset.json") -> list[dict]:
    """Load the curated golden evaluation dataset."""
    with open(path) as f:
        data = json.load(f)
    print(f"Loaded {len(data['entries'])} evaluation entries (v{data['version']})")
    return data["entries"]


def run_evaluation(
    dataset_path: str = "data/eval/golden_dataset.json",
    output_path: str = "data/eval/eval_results.json",
    sample_size: int | None = None,
) -> dict:
    """
    Run the full RAGAS evaluation pipeline.
    
    For each question in the golden dataset:
    1. Run it through the RAG pipeline
    2. Collect the answer + retrieved contexts
    3. Evaluate with RAGAS metrics
    """
    entries = load_golden_dataset(dataset_path)
    
    if sample_size:
        entries = entries[:sample_size]
    
    # Run each question through the pipeline
    questions = []
    answers = []
    contexts = []
    ground_truths = []
    
    print(f"\nRunning {len(entries)} queries through RAG pipeline...")
    
    for i, entry in enumerate(entries):
        print(f"  [{i+1}/{len(entries)}] {entry['question'][:60]}...")
        
        try:
            result = rag_query(
                entry["question"],
                verify=False,
                filters={
                    "year": entry.get("year"),
                    "subject": entry.get("subject"),
                    "course": entry.get("course"),
                },
            )
            
            questions.append(entry["question"])
            answers.append(result["answer"])
            contexts.append([c["content"] for c in result.get("context_used", [])])
            ground_truths.append(entry["ground_truth_answer"])
        except Exception as e:
            print(f"    ERROR: {e}")
            questions.append(entry["question"])
            answers.append("Error during generation")
            contexts.append([])
            ground_truths.append(entry["ground_truth_answer"])
    
    # Build RAGAS dataset
    eval_dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })
    
    # Set up local LLM and embeddings for RAGAS evaluation
    print("\nRunning RAGAS evaluation with local models...")
    
    eval_llm = LangchainLLMWrapper(ChatOllama(model="qwen2.5:7b", temperature=0))
    # eval_llm = LangchainLLMWrapper(ChatOllama(model="gemma4", temperature=0))
    eval_embeddings = LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "mps"},
    ))
    
    # Initialize metrics
    faithfulness_metric = Faithfulness(llm=eval_llm)
    answer_relevancy_metric = AnswerRelevancy(llm=eval_llm, embeddings=eval_embeddings)
    context_precision_metric = ContextPrecision(llm=eval_llm)
    
    run_config = RunConfig(
        timeout=900,        # 5 minutes per LLM call (local models are slow)
        max_retries=2,
        max_wait=360,
    )

    results = evaluate(
        dataset=eval_dataset,
        metrics=[faithfulness_metric, answer_relevancy_metric, context_precision_metric],
        run_config=run_config,
    )
    
    # Extract scores — handle both old and new RAGAS formats
    def extract_score(value):
        if isinstance(value, list):
            return sum(v for v in value if v is not None) / max(len([v for v in value if v is not None]), 1)
        return float(value)
    
    scores = {
        "faithfulness": extract_score(results["faithfulness"]),
        "answer_relevancy": extract_score(results["answer_relevancy"]),
        "context_precision": extract_score(results["context_precision"]),
    }
    
    # Check against thresholds
    thresholds = {
        "faithfulness": FAITHFULNESS_THRESHOLD,
        "answer_relevancy": ANSWER_RELEVANCY_THRESHOLD,
        "context_precision": CONTEXT_PRECISION_THRESHOLD,
    }
    
    passed = all(
        scores[metric] >= thresholds[metric] 
        for metric in thresholds
    )
    
    output = {
        "scores": scores,
        "thresholds": thresholds,
        "passed": passed,
        "num_evaluated": len(entries),
    }
    
    # Save results
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    # Print report
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    for metric, score in scores.items():
        threshold = thresholds[metric]
        status = "PASS" if score >= threshold else "FAIL"
        print(f"  {metric:25s}: {score:.4f} (threshold: {threshold}) [{status}]")
    print(f"\n  Overall: {'PASSED' if passed else 'FAILED'}")
    print("=" * 60)
    
    return output


if __name__ == "__main__":
    sample = int(sys.argv[1]) if len(sys.argv) > 1 else None
    result = run_evaluation(sample_size=sample)
    
    if not result["passed"]:
        sys.exit(1)