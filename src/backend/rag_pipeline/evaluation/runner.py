"""Evaluation runner: runs retrieval over a dataset and computes metrics.

Loads benchmark JSON, runs each config (dense, sparse, hybrid) against
each question, computes Precision@5, Recall@5, MRR, Hit@5.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from backend.rag_pipeline.evaluation.metrics import (
    EvaluationResult,
    compute_aggregates,
    hit_rate_at_k,
    mrr,
    precision_at_k,
    recall_at_k,
)


def evaluate_retrieval(
    dataset: list[dict[str, Any]],
    retrieve_fn: Callable[[str, int], list[dict[str, Any]]],
    top_k: int = 5,
) -> list[EvaluationResult]:
    """Evaluate retrieval over a dataset.

    Args:
        dataset: List of items with 'question' and 'ground_truth_contexts'.
        retrieve_fn: Callable(query, top_k) -> list of chunk dicts with 'text'.
        top_k: Number of chunks to retrieve per query.

    Returns:
        List of EvaluationResult, one per dataset item.
    """
    results: list[EvaluationResult] = []
    for item in dataset:
        question = item.get("question", "")
        gt = item.get("ground_truth_contexts", [])
        if not question or not gt:
            continue
        retrieved = retrieve_fn(question, top_k)
        results.append(
            EvaluationResult(
                question=question,
                precision_at_5=precision_at_k(retrieved, gt, top_k),
                recall_at_5=recall_at_k(retrieved, gt, top_k),
                mrr=mrr(retrieved, gt),
                hit_at_5=hit_rate_at_k(retrieved, gt, top_k),
            )
        )
    return results


def run_evaluation(
    dataset_path: str | Path,
    configs: list[str] | None = None,
    retrieve_fn_factory: Callable[[str], Callable[[str, int], list[dict[str, Any]]]] | None = None,
    top_k: int = 5,
) -> dict[str, dict[str, Any]]:
    """Run evaluation for multiple configs and return results.

    Args:
        dataset_path: Path to JSON benchmark file.
        configs: List of strategy names (e.g. ['dense', 'hybrid']). Default: ['dense', 'sparse', 'hybrid'].
        retrieve_fn_factory: Callable(config_name) -> retrieve_fn. If None, uses real RetrievalService.
        top_k: Retrieval top-k.

    Returns:
        Dict mapping config_name -> {
            'results': [EvaluationResult, ...],
            'aggregates': {mrr, recall_at_5, hit_at_5, precision_at_5, num_queries}
        }
    """
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    with open(path, encoding="utf-8") as f:
        dataset = json.load(f)
    if not isinstance(dataset, list):
        raise ValueError("Dataset must be a JSON array")

    configs = configs or ["dense", "sparse", "hybrid"]
    out: dict[str, dict[str, Any]] = {}

    if retrieve_fn_factory is None:
        retrieve_fn_factory = _default_retrieve_factory()

    for config_name in configs:
        retrieve_fn = retrieve_fn_factory(config_name)
        results = evaluate_retrieval(dataset, retrieve_fn, top_k=top_k)
        aggregates = compute_aggregates(results)
        out[config_name] = {
            "results": [r.to_dict() for r in results],
            "aggregates": {k: round(v, 4) if isinstance(v, float) else v for k, v in aggregates.items()},
        }

    return out


def _default_retrieve_factory() -> Callable[[str], Callable[[str, int], list[dict[str, Any]]]]:
    """Build retrieve function factory using real RetrievalService from env."""

    def factory(config_name: str) -> Callable[[str, int], list[dict[str, Any]]]:
        from backend.rag_pipeline.config.parameter_sets import DEFAULT_PARAM_SET_NAME, get_param_set
        from backend.rag_pipeline.core.retrieval import create_retrieval_service
        from backend.rag_pipeline.core.vector_store import get_vector_store_manager_from_env

        vsm = get_vector_store_manager_from_env()
        params = get_param_set(DEFAULT_PARAM_SET_NAME)
        persist_dir = str(vsm.config.persist_directory)
        model_name = params.embedding.model_name
        collection_name = vsm.config.collection_name
        ret = params.retrieval

        service = create_retrieval_service(
            strategy=config_name,
            model_name=model_name,
            persist_dir=persist_dir,
            collection_name=collection_name,
            hybrid_alpha=ret.hybrid_alpha,
            use_reranker=ret.use_reranker,
            reranker_model=ret.reranker_model,
            use_mmr=ret.use_mmr,
            mmr_lambda=ret.mmr_lambda,
            rerank_candidates=ret.rerank_candidates,
        )

        def retrieve(query: str, top_k: int) -> list[dict[str, Any]]:
            return service.retrieve(query=query, top_k=top_k, similarity_threshold=0.0)

        return retrieve

    return factory
