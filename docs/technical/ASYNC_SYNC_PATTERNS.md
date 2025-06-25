# Async/Sync Patterns in the RAG Pipeline

This document explains the clean patterns used for handling async and sync functions in the RAG pipeline, particularly focusing on progress callbacks and document processing.

## Key Principles

### 1. Keep Core Processing Sync

- **Document processing is CPU-intensive** and should be synchronous
- **Progress callbacks should be sync** - they're just function calls
- **Async is only needed for I/O operations** (WebSocket communication, file I/O)

### 2. Clean Separation of Concerns

- **Sync functions**: Core business logic, data processing, embeddings
- **Async functions**: API endpoints, WebSocket communication, file uploads
- **Thread pool**: Run sync functions from async contexts

## Progress Callback Pattern

### The Problem

You had mixed async/sync patterns that were confusing and error-prone:

- Some functions were async when they didn't need to be
- Progress callbacks were sometimes async, sometimes sync
- `asyncio.iscoroutinefunction()` checks everywhere

### The Solution

**Keep progress callbacks synchronous** and handle async communication at the API layer:

```python
# ✅ Clean: Sync progress callback
def progress_callback(progress: float) -> None:
    """Map processing progress (0.0-1.0) to upload progress (10-95%)."""
    upload_progress = 10 + int(progress * 85)
    # Schedule async notification to run in event loop
    asyncio.create_task(
        progress_notifier.notify(
            ProgressEvent(filename, upload_progress, f"Processing ({int(progress * 100)}%)")
        )
    )

# ✅ Clean: Sync processing function
def process_document(
    file_path: Path,
    model_name: str,
    *,
    progress_callback: Callable[[float], None] | None = None,
) -> tuple[int, int]:
    """Process document with optional progress updates."""
    if progress_callback:
        progress_callback(0.0)  # Start

    # ... processing logic ...

    if progress_callback:
        progress_callback(1.0)  # Complete

    return chunks_processed, records_stored

# ✅ Clean: Async API that uses thread pool
async def upload_document(file: UploadFile):
    """API endpoint that handles async/sync boundary."""
    # Run sync processing in thread pool
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        process_document,
        file_path,
        model_name,
        progress_callback=progress_callback,
    )
```

## Why This Pattern Works

### 1. **Progress Callbacks Don't Need Async**

- Progress updates are just function calls
- No I/O operations in the callback itself
- The async WebSocket communication happens separately

### 2. **CPU-Intensive Work Should Be Sync**

- Document processing, chunking, embedding generation are CPU-bound
- Async doesn't help with CPU-bound work
- Thread pools handle the async/sync boundary

### 3. **Cleaner Error Handling**

- Sync functions have simpler error handling
- No need to handle both sync and async exceptions
- Easier to test and debug

## Implementation Details

### Thread Pool Usage

```python
# Run sync function from async context
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(
    None,  # Use default executor
    sync_function,
    arg1,
    arg2,
    kwarg1=value1,
)
```

### Progress Callback Design

```python
# Simple sync callback signature
Callable[[float], None]  # Takes progress (0.0-1.0), returns nothing

# No complex async/sync detection needed
if progress_callback:
    progress_callback(0.5)  # Just call it
```

### WebSocket Integration

```python
# Progress callback schedules async WebSocket notification
def progress_callback(progress: float) -> None:
    asyncio.create_task(
        progress_notifier.notify(ProgressEvent(file_id, progress, message))
    )
```

### Progress Notifier

The `progress_notifier` module implements a lightweight observer pattern.
Processing functions emit :class:`ProgressEvent` objects while WebSocket clients
subscribed to ``/ws/upload-progress`` receive them as JSON messages. This keeps
the processing code independent from the WebSocket layer and allows multiple
clients to watch the same upload.

## Benefits

1. **Simpler Code**: No more `asyncio.iscoroutinefunction()` checks
2. **Better Performance**: CPU work runs in thread pool, not blocking event loop
3. **Easier Testing**: Sync functions are easier to test
4. **Clear Boundaries**: Async only where needed (I/O operations)
5. **Maintainable**: Consistent patterns throughout the codebase

## Migration Guide

If you have existing mixed async/sync code:

1. **Identify CPU-bound functions** - these should be sync
2. **Make progress callbacks sync** - they're just function calls
3. **Use thread pools** for async/sync boundaries
4. **Remove `asyncio.iscoroutinefunction()` checks** - not needed
5. **Test thoroughly** - ensure progress updates still work

## Example Migration

### Before (Mixed Async/Sync)

```python
async def process_document(...):
    if progress_call_back:
        if asyncio.iscoroutinefunction(progress_call_back):
            await progress_call_back(0.0)
        else:
            progress_call_back(0.0)
```

### After (Clean Sync)

```python
def process_document(...):
    if progress_callback:
        progress_callback(0.0)  # Simple sync call
```

This pattern makes the code much cleaner and easier to understand while maintaining all the functionality.
