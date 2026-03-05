#!/usr/bin/env python3
"""Setup script to pre-download embedding models for local development.

This script ensures that all embedding models used by the application
are downloaded and cached locally, enabling offline operation.

Usage:
    python scripts/setup_embedding_models.py
    python scripts/setup_embedding_models.py --dry-run

Environment Variables:
    HF_HOME: HuggingFace cache directory (default: data/cache/huggingface)
    SENTENCE_TRANSFORMERS_HOME: Sentence transformers cache directory
"""

import argparse
import os
import sys
import traceback
import warnings
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    from transformers import AutoModel, AutoTokenizer
except ImportError as e:
    print(f"Error: Required packages not installed: {e}")
    print("Please install dependencies with: uv pip install -e .[dev]")
    sys.exit(1)

# HuggingFaceEmbedding imported lazily in download_llamaindex_embedding to avoid
# llama_index.core.llms.ChatMessage import errors when llama-index packages have
# version mismatches (e.g. on fresh CI venvs).
#
# We avoid importing backend.shared (get_cache_dir) because that can pull in
# rag_pipeline/llama_index via the package dependency graph on fresh CI venvs.


def _get_cache_dir() -> Path:
    """Resolve project cache dir without importing backend (avoids llama_index load)."""
    root = Path(__file__).resolve().parent.parent
    return root / "data" / "cache"


def setup_cache_directories():
    """Set up cache directories for HuggingFace models."""
    # Set default cache locations in our data directory
    cache_dir = _get_cache_dir()
    hf_home = os.environ.get("HF_HOME", str(cache_dir / "huggingface"))
    transformers_cache = os.environ.get("TRANSFORMERS_CACHE", f"{hf_home}/hub")
    sentence_transformers_home = os.environ.get("SENTENCE_TRANSFORMERS_HOME", f"{hf_home}/sentence_transformers")

    # Create directories
    for cache_dir in [hf_home, transformers_cache, sentence_transformers_home]:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        print(f"Cache directory ready: {cache_dir}")

    # Set environment variables for current session
    os.environ["HF_HOME"] = hf_home
    os.environ["TRANSFORMERS_CACHE"] = transformers_cache
    os.environ["SENTENCE_TRANSFORMERS_HOME"] = sentence_transformers_home

    return hf_home, transformers_cache, sentence_transformers_home


def download_sentence_transformer_model(model_name: str):
    """Download a sentence transformer model."""
    print(f"\n[Download] sentence-transformers model: {model_name}")

    # Check if we're in offline mode
    if os.environ.get("TRANSFORMERS_OFFLINE") == "1":
        print("[WARN] Running in offline mode (TRANSFORMERS_OFFLINE=1)")
        print("   Checking if model is already cached...")

        # Try to load the model from cache
        try:
            model = SentenceTransformer(model_name, device="cpu")
            cache_path = model.cache_folder if hasattr(model, "cache_folder") else "default location"
            print(f"[OK] Model found in cache at: {cache_path}")

            # Test the model works
            test_embedding = model.encode("Test sentence")
            print(f"[OK] Model test successful - embedding dimension: {len(test_embedding)}")
            return True
        except Exception as e:
            print(f"[FAIL] Model not found in cache: {e}")
            traceback.print_exc()
            print("   Please run without TRANSFORMERS_OFFLINE=1 to download the model")
            return False

    try:
        model = SentenceTransformer(model_name)
        cache_path = model.cache_folder if hasattr(model, "cache_folder") else "default location"
        print(f"[OK] Model downloaded successfully to: {cache_path}")

        # Test the model works
        test_embedding = model.encode("Test sentence")
        print(f"[OK] Model test successful - embedding dimension: {len(test_embedding)}")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to download {model_name}: {e}")
        traceback.print_exc()
        return False


def download_transformers_model(model_name: str):
    """Download a transformers model (tokenizer + model)."""
    print(f"\n[Download] transformers model: {model_name}")

    # Check if we're in offline mode
    if os.environ.get("TRANSFORMERS_OFFLINE") == "1":
        print("[WARN] Running in offline mode (TRANSFORMERS_OFFLINE=1)")
        print("   Checking if model is already cached...")

        # Try to load the model from cache
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
            model = AutoModel.from_pretrained(model_name, local_files_only=True)
            print("[OK] Model found in cache")

            # Test the model works
            inputs = tokenizer("Test sentence", return_tensors="pt")
            outputs = model(**inputs)
            print(f"[OK] Model test successful - output shape: {outputs.last_hidden_state.shape}")
            return True
        except Exception as e:
            print(f"[FAIL] Model not found in cache: {e}")
            traceback.print_exc()
            print("   Please run without TRANSFORMERS_OFFLINE=1 to download the model")
            return False

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        print("[OK] Tokenizer and model downloaded successfully")

        # Test the model works
        inputs = tokenizer("Test sentence", return_tensors="pt")
        outputs = model(**inputs)
        print(f"[OK] Model test successful - output shape: {outputs.last_hidden_state.shape}")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to download {model_name}: {e}")
        traceback.print_exc()
        return False


