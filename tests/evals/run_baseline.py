"""
Centaurus Retrieval Evaluation Runner.
Evaluates retrieval accuracy (Recall@1, Recall@3, MRR) on the golden dataset.
"""
import os
import sys
import json
import time
from typing import List, Dict, Any

# Ensure parent directory is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.config import settings
from backend.services import knowledge_base

def load_golden_set(file_path: str = "tests/evals/golden.json") -> List[Dict[str, Any]]:
    """Loads the golden dataset from disk."""
    if not os.path.exists(file_path):
        print(f"Error: Golden set not found at {file_path}")
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_evaluation() -> Dict[str, Any]:
    """Runs retrieval evaluation and returns metrics."""
    golden_set = load_golden_set()
    if not golden_set:
        return {}

    print(f"Starting evaluation of {len(golden_set)} queries...")
    print(f"Mode: {'MOCK (Keyword)' if settings.is_mock_mode else 'LIVE (Qdrant Hybrid)'}")

    # Build cache / initialize collection
    knowledge_base.build_kb_cache()

    results = []
    recalls_at_1 = 0
    recalls_at_3 = 0
    reciprocal_ranks = []
    latencies = []

    for i, case in enumerate(golden_set, start=1):
        query = case["query"]
        expected_chunk = case["expected_chunk_id"]
        expected_sec = case["expected_section"]

        start_time = time.perf_counter()
        # Retrieve top 3
        retrieved = knowledge_base.search_knowledge_base_hybrid(query, top_k=3)
        latency = (time.perf_counter() - start_time) * 1000  # ms
        latencies.append(latency)

        top_1_hit = False
        top_3_hit = False
        rank = 0

        # Find the rank of the expected chunk
        for r_idx, doc in enumerate(retrieved, start=1):
            doc_chunk_id = doc["metadata"].get("chunk_id")
            doc_section = doc["metadata"].get("section")
            
            # Match either by chunk ID slug or section name
            if doc_chunk_id == expected_chunk or doc_section == expected_sec:
                rank = r_idx
                if rank == 1:
                    top_1_hit = True
                    recalls_at_1 += 1
                top_3_hit = True
                recalls_at_3 += 1
                break

        rr = 1.0 / rank if rank > 0 else 0.0
        reciprocal_ranks.append(rr)

        results.append({
            "query": query,
            "expected_chunk_id": expected_chunk,
            "latency_ms": latency,
            "rank_found": rank,
            "retrieved": [
                {
                    "chunk_id": d["metadata"].get("chunk_id"),
                    "section": d["metadata"].get("section"),
                    "score": d["score"]
                }
                for d in retrieved
            ]
        })

    # Aggregate metrics
    total = len(golden_set)
    recall_1 = recalls_at_1 / total
    recall_3 = recalls_at_3 / total
    mrr = sum(reciprocal_ranks) / total
    avg_latency = sum(latencies) / total

    metrics = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mode": "mock" if settings.is_mock_mode else "live",
        "total_queries": total,
        "recall_at_1": recall_1,
        "recall_at_3": recall_3,
        "mrr": mrr,
        "avg_latency_ms": avg_latency,
        "details": results
    }

    # Write report
    report_path = "tests/evals/baseline_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # Print Summary Table
    print("\n" + "=" * 50)
    print("           RETRIEVAL EVALUATION REPORT")
    print("=" * 50)
    print(f"Mode:            {'MOCK (Keyword)' if settings.is_mock_mode else 'LIVE (Qdrant Hybrid)'}")
    print(f"Total Queries:   {total}")
    print(f"Recall@1:        {recall_1:.2%}")
    print(f"Recall@3:        {recall_3:.2%}")
    print(f"MRR:             {mrr:.4f}")
    print(f"Avg Latency:     {avg_latency:.2f} ms")
    print("=" * 50)
    print(f"Detailed logs saved to {report_path}\n")

    return metrics

if __name__ == "__main__":
    run_evaluation()
