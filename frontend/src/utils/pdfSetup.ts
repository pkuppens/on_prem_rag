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
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.js',
  import.meta.url
).toString();

export { pdfjs };
