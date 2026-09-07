import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props { children: ReactNode; title?: string }
interface State { error: Error | null }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };
  static getDerivedStateFromError(error: Error): State {
    return { error };
  }
  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("recordShelf UI error", error, info.componentStack);
  }
  render() {
    if (this.state.error) {
      return (
        <div className="error-box">
          <strong>{this.props.title ?? "Something went wrong"}</strong>
          <code>{this.state.error.message}</code>
          <button className="btn sm" style={{ marginTop: 8 }} onClick={() => this.setState({ error: null })}>
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export function QueryError({ error, what }: { error: unknown; what?: string }) {
  const msg = error instanceof Error ? error.message : String(error);
  return (
    <div className="error-box">
      <strong>Could not load {what ?? "data"}</strong>
      <code>{msg}</code>
    </div>
  );
}
