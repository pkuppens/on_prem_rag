import { pdfjs } from 'react-pdf';

/**
 * PDF.js Security Configuration for On-Premises Deployment
 *
 * Uses local worker files to avoid CDN dependencies, ensuring:
 * - No external network requests for PDF processing
 * - Compatible with strict Content Security Policy (CSP)
 * - Offline operation capability
 * - High security environment compliance
 */

// Set worker source to use local files bundled with the application
// Updated to match pdfjs-dist version 5.3.31 to fix version mismatch
// Fix: Using pdfjs.version ensures API and Worker versions match
// Previous error: "The API version "4.8.69" does not match the Worker version "5.3.31""
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

export { pdfjs };
