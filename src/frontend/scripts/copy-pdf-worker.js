#!/usr/bin/env node

/**
 * Cross-platform script to copy PDF.js worker file
 *
 * This script copies the PDF.js worker file from node_modules to the public directory
 * during the build process, ensuring the application can work offline.
 */

import { copyFile, mkdir } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const sourcePath = join(__dirname, '..', 'node_modules', 'react-pdf', 'node_modules', 'pdfjs-dist', 'build', 'pdf.worker.min.mjs');
const destPath = join(__dirname, '..', 'public', 'pdf.worker.min.mjs');

async function copyPdfWorker() {
  try {
    // Ensure the public directory exists
    await mkdir(dirname(destPath), { recursive: true });

    // Copy the worker file
    await copyFile(sourcePath, destPath);

    console.log('✅ PDF worker file copied successfully');
    console.log(`   From: ${sourcePath}`);
    console.log(`   To: ${destPath}`);
  } catch (error) {
    console.error('❌ Failed to copy PDF worker file:', error.message);

    if (error.code === 'ENOENT') {
      console.error('   The source file was not found. Please ensure react-pdf is installed.');
      console.error('   Try running: npm install');
    }

    process.exit(1);
  }
}

copyPdfWorker();
