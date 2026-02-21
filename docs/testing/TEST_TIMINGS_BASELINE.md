# Test Timings Baseline

Created: 2025-02-20  
Source: `uv run python -m scripts.test_bottlenecks --run --top 25` (unit tests only, excludes slow/internet/ollama)

## Purpose

Baseline for tracking test duration regressions. Tests marked [SLOW] exceed the unit threshold (1.0s).
Regenerate with: `uv run python -m scripts.test_bottlenecks --run --top 50`

## Top 25 Slowest Unit Tests (baseline)

Updated 2025-02-20 after Task 3: test_document_loader now uses smaller PDF (2005.11401v4.pdf).

| Duration (s) | Test | File |
|-------------|------|------|
| 5.28 [SLOW] | test_websocket_progress_edge_case_completion_cleanup | tests/test_websocket.py |
| 4.09 [SLOW] | test_websocket_connection | tests/test_websocket_connection.py |
| 3.37 [SLOW] | test_upload_multiple_valid_files | tests/test_enhanced_documents_api.py |
| 2.98 [SLOW] | test_reset_memory_manager | tests/backend/memory/test_memory_manager.py |
| 1.97 [SLOW] | test_audit_action_logs_event | tests/backend/guardrails/test_actions.py |
| 1.95 [SLOW] | test_entity_store_property | tests/backend/memory/test_memory_manager.py |
| 1.92 [SLOW] | test_store_long_term | tests/backend/memory/test_memory_manager.py |
| 1.92 [SLOW] | test_access_control_property | tests/backend/memory/test_memory_manager.py |
| 1.87 [SLOW] | test_get_processing_status | tests/test_enhanced_documents_api.py |
| 1.84 [SLOW] | test_upload_single_valid_file | tests/test_enhanced_documents_api.py |
| 1.82 [SLOW] | test_access_denied_for_other_agent | tests/backend/memory/test_memory_manager.py |
| 1.79 [SLOW] | test_vector_memory_property | tests/backend/memory/test_memory_manager.py |
| 1.76 [SLOW] | test_search_long_term | tests/backend/memory/test_memory_manager.py |
| 1.69 [SLOW] | test_store_to_shared | tests/backend/memory/test_memory_manager.py |
| 1.66 [SLOW] | test_search_entities | tests/backend/memory/test_memory_manager.py |
| 1.65 [SLOW] | test_create_context | tests/backend/memory/test_memory_manager.py |
| 1.63 [SLOW] | test_store_entity | tests/backend/memory/test_memory_manager.py |
| 1.63 [SLOW] | test_update_context | tests/backend/memory/test_memory_manager.py |
| 1.63 [SLOW] | test_get_all_short_term | tests/backend/memory/test_memory_manager.py |
| 1.62 [SLOW] | test_session_store_property | tests/backend/memory/test_memory_manager.py |
| 1.61 [SLOW] | test_clear_short_term | tests/backend/memory/test_memory_manager.py |
| 1.61 [SLOW] | test_get_stats | tests/backend/memory/test_memory_manager.py |

## Notes

- Unit test marker: `-m "not slow and not internet and not ollama and not docker"`
- Thresholds: unit >1s, integration >5s (see `scripts/test_bottlenecks.py --help`)
- CI: ~72s total for ~694 unit tests (after Task 3 optimization)
