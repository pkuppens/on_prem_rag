/**
 * Document preview registry - extendable configuration for file-type-specific previews.
 *
 * - PDF: native viewer (react-pdf)
 * - TXT: plain text from as-text endpoint
 * - MD: plain text now; extendable for formatted Markdown rendering (e.g. react-markdown)
 * - DOCX: extracted text from as-text endpoint; extendable for PDF conversion or dedicated renderer
 */

export type PreviewType = 'pdf' | 'text' | 'markdown' | 'docx-text';

export interface PreviewConfig {
  /** Viewer type - determines which component to use */
  type: PreviewType;
  /** Whether to fetch full file content via as-text endpoint (vs raw file URL) */
  fetchAsText: boolean;
  /** Optional: future markdown/HTML renderer, docx-to-PDF, etc. */
  note?: string;
}

const EXTENSION_CONFIG: Record<string, PreviewConfig> = {
  pdf: { type: 'pdf', fetchAsText: false },
  txt: { type: 'text', fetchAsText: true },
  md: {
    type: 'markdown',
    fetchAsText: true,
    note: 'Plain text for now; add react-markdown or similar for formatted preview later',
  },
  docx: {
    type: 'docx-text',
    fetchAsText: true,
    note: 'Extracted text; future: convert to PDF/markdown or dedicated Word renderer',
  },
  doc: { type: 'docx-text', fetchAsText: true },
};

/**
 * Get preview config for a filename. Returns undefined if preview is not supported.
 */
export function getPreviewConfig(filename: string): PreviewConfig | undefined {
  const ext = filename.split('.').pop()?.toLowerCase();
  return ext ? EXTENSION_CONFIG[ext] : undefined;
}

/**
 * Check if a file type has a supported preview.
 */
export function hasPreview(filename: string): boolean {
  return getPreviewConfig(filename) !== undefined;
}