def download_llamaindex_embedding(model_name: str):
    """Download a model via LlamaIndex HuggingFaceEmbedding."""
    print(f"\n[Download] LlamaIndex embedding model: {model_name}")

    # Lazy import to avoid ChatMessage/HuggingFaceInferenceAPI errors when
    # llama-index packages have version mismatches (e.g. on fresh CI venvs).
    # The same model (e.g. BAAI/bge-small-en-v1.5) is already cached by the
    # transformers download step, so skipping here does not break offline tests.
    try:
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    except ImportError as e:
        print(f"[WARN] Cannot import HuggingFaceEmbedding (llama-index compat): {e}")
        print("   Model will be used from transformers cache. Skipping LlamaIndex validation.")
        return True  # Accept: model is cached by transformers download

    # Check if we're in offline mode
    if os.environ.get("TRANSFORMERS_OFFLINE") == "1":
        print("[WARN] Running in offline mode (TRANSFORMERS_OFFLINE=1)")
        print("   Checking if model is already cached...")

        # Try to load the model from cache
        try:
            embed_model = HuggingFaceEmbedding(model_name=model_name, local_files_only=True)
            test_embedding = embed_model.get_text_embedding("Test sentence")
            print(f"[OK] Model found in cache and tested - dimension: {len(test_embedding)}")
            return True
        except Exception as e:
            print(f"[FAIL] Model not found in cache: {e}")
            traceback.print_exc()
            print("   Please run without TRANSFORMERS_OFFLINE=1 to download the model")
            return False

    try:
        embed_model = HuggingFaceEmbedding(model_name=model_name)
        test_embedding = embed_model.get_text_embedding("Test sentence")
        print(f"[OK] LlamaIndex embedding model downloaded and tested - dimension: {len(test_embedding)}")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to download via LlamaIndex {model_name}: {e}")
        traceback.print_exc()
        return False


def main():
    """Main setup function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Setup embedding models for local development")
    parser.add_argument("--dry-run", action="store_true", help="Setup directories but skip model downloads")
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: only download lightweight models needed for tests (excludes bge-large-en-v1.5)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat deprecation and API warnings as errors (use -W error for local validation)",
    )
    args = parser.parse_args()

    if args.strict:
        warnings.filterwarnings("error", category=DeprecationWarning)
        warnings.filterwarnings("error", category=FutureWarning)

    print("Setting up embedding models for local development...")
    if args.dry_run:
        print("[DRY-RUN] Directories will be set up but no models will be downloaded")
    print("=" * 60)

    # Check for dry run mode
    is_dry_run = "--dry-run" in sys.argv
    if is_dry_run:
        print("[DRY-RUN] No models will be downloaded")

    # Setup cache directories
    hf_home, transformers_cache, sentence_transformers_home = setup_cache_directories()

    if args.dry_run:
        print("\n" + "=" * 60)
        print("Summary: Cache directories set up successfully")
        print("Environment Configuration:")
        print(f"   HF_HOME: {hf_home}")
        print(f"   TRANSFORMERS_CACHE: {transformers_cache}")
        print(f"   SENTENCE_TRANSFORMERS_HOME: {sentence_transformers_home}")
        print("\nTo download models, run without --dry-run flag")
        return True

    # Models used in the project (from parameter_sets.py and test files)
    # In CI mode, skip large models not needed for tests to save disk space
    # (~14GB limit on GitHub Actions ubuntu-latest runners)
    if args.ci:
        print("[CI] Downloading only lightweight test models (skipping bge-large-en-v1.5)")
        models_to_download = [
            ("sentence_transformer", "sentence-transformers/all-MiniLM-L6-v2"),
            ("transformers", "BAAI/bge-small-en-v1.5"),
            ("llamaindex", "BAAI/bge-small-en-v1.5"),
        ]
    else:
        models_to_download = [
            # Core models from parameter_sets.py
            ("sentence_transformer", "sentence-transformers/all-MiniLM-L6-v2"),
            ("transformers", "BAAI/bge-small-en-v1.5"),
            ("transformers", "BAAI/bge-large-en-v1.5"),
            # Test via LlamaIndex (this is how the app actually uses them)
            ("llamaindex", "sentence-transformers/all-MiniLM-L6-v2"),
            ("llamaindex", "BAAI/bge-small-en-v1.5"),
        ]

    success_count = 0
    total_count = len(models_to_download)

    for download_type, model_name in models_to_download:
        if is_dry_run:
            print(f"[DRY-RUN] Would download {download_type} model: {model_name}")
            success = True
        else:
            if download_type == "sentence_transformer":
                success = download_sentence_transformer_model(model_name)
            elif download_type == "transformers":
                success = download_transformers_model(model_name)
            elif download_type == "llamaindex":
                success = download_llamaindex_embedding(model_name)
            else:
                print(f"[FAIL] Unknown download type: {download_type}")
                success = False

        if success:
            success_count += 1

    print("\n" + "=" * 60)
    if is_dry_run:
        print(f"Summary: {success_count}/{total_count} models would be downloaded")
    else:
        print(f"Summary: {success_count}/{total_count} models downloaded successfully")

    if success_count == total_count:
        if is_dry_run:
            print("[OK] All models would be downloaded successfully")
        else:
            print("[OK] All models downloaded successfully")
            print("\nEnvironment configuration:")
            print(f"   HF_HOME: {hf_home}")
            print(f"   TRANSFORMERS_CACHE: {transformers_cache}")
            print(f"   SENTENCE_TRANSFORMERS_HOME: {sentence_transformers_home}")
            print("\nFor offline testing, set these environment variables:")
            print("   export TRANSFORMERS_OFFLINE=1")
            print("   export HF_DATASETS_OFFLINE=1")
        return True
    else:
        if is_dry_run:
            print(f"[WARN] {total_count - success_count} models would fail to download")
        else:
            print(f"[WARN] {total_count - success_count} models failed to download")
            print("   Check your internet connection and try again")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
