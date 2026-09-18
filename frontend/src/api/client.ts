import type {
  AnalyzeRequest,
  AnalyzeResponse,
  DownloadRequest,
  DownloadResponse,
  JobResponse,
  HealthResponse,
  ApiError,
} from './types';

export interface FriendlyError {
  title: string;
  message: string;
  tip?: string;
}

export function sanitizeErrorMessage(code?: string | null, rawMessage?: string | null): FriendlyError {
  const raw = (rawMessage || '').toLowerCase();
  const c = (code || '').toUpperCase();

  // 1. Technical/internal errors: Database, Postgres, SQLite, 500, 502, 503, Exceptions, Tracebacks
  if (
    c === 'INTERNAL_ERROR' ||
    raw.includes('database') ||
    raw.includes('sql') ||
    raw.includes('postgres') ||
    raw.includes('sqlite') ||
    raw.includes('internal server error') ||
    raw.includes('server error') ||
    raw.includes('status code 500') ||
    raw.includes('status code 502') ||
    raw.includes('status code 503') ||
    raw.includes('traceback') ||
    raw.includes('exception') ||
    raw.includes('jsondecodeerror') ||
    raw.includes('fastapi') ||
    raw.includes('pydantic')
  ) {
    return {
      title: 'Temporary Server Hiccup',
      message: 'Our service experienced a brief connection hiccup while communicating with our background workers.',
      tip: 'Please wait a few seconds and try again. No download data was lost.',
    };
  }

  // 2. Network / connection problems
  if (
    c === 'NETWORK_ERROR' ||
    raw.includes('failed to fetch') ||
    raw.includes('network') ||
    raw.includes('timeout') ||
    raw.includes('econnrefused')
  ) {
    return {
      title: 'Connection Issue',
      message: 'Could not connect to our servers right now.',
      tip: 'Please check your internet connection or try again in a few moments.',
    };
  }

  // 3. Private, age-restricted, login-required, or removed media
  if (
    c === 'AUTHENTICATION_REQUIRED' ||
    c === 'VIDEO_UNAVAILABLE' ||
    raw.includes('private') ||
    raw.includes('login') ||
    raw.includes('removed') ||
    raw.includes('unavailable') ||
    raw.includes('sign in') ||
    raw.includes('restricted') ||
    raw.includes('this video is not available') ||
    raw.includes('post is unavailable')
  ) {
    return {
      title: 'Media Unavailable or Private',
      message: 'This post, reel, or video is either private, age-restricted, or removed by its creator.',
      tip: 'We can only download public content. Please verify that the post is accessible without an account.',
    };
  }

  // 4. Invalid or unsupported URL
  if (
    c === 'INVALID_URL' ||
    c === 'UNSUPPORTED_PLATFORM' ||
    raw.includes('unsupported') ||
    raw.includes('invalid url') ||
    raw.includes('not a valid')
  ) {
    return {
      title: 'Invalid Media Link',
      message: 'We could not recognize this link.',
      tip: 'Make sure you copy a complete, valid link from YouTube (video/short) or Instagram (reel/post/carousel/story).',
    };
  }

  // 5. Rate limit / high demand
  if (
    c === 'RATE_LIMIT_EXCEEDED' ||
    c === 'CONCURRENCY_LIMIT_EXCEEDED' ||
    raw.includes('rate limit') ||
    raw.includes('too many')
  ) {
    return {
      title: 'High Server Traffic',
      message: 'Our servers are currently handling high traffic from multiple downloaders.',
      tip: 'Please wait about 10-15 seconds before trying again.',
    };
  }

  // 6. Extraction or format issues
  if (
    c === 'EXTRACTION_FAILED' ||
    c === 'FORMAT_NOT_FOUND' ||
    raw.includes('extract') ||
    raw.includes('no video formats') ||
    raw.includes('yt-dlp') ||
    raw.includes('ytdl')
  ) {
    return {
      title: 'Could Not Retrieve Media',
      message: 'We were unable to extract media streams from this link.',
      tip: 'The platform might be temporarily restricting access. Please check the link and try again.',
    };
  }

  // 7. Expired jobs or sessions
  if (c === 'JOB_EXPIRED' || c === 'ANALYSIS_NOT_FOUND' || c === 'UNAUTHORIZED_SESSION') {
    return {
      title: 'Session Expired',
      message: 'Your download session has expired due to inactivity.',
      tip: 'Please re-paste or search the link again to start a fresh download.',
    };
  }

  // 8. Fallback friendly message
  const hasRawErrorWord = raw.includes('error') || raw.includes('fail') || raw.includes('cannot');
  return {
    title: 'Download Interrupted',
    message: rawMessage && !hasRawErrorWord && rawMessage.length < 80
      ? rawMessage
      : 'Something unexpected occurred while preparing your download.',
    tip: 'Please try analyzing the link again, or check back in a few moments.',
  };
}

export function getFriendlyErrorMessage(code?: string | null, fallbackMessage?: string | null): string {
  const sanitized = sanitizeErrorMessage(code, fallbackMessage);
  return sanitized.message;
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
      const sanitized = sanitizeErrorMessage(code, rawMessage);

      throw {
        code,
        title: sanitized.title,
        message: sanitized.message,
        tip: sanitized.tip,
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
