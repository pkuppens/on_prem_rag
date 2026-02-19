import { useEffect, useState } from 'react';
import { apiUrls } from '../config/api';

/**
 * Fetch document content as plain text from the as-text endpoint.
 * Used by TextViewer (txt, md) and DOCXViewer (docx).
 */
export function useDocumentTextContent(
  documentName: string | null,
  enabled: boolean
): { content: string | null; loading: boolean; error: string | null } {
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!documentName || !enabled) {
      setContent(null);
      setLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    fetch(apiUrls.fileAsText(documentName))
      .then((res) => {
        if (cancelled) return;
        if (!res.ok) throw new Error(`Failed to load: ${res.status} ${res.statusText}`);
        return res.text();
      })
      .then((text) => {
        if (!cancelled) setContent(text ?? '');
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [documentName, enabled]);

  return { content, loading, error };
}
