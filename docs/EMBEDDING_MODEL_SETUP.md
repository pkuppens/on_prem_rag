# Embedding Model Setup Guide

This guide explains how to set up embedding models for offline operation in GitHub Actions and local development environments, including Codex.

## Problem Background

The RAG pipeline uses HuggingFace embedding models (like `sentence-transformers/all-MiniLM-L6-v2`) that need to be downloaded from the internet. However:

1. **GitHub Actions**: Tests run in offline mode (`TRANSFORMERS_OFFLINE=1`) but the models need to be pre-cached
2. **Local Development**: Developers may work in environments with limited internet access
3. **Codex Integration**: AI coding assistants need access to cached models in the workspace
4. **Local Deployment**: System could be deployed in secured environments with little or on internet access.

## Solution Overview

We've implemented a two-part solution:

1. **GitHub Actions**: Automatic model caching with proper cache configuration
2. **Local Development**: Setup script for pre-downloading models

## GitHub Actions Setup

The CI workflow now includes:

### Model Caching

```yaml
- name: Cache HuggingFace models
  uses: actions/cache@v3
  with:
    path: ~/.cache/huggingface
    key: ${{ runner.os }}-huggingface-${{ hashFiles('**/pyproject.toml') }}
    restore-keys: |
      ${{ runner.os }}-huggingface-
```

### Model Pre-download

```yaml
- name: Pre-download embedding models
  run: |
    source .venv/bin/activate
    export HF_HOME=$HOME/.cache/huggingface
    export TRANSFORMERS_CACHE=$HOME/.cache/huggingface/hub
    export SENTENCE_TRANSFORMERS_HOME=$HOME/.cache/huggingface/sentence_transformers
    # Download all required models...
```

### Offline Testing

```yaml
- name: Test with pytest
  run: |
    source .venv/bin/activate
    export HF_HOME=$HOME/.cache/huggingface
    export TRANSFORMERS_CACHE=$HOME/.cache/huggingface/hub
    export SENTENCE_TRANSFORMERS_HOME=$HOME/.cache/huggingface/sentence_transformers
    TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 pytest
```

## Local Development Setup

### Quick Setup

Run the setup script to download all required models:

```bash
# Install dependencies first
uv pip install -e .[dev]

# Download models
python scripts/setup_embedding_models.py
```

### Manual Setup

If you prefer manual setup:

```bash
# Set cache environment variables
export HF_HOME=~/.cache/huggingface
export TRANSFORMERS_CACHE=~/.cache/huggingface/hub
export SENTENCE_TRANSFORMERS_HOME=~/.cache/huggingface/sentence_transformers

# Download models in Python
python -c "
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel

# Download required models
SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
AutoTokenizer.from_pretrained('BAAI/bge-small-en-v1.5')
AutoModel.from_pretrained('BAAI/bge-small-en-v1.5')
"
```

### Offline Testing

Once models are cached, you can run tests offline:

```bash
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
pytest
```

## Codex Integration

For AI coding assistants like OpenAI Codex:

### Workspace Setup

1. **Include the setup script in your workspace**:

   ```
   scripts/setup_embedding_models.py
   ```

2. **Run the setup script during workspace initialization**:
   ```bash
   python scripts/setup_embedding_models.py
   ```

### Environment Configuration

Ensure these environment variables are set in your Codex environment:

```bash
export HF_HOME=~/.cache/huggingface
export TRANSFORMERS_CACHE=~/.cache/huggingface/hub
export SENTENCE_TRANSFORMERS_HOME=~/.cache/huggingface/sentence_transformers
```

## Models Used

The following models are pre-cached:

| Model                                    | Purpose                 | Size   | Used In            |
| ---------------------------------------- | ----------------------- | ------ | ------------------ |
| `sentence-transformers/all-MiniLM-L6-v2` | Fast embeddings         | ~90MB  | Tests, Fast config |
| `BAAI/bge-small-en-v1.5`                 | General embeddings      | ~130MB | Default config     |
| `BAAI/bge-large-en-v1.5`                 | High-quality embeddings | ~1.3GB | Precise config     |

## Troubleshooting

### Common Issues

1. **"OSError: We couldn't connect to 'https://huggingface.co'"**

   - **Solution**: Run the setup script first to cache models
   - **Cause**: Models not cached or wrong cache directory

2. **"No sentence-transformers model found"**

   - **Solution**: Check cache environment variables are set correctly
   - **Cause**: sentence-transformers can't find cached models

3. **Cache directory permissions**
   - **Solution**: Ensure cache directory is writable
   - **Cause**: Permission issues in `~/.cache/huggingface`

### Verification

Verify your setup works:

```python
import os
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print("✅ Offline model loading works!")
```

### Cache Locations

Default cache locations:

- **Linux/macOS**: `~/.cache/huggingface/`
- **Windows**: `%USERPROFILE%\.cache\huggingface\`

Cache structure:

```
~/.cache/huggingface/
├── hub/                          # transformers models
├── sentence_transformers/        # sentence-transformers models
└── datasets/                     # HuggingFace datasets
```

## Best Practices

1. **Pre-download models** before working offline
2. **Set environment variables** consistently across environments
3. **Use the setup script** for new environments
4. **Cache models in CI** to speed up builds
5. **Version control exclude** cache directories (already in `.gitignore`)

## Integration with Other Tools

This setup is compatible with:

- ✅ GitHub Actions
- ✅ Local development
- ✅ Docker containers (mount cache volume)
- ✅ AI coding assistants (Codex, Copilot)
- ✅ Jupyter notebooks
- ✅ VS Code with Python extension
