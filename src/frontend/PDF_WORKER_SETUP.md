# PDF Worker Setup

This document explains the PDF.js worker file setup for offline operation.

## Overview

The application uses `react-pdf` for PDF viewing, which requires the PDF.js worker file to be available locally for offline operation. The worker file is automatically copied during the build process.

## How It Works

1. **Automatic Copy**: The `copy-pdf-worker.js` script copies the worker file from `node_modules` to the `public` directory
2. **Build Integration**: The copy process is integrated into both `dev` and `build` scripts
3. **Offline Operation**: The worker file is served from the local public directory, eliminating CDN dependencies

## Scripts

- `npm run copy-pdf-worker`: Manually copy the PDF worker file
- `npm run dev`: Start development server (includes worker copy)
- `npm run build`: Build for production (includes worker copy)

## File Locations

- **Source**: `node_modules/react-pdf/node_modules/pdfjs-dist/build/pdf.worker.min.mjs`
- **Destination**: `public/pdf.worker.min.mjs`
- **Configuration**: `src/utils/pdfSetup.ts` (sets worker source to `/pdf.worker.min.mjs`)

## Troubleshooting

### Worker File Not Found

If you see "Failed to fetch dynamically imported module" errors:

1. Ensure `react-pdf` is installed: `npm install`
2. Run the copy script: `npm run copy-pdf-worker`
3. Restart the development server: `npm run dev`

### Cross-Platform Compatibility

The copy script works on Windows, macOS, and Linux using Node.js file system APIs.

## Security Benefits

- **No CDN Dependencies**: Eliminates external network requests for PDF processing
- **CSP Compliance**: Works with strict Content Security Policies
- **Offline Operation**: PDF viewing works without internet connectivity
- **Version Control**: Worker file version is locked to the installed `react-pdf` version
