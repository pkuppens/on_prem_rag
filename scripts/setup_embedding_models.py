#!/usr/bin/env python3
"""Setup script to pre-download embedding models for local development.

This script ensures that all embedding models used by the application
are downloaded and cached locally, enabling offline operation.

Usage:
    python scripts/setup_embedding_models.py

Environment Variables:
    HF_HOME: HuggingFace cache directory (default: data/cache/huggingface)
    SENTENCE_TRANSFORMERS_HOME: Sentence transformers cache directory
"""

import os
import sys
from pathlib import Path

try:
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from sentence_transformers import SentenceTransformer
    from transformers import AutoModel, AutoTokenizer
except ImportError as e:
    print(f"Error: Required packages not installed: {e}")
    print("Please install dependencies with: uv pip install -e .[dev]")
    sys.exit(1)

from backend.rag_pipeline.utils.directory_utils import ensure_directory_exists, get_cache_dir


def setup_cache_directories():
    """Set up cache directories for HuggingFace models."""
    # Set default cache locations in our data directory
    cache_dir = get_cache_dir()
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
    print(f"\n📥 Downloading sentence-transformers model: {model_name}")
    try:
        model = SentenceTransformer(model_name)
        cache_path = model.cache_folder if hasattr(model, "cache_folder") else "default location"
        print(f"✅ Model downloaded successfully to: {cache_path}")

        # Test the model works
        test_embedding = model.encode("Test sentence")
        print(f"✅ Model test successful - embedding dimension: {len(test_embedding)}")
        return True
    except Exception as e:
        print(f"❌ Failed to download {model_name}: {e}")
        return False


def download_transformers_model(model_name: str):
    """Download a transformers model (tokenizer + model)."""
    print(f"\n📥 Downloading transformers model: {model_name}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        print(f"✅ Tokenizer and model downloaded successfully")

        # Test the model works
        inputs = tokenizer("Test sentence", return_tensors="pt")
        outputs = model(**inputs)
        print(f"✅ Model test successful - output shape: {outputs.last_hidden_state.shape}")
        return True
    except Exception as e:
        print(f"❌ Failed to download {model_name}: {e}")
        return False


def download_llamaindex_embedding(model_name: str):
    """Download a model via LlamaIndex HuggingFaceEmbedding."""
    print(f"\n📥 Downloading LlamaIndex embedding model: {model_name}")
    try:
        embed_model = HuggingFaceEmbedding(model_name=model_name)
        test_embedding = embed_model.get_text_embedding("Test sentence")
        print(f"✅ LlamaIndex embedding model downloaded and tested - dimension: {len(test_embedding)}")
        return True
    except Exception as e:
        print(f"❌ Failed to download via LlamaIndex {model_name}: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 Setting up embedding models for local development...")
    print("=" * 60)

    # Setup cache directories
    hf_home, transformers_cache, sentence_transformers_home = setup_cache_directories()

    # Models used in the project (from parameter_sets.py and test files)
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
        if download_type == "sentence_transformer":
            success = download_sentence_transformer_model(model_name)
        elif download_type == "transformers":
            success = download_transformers_model(model_name)
        elif download_type == "llamaindex":
            success = download_llamaindex_embedding(model_name)
        else:
            print(f"❌ Unknown download type: {download_type}")
            success = False

        if success:
            success_count += 1

    print("\n" + "=" * 60)
    print(f"📊 Download Summary: {success_count}/{total_count} models downloaded successfully")

    if success_count == total_count:
        print("🎉 All models downloaded successfully!")
        print("\n📝 Environment Configuration:")
        print(f"   HF_HOME: {hf_home}")
        print(f"   TRANSFORMERS_CACHE: {transformers_cache}")
        print(f"   SENTENCE_TRANSFORMERS_HOME: {sentence_transformers_home}")
        print("\n💡 For offline testing, set these environment variables:")
        print("   export TRANSFORMERS_OFFLINE=1")
        print("   export HF_DATASETS_OFFLINE=1")
        return True
    else:
        print(f"⚠️  {total_count - success_count} models failed to download")
        print("   Check your internet connection and try again")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
