/**
 * Error Boundary to surface React render errors instead of a blank page.
 * Helps diagnose issues when the app fails to mount or a child throws.
 */
import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  render(): ReactNode {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div
          style={{
            padding: 24,
            maxWidth: 640,
            margin: '40px auto',
            fontFamily: 'system-ui, sans-serif',
            background: '#1a1a1a',
            color: '#fff',
            borderRadius: 8,
          }}
        >
          <h2 style={{ color: '#f87171', marginTop: 0 }}>Application Error</h2>
          <p>Something went wrong. Check the browser console (F12) for details.</p>
          <pre
            style={{
              overflow: 'auto',
              padding: 12,
              background: '#0f0f0f',
              borderRadius: 4,
              fontSize: 12,
            }}
          >
            {this.state.error.message}
          </pre>
        </div>
      );
    }
    return this.props.children;
  }
}
