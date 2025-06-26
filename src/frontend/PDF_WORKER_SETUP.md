# PDF Worker Setup

## Overview

This project uses a local PDF.js worker file instead of loading it from a CDN to ensure:

- **Offline operation**: No external network dependencies
- **Security**: No external requests for PDF processing
- **Reliability**: No CDN connectivity issues
- **CSP compliance**: Works with strict Content Security Policies
- **Version compatibility**: Uses the exact worker version that react-pdf expects

## Setup

### Automatic Setup (Recommended)

The PDF worker file is automatically copied during the build process:

```bash
npm run build:with-worker
```

This command:

1. Copies the worker file from `node_modules/react-pdf/node_modules/pdfjs-dist/build/pdf.worker.min.mjs` to `public/pdf.worker.min.mjs`
2. Builds the application

### Manual Setup

If you need to copy the worker file manually:

```bash
npm run copy-pdf-worker
```

Or manually copy the file:

```bash
copy node_modules\react-pdf\node_modules\pdfjs-dist\build\pdf.worker.min.mjs public\pdf.worker.min.mjs
```

## Configuration

The PDF worker is configured in `src/utils/pdfSetup.ts`:

```typescript
import { pdfjs } from "react-pdf";

// Set worker source to use local file
pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.mjs";

export { pdfjs };
```

## Usage

Import the configured PDF.js instance in your components:

```typescript
import { pdfjs } from "../utils/pdfSetup";
import { Document, Page } from "react-pdf";

// Use Document and Page components normally
<Document file={pdfUrl}>
  <Page pageNumber={1} />
</Document>;
```

## Troubleshooting

### Worker Not Found Error

If you see "Failed to fetch dynamically imported module" errors:

1. **Check if worker file exists**: Verify `public/pdf.worker.min.mjs` exists
2. **Copy worker file**: Run `npm run copy-pdf-worker`
3. **Restart dev server**: Restart the development server after copying

### Version Mismatch Error

If you see "API version does not match Worker version" errors:

1. **Check versions**: Ensure the worker file matches react-pdf's expected version
2. **Copy correct worker**: Run `npm run copy-pdf-worker` to get the right version
3. **Restart dev server**: Restart the development server after copying

### Build Issues

If the build fails:

1. **Check file paths**: Ensure the worker file exists in `node_modules/react-pdf/node_modules/pdfjs-dist/build/`
2. **Run copy command**: Execute `npm run copy-pdf-worker` before building
3. **Check permissions**: Ensure write permissions to the `public/` directory

## File Locations

- **Source worker**: `node_modules/react-pdf/node_modules/pdfjs-dist/build/pdf.worker.min.mjs`
- **Public worker**: `public/pdf.worker.min.mjs`
- **Configuration**: `src/utils/pdfSetup.ts`

## Dependencies

- `react-pdf@9.2.1`: React PDF viewer component (includes pdfjs-dist@4.8.69)

## Version Compatibility

This setup ensures that:

- The worker file version matches exactly what `react-pdf` expects
- No version conflicts between different pdfjs-dist installations
- Consistent behavior across all PDF viewing components

## Security Benefits

1. **No external requests**: All PDF processing happens locally
2. **CSP compliance**: No need for `unsafe-eval` or external script sources
3. **Offline capability**: PDF viewing works without internet connection
4. **Version control**: Worker version is locked to react-pdf's expected version
