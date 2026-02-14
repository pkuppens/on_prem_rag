# Manual Upload Testing for Document Ingestion

**Created:** 2025-02-14  
**Context:** PR #102 – Extend document ingestion pipeline (#78)

This guide describes how to manually verify HTML and PDF uploads, text extraction, and deduplication.

## Prerequisites

1. **Start the backend**: `uv run start-backend` (runs on http://localhost:8000)
2. **Optional**: Ollama running for `/api/ask` queries (not required for upload tests)

## Test 1: HTML Upload and Text Extraction

### Step 1: Create a test HTML file

```html
<!DOCTYPE html>
<html>
<head><title>Manual Upload Test</title></head>
<body>
  <section id="s1">
    <h1>Document Title</h1>
    <p>This is sample content for manual upload testing.</p>
    <h2>Section Two</h2>
    <p>Second paragraph with more text.</p>
  </section>
</body>
</html>
```

Save as `tests/test_data/manual_test.html` or any `.html` file.

### Step 2: Upload via API

**PowerShell** (use Python; PowerShell's `curl` alias has different syntax):

```powershell
cd c:\Users\piete\Repos\pkuppens\on_prem_rag
uv run python -c "
import httpx
with open('tests/test_data/manual_test.html', 'rb') as f:
    files = {'file': ('manual_test.html', f, 'text/html')}
    data = {'params_name': 'default'}
    r = httpx.post('http://localhost:8000/api/documents/upload', files=files, data=data, timeout=120)
    print('Status:', r.status_code, r.json())
"
```

**Bash/curl** (Linux/macOS/Git Bash):

```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@tests/test_data/manual_test.html" \
  -F "params_name=default"
```

**Expected**: `200 OK` with `"status": "uploaded"`, `"processing": "started"`.

### Step 3: Verify file is listed

```powershell
uv run python -c "import httpx; print(httpx.get('http://localhost:8000/api/documents/list').json())"
```

**Expected**: `{"files": ["manual_test.html"]}` (or includes the file).

### Step 4: Re-upload same file (dedup robustness)

Upload the same HTML file again. Background processing runs; deduplication skips re-storing identical chunks in the vector store. Response should still be `200 OK`.

---

## Test 2: PDF Upload

### Step 1: Obtain a test PDF

- Use existing `tests/test_data/2005.11401v4.pdf` if present (gitignored except `2*.pdf`), or
- Download: `https://arxiv.org/pdf/2005.11401v4.pdf`

```powershell
uv run python -c "
import httpx
from pathlib import Path
url = 'https://arxiv.org/pdf/2005.11401v4.pdf'
p = Path('tests/test_data/2005.11401v4.pdf')
p.parent.mkdir(parents=True, exist_ok=True)
with httpx.Client(follow_redirects=True, timeout=60) as c:
    r = c.get(url)
    r.raise_for_status()
    p.write_bytes(r.content)
print('Downloaded:', p.stat().st_size, 'bytes')
"
```

### Step 2: Upload PDF

```powershell
uv run python -c "
import httpx
with open('tests/test_data/2005.11401v4.pdf', 'rb') as f:
    files = {'file': ('2005.11401v4.pdf', f, 'application/pdf')}
    data = {'params_name': 'default'}
    r = httpx.post('http://localhost:8000/api/documents/upload', files=files, data=data, timeout=180)
    print('Status:', r.status_code, r.json())
"
```

**Expected**: `200 OK` with `"status": "uploaded"`, `"processing": "started"`.

### Step 3: Wait and verify

Processing can take 30–60 seconds for a multi-page PDF. Then:

```powershell
uv run python -c "import httpx; print(httpx.get('http://localhost:8000/api/documents/list').json())"
```

**Expected**: List includes `2005.11401v4.pdf`.

### Step 4: Re-upload PDF (dedup)

Upload the same PDF again. Processing runs; dedup prevents duplicate chunks. Response: `200 OK`.

---

## Supported Formats (API)

| Extension | MIME Type |
|-----------|-----------|
| .pdf | application/pdf |
| .html, .htm | text/html |
| .txt | text/plain |
| .md | text/markdown |
| .docx | application/vnd.openxmlformats-officedocument.wordprocessingml.document |
| .doc | application/msword |
| .csv | text/csv |
| .json | application/json |

---

## Optional: Verify via Ask Endpoint

Requires Ollama running locally:

```powershell
uv run python -c "
import httpx
r = httpx.post('http://localhost:8000/api/ask', json={'question': 'What is the main topic?'}, timeout=60)
print('Status:', r.status_code)
if r.status_code == 200:
    print('Answer:', r.json().get('answer', '')[:400])
"
```

---

## Quick Checklist

- [ ] HTML upload returns 200
- [ ] HTML file appears in `/api/documents/list`
- [ ] Same HTML can be uploaded again (no errors)
- [ ] PDF upload returns 200
- [ ] PDF file appears in list after processing
- [ ] Same PDF can be uploaded again (no errors)
