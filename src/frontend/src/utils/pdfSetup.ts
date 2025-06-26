import { pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/TextLayer.css';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';

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
// Using local worker file to avoid CDN connectivity issues
// The worker file is copied to the public directory during build
pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

export { pdfjs };
