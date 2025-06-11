"""Test importing RAG parameter sets."""

from src.backend.rag_pipeline.config.parameter_sets import (
    FAST_ANSWERS,
    get_param_set,
)


def test_get_fast_parameters():
    """Ensure the 'fast' parameter set can be imported and retrieved."""
    fast_params = get_param_set("fast")
    assert fast_params == FAST_ANSWERS

