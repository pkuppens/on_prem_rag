"""Directory preconditions of LocalRAGSystem (the callers of the shared directory helpers).

The heavy constructor (embeddings, vector store) is bypassed with ``__new__``; only the
directory checks that run before any model or index work are exercised.
"""

import pytest

from backend.rag_pipeline.core.rag_system import DirectoryEmptyError, LocalRAGSystem


@pytest.fixture
def system(tmp_path) -> LocalRAGSystem:
    """A LocalRAGSystem without initialisation, pointing at directories under tmp_path."""
    rag = LocalRAGSystem.__new__(LocalRAGSystem)
    rag.input_data_dir = tmp_path / "data"
    rag.index_storage_dir = tmp_path / "storage"
    return rag


def test_load_mixed_documents_missing_input_directory_raises_file_not_found(system):
    """As a user I want a clear error when the input data directory does not exist."""
    with pytest.raises(FileNotFoundError, match="Input data directory not found"):
        system.load_mixed_documents()


def test_load_mixed_documents_empty_input_directory_raises_directory_empty(system, tmp_path):
    """As a user I want to be told to add documents when the input directory is empty."""
    (tmp_path / "data").mkdir()

    with pytest.raises(DirectoryEmptyError, match="Please add your documents"):
        system.load_mixed_documents()


def test_load_mixed_documents_input_path_that_is_a_file_raises_not_a_directory(system, tmp_path):
    """A file given as input directory is rejected explicitly."""
    (tmp_path / "data").write_text("not a directory")

    with pytest.raises(NotADirectoryError):
        system.load_mixed_documents()


def test_load_index_missing_index_directory_raises_file_not_found(system):
    """As a user I want a clear error when there is no saved index to load."""
    with pytest.raises(FileNotFoundError, match="Index directory not found"):
        system.load_index()
