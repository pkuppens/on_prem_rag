# PDF URL and WebSocket Fixes

## Issues Resolved

### 1. PDF Previewer 404 Error

**Problem**: Frontend was getting 404 errors when trying to load PDF files with URLs like:

```
http://localhost:8000/files/learninglangchain.pdf
```

**Root Cause**: Frontend was using incorrect URL path. The backend endpoint is:

```
/api/documents/files/{filename}
```

But frontend was using:

```
/files/{filename}
```

**Solution**: Updated all frontend components to use the correct URL path:

#### Files Updated:

- `src/frontend/src/components/pdf/PDFViewer.tsx`
- `src/frontend/src/pages/PDFTestPage.tsx`
- `src/frontend/src/pages/DocxTestPage.tsx`

#### Changes Made:

```typescript
// Before
const pdfUrl = `http://localhost:8000/files/${selectedResult.document_name}`;

// After
const pdfUrl = apiUrls.file(selectedResult.document_name);
```

### 2. WebSocket 'undefined' Document Issue

**Problem**: When uploading documents, an 'undefined' document would appear in the upload progress.

**Root Cause**: Mismatch between backend and frontend WebSocket message field names:

- Backend sends: `file_id`
- Frontend expects: `filename`

**Solution**: Updated all frontend WebSocket handlers to use the correct field name:

#### Files Updated:

- `src/frontend/src/App.tsx`
- `src/frontend/src/pages/UploadPage.tsx`
- `src/frontend/src/pages/PDFTestPage.tsx`

#### Changes Made:

```typescript
// Before
setUploadProgress((prev) => ({
  ...prev,
  [data.filename]: {
    progress: data.progress,
    error: data.error,
    isComplete: data.isComplete,
  },
}));

// After
setUploadProgress((prev) => ({
  ...prev,
  [data.file_id]: {
    progress: data.progress,
    error: data.error,
    isComplete: data.isComplete,
  },
}));
```

## New Configuration System

As part of this fix, we also implemented a **robust configuration system** to eliminate hardcoded URLs and make the application production-ready. See [FRONTEND_API_CONFIGURATION.md](FRONTEND_API_CONFIGURATION.md) for complete details.

### Key Benefits:

- **Environment-aware**: Automatically switches between development and production settings
- **Configurable**: All URLs can be changed via environment variables
- **Centralized**: All API endpoints defined in one place
- **Type-safe**: TypeScript interfaces ensure correct configuration

### Environment Variables:

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_WEBSOCKET_URL=ws://localhost:8000
VITE_API_TIMEOUT=30000
VITE_API_DEBUG=true
```

## Testing

### Backend File Serving Test

```bash
curl -v http://localhost:8000/api/documents/files/learninglangchain.pdf
```

Expected: HTTP 200 OK with PDF content

### Frontend Test

Created `src/frontend/tests/pdf-url.spec.ts` to verify:

1. Correct URL construction
2. PDF file accessibility
3. Upload functionality

## Debug Logging

The backend has debug logging enabled in `src/backend/rag_pipeline/api/documents.py`:

```python
logger = StructuredLogger(__name__, level="DEBUG")
```

Debug logs should show:

- File request details
- Path resolution
- File existence checks
- Serving success/failure

If debug logs aren't appearing, check:

1. Backend server is running with debug mode
2. Log level is set to DEBUG
3. Console output is not being filtered

## Verification Steps

1. **Upload a PDF file** through the frontend
2. **Search for content** in the uploaded document
3. **Click on search results** to view the PDF
4. **Verify PDF loads** without 404 errors
5. **Check upload progress** shows correct filename (not 'undefined')

## Related Files

- `src/backend/rag_pipeline/api/documents.py` - File serving endpoint
- `src/backend/rag_pipeline/utils/progress.py` - WebSocket progress notifications
- `src/frontend/src/components/pdf/PDFViewer.tsx` - PDF viewer component
- `src/frontend/src/components/upload/UploadProgress.tsx` - Upload progress display
- `src/frontend/src/config/api.ts` - **NEW**: Centralized API configuration
- `src/frontend/env.example` - **NEW**: Environment configuration template
