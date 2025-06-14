# Frontend Manual Test Pages

This guide describes how to manually verify frontend components.

## Setup

1. Install dependencies and start the dev server:

```bash
cd src/frontend
npm install
npm run dev
```

2. Access the test pages at `http://localhost:5173`.

## Test Pages

- `/pdf-test` – Loads `PDFTestPage` with a sample PDF from `tests/test_data`.
- `/docx-test` – Displays `DOCXViewer` with a sample DOCX file.
- `/text-test` – Shows `TextViewer` using a Markdown file.

Each page demonstrates the viewer component in isolation and includes a copy
button for selected text.

## Expected Behaviour

1. The viewer loads the sample file without errors.
2. Text can be selected and copied to the clipboard.
3. Navigation buttons work for the PDF viewer.

These pages aid in verifying component rendering during development.


## Code Files

- [src/frontend/src/pages/PDFTestPage.tsx](../../src/frontend/src/pages/PDFTestPage.tsx) - Standalone PDF viewer
- [src/frontend/src/pages/DocxTestPage.tsx](../../src/frontend/src/pages/DocxTestPage.tsx) - DOCX viewer page
- [src/frontend/src/pages/TextTestPage.tsx](../../src/frontend/src/pages/TextTestPage.tsx) - Text viewer page
