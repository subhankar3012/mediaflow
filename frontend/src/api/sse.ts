import type { SSEEventData, JobStatus } from './types';
import { getOrCreateSessionId, DEFAULT_API_BASE_URL } from './client';

export interface SSEOptions {
  jobId: string;
  onEvent: (data: SSEEventData) => void;
  onError?: (err: any) => void;
  onComplete?: (downloadUrl: string) => void;
  onTerminal?: (status: JobStatus, data: SSEEventData) => void;
}

export class JobEventSubscriber {
  private options: SSEOptions;
  private eventSource: EventSource | null = null;
  private closed = false;
  private retryCount = 0;
  private maxRetries = 3;

  constructor(options: SSEOptions) {
    this.options = options;
  }

  public connect(): void {
    if (this.closed) return;

    const apiBase = DEFAULT_API_BASE_URL;

    const sessionId = getOrCreateSessionId();
    const query = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
    const url = `${apiBase}/api/jobs/${encodeURIComponent(this.options.jobId)}/events${query}`;
    this.eventSource = new EventSource(url, { withCredentials: true });

    this.eventSource.onmessage = (event) => {
      try {
        const data: SSEEventData = JSON.parse(event.data);
        this.options.onEvent(data);

        // Terminal states check
        const terminalStates: JobStatus[] = ['COMPLETED', 'FAILED', 'CANCELLED', 'EXPIRED'];
        if (terminalStates.includes(data.status)) {
          this.close();

          if (data.status === 'COMPLETED') {
            const rawUrl = data.download_url || `/api/jobs/${this.options.jobId}/file`;
            const fullUrl = rawUrl.startsWith('http') ? rawUrl : `${apiBase}${rawUrl}`;
            const delimiter = fullUrl.includes('?') ? '&' : '?';
            const fileUrl = sessionId && !fullUrl.includes('session_id=')
              ? `${fullUrl}${delimiter}session_id=${encodeURIComponent(sessionId)}`
              : fullUrl;
            this.options.onComplete?.(fileUrl);
          }
          this.options.onTerminal?.(data.status, data);
        }
      } catch (err) {
        console.error('Failed to parse SSE message:', err);
      }
    };

    this.eventSource.onerror = (err) => {
      if (this.closed) return;
      this.retryCount++;

      if (this.retryCount > this.maxRetries) {
        this.close();
        this.options.onError?.(err);
      }
    };
  }

  public close(): void {
    this.closed = true;
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}

export function subscribeToJobEvents(options: SSEOptions): () => void {
  const subscriber = new JobEventSubscriber(options);
  subscriber.connect();
  return () => subscriber.close();
}
