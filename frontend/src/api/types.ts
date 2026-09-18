/**
 * TypeScript definitions matching API_CONTRACT.md
 */

export type MediaType = 'video' | 'audio' | 'video+audio' | 'image' | 'gallery';
export type OutputType = 'mp4' | 'mp3' | 'thumbnail' | 'zip';

export interface NormalizedFormat {
  format_id: string;
  type: MediaType;
  container: string;
  width?: number | null;
  height?: number | null;
  fps?: number | null;
  vcodec?: string | null;
  acodec?: string | null;
  bitrate?: number | null;
  has_audio: boolean;
  has_video: boolean;
  filesize?: number | null;
  filesize_approx?: number | null;
  format_note?: string | null;
  quality?: string | null;
  downloadable?: boolean;
}

export interface GalleryItem {
  index: number;
  id: string;
  type: 'image' | 'video';
  thumbnail?: string | null;
  display_url?: string | null;
  width?: number | null;
  height?: number | null;
  duration?: number | null;
  formats?: NormalizedFormat[];
}

export interface AnalyzeRequest {
  url: string;
}

export interface AnalyzeResponse {
  analysis_id: string;
  platform: string;
  source_url: string;
  title?: string | null;
  thumbnail?: string | null;
  duration?: number | null;
  uploader?: string | null;
  formats: NormalizedFormat[];
  is_gallery?: boolean;
  gallery_items?: GalleryItem[];
  media_type?: 'video' | 'audio' | 'image' | 'gallery';
  expires_at: string;
}

export interface DownloadRequest {
  analysis_id: string;
  format_id?: string;
  quality?: string;
  output_format?: string;
  audio_only?: boolean;
  selected_indices?: number[];
}

export interface DownloadResponse {
  job_id: string;
  status: 'QUEUED';
  message: string;
}

export type JobStatus =
  | 'QUEUED'
  | 'PROCESSING'
  | 'COMPLETED'
  | 'FAILED'
  | 'EXPIRED'
  | 'CANCELLED';

export interface JobResponse {
  id: string;
  analysis_id?: string | null;
  source_url?: string;
  platform?: string;
  title?: string | null;
  status: JobStatus;
  requested_format?: string | null;
  output_format?: string | null;
  progress: number;
  downloaded_bytes?: number | null;
  total_bytes?: number | null;
  speed?: string | null;
  eta?: string | null;
  file_size?: number | null;
  error_code?: string | null;
  error_message?: string | null;
  download_url?: string | null;
  created_at?: string;
  started_at?: string | null;
  completed_at?: string | null;
  expires_at?: string | null;
}

export interface SSEEventData {
  job_id: string;
  event?: 'status' | 'progress';
  status: JobStatus;
  progress: number;
  downloaded_bytes?: number | null;
  total_bytes?: number | null;
  speed?: string | null;
  eta?: string | null;
  download_url?: string | null;
  error_code?: string | null;
  error_message?: string | null;
  file_size?: number | null;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded';
  api: string;
  database: string;
  database_adapter: string;
  ytdlp: string;
  ytdlp_version?: string;
  ffmpeg: string;
  ffprobe: string;
  storage: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: any;
}
