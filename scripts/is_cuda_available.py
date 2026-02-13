#!/usr/bin/env python3
"""Run the CUDA availability check.

Use: uv run is-cuda-available
     uv run python scripts/is_cuda_available.py
"""

from backend.rag_pipeline.utils.cuda_check import main

if __name__ == "__main__":
    main()
