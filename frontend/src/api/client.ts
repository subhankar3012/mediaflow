import type {
  AnalyzeRequest,
  AnalyzeResponse,
  DownloadRequest,
  DownloadResponse,
  JobResponse,
  HealthResponse,
  ApiError,
} from './types';

const ERROR_MESSAGE_MAP: Record<string, string> = {
  INVALID_URL: 'Please enter a valid media URL (e.g. YouTube or Instagram).',
  UNSUPPORTED_PLATFORM: "This platform isn't supported yet. We currently support YouTube and Instagram.",
  VIDEO_UNAVAILABLE: 'This media is unavailable, private, or has been removed.',
  AUTHENTICATION_REQUIRED: 'This content requires login or is age-restricted and cannot be downloaded.',
  EXTRACTION_FAILED: 'Could not extract media info. Please verify the URL and try again.',
  ANALYSIS_NOT_FOUND: 'Your analysis session has expired. Please analyze the URL again.',
  FORMAT_NOT_FOUND: 'That format is no longer available. Please analyze the URL again.',
  JOB_NOT_FOUND: 'The requested download job was not found.',
  JOB_NOT_READY: 'Your file is still being prepared. Please wait a moment.',
  JOB_FAILED: 'Download failed during processing. Please try again.',
  JOB_EXPIRED: 'This download has expired. Please re-analyze the video to download again.',
  FILE_NOT_FOUND: 'The prepared file was not found or has been cleaned up.',
  UNAUTHORIZED_SESSION: 'Your download session expired or is unauthorized. Please try again.',
  RATE_LIMIT_EXCEEDED: 'Too many requests. Please wait a moment before trying again.',
  CONCURRENCY_LIMIT_EXCEEDED: 'Download limit reached. Please wait for your current download to finish.',
  VALIDATION_ERROR: 'Invalid input provided. Please check the URL and try again.',
  INTERNAL_ERROR: 'A temporary server error occurred. Please try again shortly.',
};

export function getFriendlyErrorMessage(code?: string | null, fallbackMessage?: string | null): string {
  if (code && ERROR_MESSAGE_MAP[code]) {
    return ERROR_MESSAGE_MAP[code];
  }
  return fallbackMessage || 'An unexpected error occurred. Please try again.';
}

export const getApiBaseUrl = (): string => {
  if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) {
    return (import.meta.env.VITE_API_BASE_URL as string).replace(/\/+$/, '');
  }
  if (typeof window !== 'undefined') {
    const host = window.location.hostname;
    if (host && host !== 'localhost' && host !== '127.0.0.1') {
      return 'https://mediaflow-c83t.onrender.com';
    }
  }
  return '';
};

export const DEFAULT_API_BASE_URL = getApiBaseUrl();

export function getOrCreateSessionId(): string {
  if (typeof window === 'undefined') return '';
  try {
    let sess = localStorage.getItem('downloader_session_id');
    if (!sess) {
      sess = 'sess_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
      localStorage.setItem('downloader_session_id', sess);
    }
    return sess;
  } catch {
    return '';
  }
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = DEFAULT_API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const sessionId = getOrCreateSessionId();
    const defaultHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(sessionId ? { 'X-Session-ID': sessionId } : {}),
    };

    const config: RequestInit = {
      ...options,
      credentials: 'include', // Preserves downloader_session cookie
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    let response: Response;
    try {
      response = await fetch(url, config);
    } catch {
      throw {
        code: 'NETWORK_ERROR',
        message: 'Could not connect to the server. Please check your internet connection.',
      } as ApiError;
    }

    // Persist server-provided session ID if present
    const serverSession = response.headers.get('X-Session-ID');
    if (serverSession && typeof window !== 'undefined') {
      try {
        localStorage.setItem('downloader_session_id', serverSession);
      } catch {}
    }

    let data: any;
    try {
      data = await response.json();
    } catch {
      data = null;
    }

    if (!response.ok) {
      const code =
        data?.error?.code ||
        data?.error_code ||
        data?.detail?.error_code ||
        'UNKNOWN_ERROR';
      const rawMessage =
        data?.error?.message ||
        data?.message ||
        data?.detail?.message ||
        response.statusText;
      const friendlyMessage = getFriendlyErrorMessage(code, rawMessage);

      throw {
        code,
        message: friendlyMessage,
        details: data?.error?.details || data?.detail,
      } as ApiError;
    }

    return data as T;
  }

  /**
   * Analyze media URL to fetch metadata and available formats.
   */
  async analyze(req: AnalyzeRequest): Promise<AnalyzeResponse> {
    return this.request<AnalyzeResponse>('/api/analyze', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  }

  /**
   * Queue a media download job.
   */
  async createDownload(req: DownloadRequest): Promise<DownloadResponse> {
    return this.request<DownloadResponse>('/api/download', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  }

  /**
   * Fetch status of a download job (polling fallback).
   */
  async getJob(jobId: string): Promise<JobResponse> {
    return this.request<JobResponse>(`/api/jobs/${jobId}`);
  }

  /**
   * Delete or cancel a download job.
   */
  async cancelJob(jobId: string): Promise<{ job_id: string; status: string }> {
    return this.request<{ job_id: string; status: string }>(`/api/jobs/${jobId}`, {
      method: 'DELETE',
    });
  }

  /**
   * System health check.
   */
  async checkHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/api/health');
  }

  /**
   * Constructs the absolute file download URL with session authentication.
   */
  getFileDownloadUrl(jobId: string): string {
    const base = this.baseUrl || getApiBaseUrl();
    const sessionId = getOrCreateSessionId();
    const query = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
    return `${base}/api/jobs/${encodeURIComponent(jobId)}/file${query}`;
  }
}

export const api = new ApiClient();
