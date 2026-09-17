# Media Downloader Engine (Backend-First Architecture)

A production-grade, modular media-downloader system built with **FastAPI**, **yt-dlp**, **FFmpeg**, and **Supabase PostgreSQL**. Designed strictly with a backend-first architecture, separating the core downloader engine from any frontend consumer.

---

## 1. Architecture Diagram

```
                              CLIENT
                                │
                                ▼
                       MINIMAL TESTING UI
               (React + TypeScript · Vite · SSE)
                                │
                                ▼
                         FASTAPI BACKEND
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
Security & SSRF            Job Service               Platform
  Rate Limiter           (State Machine)             Registry
(Sliding Window)         (SSE Event Hub)        (YouTube / Insta)
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
 [POST /api/analyze]                           [POST /api/download]
    YtDlpService                                     JobQueue
(Metadata Extraction)                        (AsyncIO / Redis Ready)
(Format Normalization)                                  │
        │                                               ▼
        ▼                                        DownloadWorker
 media_analyses                                         │
(PostgreSQL JSONB)                      ┌───────────────┴───────────────┐
                                        ▼                               ▼
                                     yt-dlp                           FFmpeg
                               (Media Download)                  (Remux & Merge)
                               (Progress Hooks)                  (Audio Extract)
                                        └───────────────┬───────────────┘
                                                        ▼
                                                 StorageService
                                             /tmp/downloader/{job_id}/
                                            (source/ working/ output/)
                                                        │
                                                        ▼
                                              GET /api/jobs/{id}/file
                                            (Streaming Delivery with RLS)
                                                        │
                                                        ▼
                                                  CleanupEngine
                                            (Scheduled / On-Demand Purge)
                                                        │
                                                        ▼
                                               download_jobs State
                                              (Supabase PostgreSQL)
```

---

## 2. Project Structure

```
project/
├── frontend/                               # Minimal testing interface
│   ├── src/
│   │   ├── App.tsx                        # Pure functional testing UI
│   │   ├── main.tsx
│   │   └── index.css
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.ts                     # Proxies /api to FastAPI backend
│
├── backend/
│   ├── app/
│   │   ├── main.py                        # FastAPI entrypoint & lifecycle
│   │   ├── config.py                      # Pydantic Settings (.env)
│   │   ├── api/
│   │   │   ├── __init__.py                # Router aggregator
│   │   │   ├── analyze.py                 # POST /api/analyze
│   │   │   ├── downloads.py               # POST /api/download
│   │   │   ├── jobs.py                    # GET status, SSE stream, file delivery
│   │   │   └── health.py                  # GET /api/health
│   │   ├── services/
│   │   │   ├── ytdlp_service.py           # yt-dlp Python integration
│   │   │   ├── ffmpeg_service.py          # FFmpeg stream-copy & merge
│   │   │   ├── job_service.py             # State machine & SSE event hub
│   │   │   ├── storage_service.py         # Isolated temp storage manager
│   │   │   └── cleanup_service.py         # Scheduled & startup cleanup
│   │   ├── platforms/
│   │   │   ├── base.py                    # PlatformHandler ABC
│   │   │   ├── youtube.py                 # YouTube extractor & format builder
│   │   │   └── instagram.py               # Instagram extractor & format builder
│   │   ├── workers/
│   │   │   ├── queue.py                   # Decoupled queue abstraction
│   │   │   └── download_worker.py         # Long-running async download worker
│   │   ├── database/
│   │   │   ├── __init__.py                # Repository factory
│   │   │   ├── supabase.py                # Supabase client provider
│   │   │   └── repositories/
│   │   │       ├── base.py                # BaseRepository interface
│   │   │       ├── supabase_repository.py # Native Supabase PostgreSQL adapter
│   │   │       └── sqlite_repository.py   # Explicit SQLite dev adapter
│   │   ├── schemas/
│   │   │   ├── format.py                  # NormalizedFormat model
│   │   │   ├── analyze.py                 # AnalyzeRequest / AnalyzeResponse
│   │   │   ├── download.py                # DownloadRequest / DownloadResponse
│   │   │   └── job.py                     # JobStatus, JobResponse
│   │   ├── security/
│   │   │   ├── url_validator.py           # SSRF & domain validation
│   │   │   ├── rate_limiter.py            # Sliding-window rate limiter
│   │   │   └── session.py                 # Cryptographic session manager
│   │   └── utils/
│   │       ├── logger.py                  # Structured logging
│   │       └── system.py                  # Tool & binary checks
│   ├── tests/
│   │   ├── test_url_validator.py
│   │   ├── test_format_normalization.py
│   │   ├── test_job_state_machine.py
│   │   ├── test_storage_service.py
│   │   └── test_api_endpoints.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── supabase/
│   └── migrations/
│       └── 20260915000000_create_media_downloader_tables.sql
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 3. Environment Setup Instructions

Copy the template configuration:
```bash
cp .env.example .env
```

Key environment variables:
| Variable | Description | Default |
|---|---|---|
| `ENVIRONMENT` | Runtime environment (`development`, `production`, `testing`) | `development` |
| `DB_ADAPTER` | Database adapter: `supabase` (required for prod), `sqlite`, `memory` | `sqlite` |
| `SQLITE_DB_PATH` | Path for local SQLite database file | `./downloader.db` |
| `SUPABASE_URL` | Supabase project URL (`https://<id>.supabase.co`) | Required for Supabase |
| `SUPABASE_SERVICE_ROLE_KEY`| Supabase Service Role Key (Backend only!) | Required for Supabase |
| `TEMP_STORAGE_PATH` | Base directory for temporary job media | `./tmp_downloader` |
| `MAX_OUTPUT_SIZE_BYTES` | Maximum allowed media file size | `2147483648` (2 GB) |
| `MAX_JOB_DURATION_SECONDS`| Subprocess timeout guard | `600` (10 minutes) |
| `JOB_EXPIRATION_MINUTES`| Retention time before media is deleted | `30` (minutes) |
| `MAX_REQUESTS_PER_MINUTE` | Per-client sliding window request rate limit | `60` |
| `MAX_CONCURRENT_JOBS_PER_SESSION`| Concurrency guard per session | `2` |
| `MAX_CONCURRENT_JOBS_GLOBAL` | Global worker concurrency capacity | `5` |

---

## 4. Supabase Migration SQL

Execute in Supabase SQL Editor:
```sql
-- Ensure pgcrypto extension is active
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- media_analyses: Stores analysis sessions and normalized format JSONB
CREATE TABLE IF NOT EXISTS public.media_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NULL,
    source_url TEXT NOT NULL,
    platform TEXT NOT NULL,
    title TEXT NULL,
    thumbnail TEXT NULL,
    duration INTEGER NULL,
    uploader TEXT NULL,
    normalized_formats JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_media_analyses_session_id ON public.media_analyses(session_id);
CREATE INDEX IF NOT EXISTS idx_media_analyses_created_at ON public.media_analyses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_media_analyses_expires_at ON public.media_analyses(expires_at);

-- download_jobs: State, progress snapshots, error messages, and expiration
CREATE TABLE IF NOT EXISTS public.download_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NULL REFERENCES public.media_analyses(id) ON DELETE SET NULL,
    user_id UUID NULL,
    session_id TEXT NULL,
    source_url TEXT NOT NULL,
    platform TEXT NOT NULL,
    title TEXT NULL,
    status TEXT NOT NULL DEFAULT 'QUEUED' CHECK (
        status IN ('QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED', 'EXPIRED', 'CANCELLED')
    ),
    requested_format TEXT NULL,
    output_format TEXT NULL,
    progress NUMERIC NOT NULL DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    downloaded_bytes BIGINT NULL,
    total_bytes BIGINT NULL,
    speed TEXT NULL,
    eta TEXT NULL,
    file_size BIGINT NULL,
    temporary_file_key TEXT NULL,
    error_code TEXT NULL,
    error_message TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ NULL,
    completed_at TIMESTAMPTZ NULL,
    expires_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS idx_download_jobs_user_id ON public.download_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_download_jobs_session_id ON public.download_jobs(session_id);
CREATE INDEX IF NOT EXISTS idx_download_jobs_status ON public.download_jobs(status);
CREATE INDEX IF NOT EXISTS idx_download_jobs_created_at ON public.download_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_download_jobs_expires_at ON public.download_jobs(expires_at);

-- Enable Row Level Security
ALTER TABLE public.media_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.download_jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access on media_analyses"
    ON public.media_analyses FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access on download_jobs"
    ON public.download_jobs FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Anon view session jobs"
    ON public.download_jobs FOR SELECT TO anon USING (session_id IS NOT NULL);
```

---

## 5. API Documentation

### `GET /api/health`
Returns system diagnostics (API status, Database health, yt-dlp version, FFmpeg/FFprobe presence, storage writeability).

### `POST /api/analyze`
Submits a public media URL for metadata and format extraction.
- **Request Body**:
  ```json
  { "url": "https://www.youtube.com/watch?v=..." }
  ```
- **Response**:
  ```json
  {
    "analysis_id": "f8a7e0c4-95b2-4d2a-89de-d93eb129759c",
    "platform": "youtube",
    "source_url": "https://www.youtube.com/watch?v=...",
    "title": "Sample Media",
    "thumbnail": "https://i.ytimg.com/...",
    "duration": 210,
    "uploader": "Author",
    "formats": [
      {
        "format_id": "18",
        "type": "video+audio",
        "container": "mp4",
        "width": 640,
        "height": 360,
        "fps": 30,
        "vcodec": "avc1.42001E",
        "acodec": "mp4a.40.2",
        "bitrate": 600.5,
        "has_audio": true,
        "has_video": true,
        "filesize": 15728640
      }
    ],
    "expires_at": "2026-09-15T11:45:00Z"
  }
  ```

### `POST /api/download`
Creates an asynchronous download job for a verified format.
- **Request Body**:
  ```json
  {
    "analysis_id": "f8a7e0c4-95b2-4d2a-89de-d93eb129759c",
    "format_id": "18",
    "output_format": "mp4"
  }
  ```
- **Response**:
  ```json
  {
    "job_id": "3b2e59a1-872f-410a-b21a-47120df077b9",
    "status": "QUEUED",
    "message": "Download job created and enqueued successfully"
  }
  ```

### `GET /api/jobs/{job_id}/events`
Server-Sent Events (SSE) live progress stream.
Streams status changes, download percentage, speed, ETA, and final download URL.

### `GET /api/jobs/{job_id}`
Polling fallback for job status and progress snapshot.

### `GET /api/jobs/{job_id}/file`
Secure streaming delivery of completed media. Returns media with safe `Content-Disposition` filename.

### `DELETE /api/jobs/{job_id}`
Cancels processing job or purges stored media on demand.

---

## 6. Worker Lifecycle Explanation

1. **Queue Dequeue**: The `DownloadWorker` asynchronously pulls the next `job_id` from `job_queue`.
2. **Directory Allocation**: `storage_service.create_job_dirs(job_id)` isolates execution in `TEMP_STORAGE_PATH/{job_id}/(source, working, output)`.
3. **State Transition**: State moves to `PROCESSING` and start timestamp is recorded.
4. **Execution**: `ytdlp_service.download_media_async()` downloads the selected format stream into `source/`. Realtime progress events are emitted to SSE and throttled to the database.
5. **Stream Analysis & FFmpeg**: If separate video/audio streams are downloaded, `ffmpeg_service.merge_video_audio()` executes stream-copy remuxing (`-c copy`) without re-encoding. If audio conversion (e.g. MP3) is requested, `ffmpeg_service.extract_audio()` is executed.
6. **Output Validation**: File presence, non-zero size, and `< MAX_OUTPUT_SIZE_BYTES` are verified in `output/`.
7. **Intermediate Purge**: `source/` and `working/` are purged; only `output/final.<ext>` is preserved.
8. **Completion**: State moves to `COMPLETED` with file size and expiration timestamp.
9. **Failure Protection**: On any error or timeout, state moves to `FAILED` with normalized error code/message and all temporary files are purged.

---

## 7. yt-dlp Integration Explanation

- **Direct Python API**: yt-dlp is integrated natively through `import yt_dlp` inside `app/services/ytdlp_service.py`.
- **Extraction vs. Download**: Extraction uses `extract_info(download=False)` with timeouts and playlist handling.
- **Normalization**: Translates raw format structures into clean `NormalizedFormat` objects.
- **Progress Hooks**: Captures `downloaded_bytes`, `total_bytes`, `speed`, and `eta`, formatting them cleanly.

---

## 8. FFmpeg Integration Explanation

- **Dedicated Service**: `FFmpegService` inside `app/services/ffmpeg_service.py`.
- **Stream Copy Priority**: Always attempts `-c copy` with stream mapping (`-map 0:v:0 -map 1:a:0`). Re-encoding only occurs when containers or codecs strictly require it (e.g. converting AAC/Opus to MP3).
- **Subprocess Isolation**: Commands are invoked using `asyncio.create_subprocess_exec` with structured arguments (never arbitrary shell strings).

---

## 9. Temporary Storage Strategy

Temporary media is organized in strictly isolated folders:
```
TEMP_STORAGE_PATH/
    └── {job_id}/
        ├── source/     # Raw downloaded stream(s)
        ├── working/    # FFmpeg scratch files
        └── output/     # Validated final deliverable (final.mp4)
```
- Server-generated filenames prevent user filesystem path injection.
- Path traversal validation (`StorageSecurityError`) rejects any path escaping the base storage path.

---

## 10. Cleanup Strategy

1. **Startup Cleanup**: `cleanup_service.startup_cleanup()` purges any directories lingering from a server crash/restart.
2. **Periodic Cleanup**: Background asyncio task runs every 60 seconds, querying jobs with `expires_at < now()`, purges disk storage, and marks status `EXPIRED`.
3. **Failure Cleanup**: Immediate purge on any download error or cancellation.
4. **On-Demand Cleanup**: `DELETE /api/jobs/{job_id}` purges storage immediately.

---

## 11. Security Model

- **SSRF Prevention**: Strict URL parsing, domain allowlist (`youtube.com`, `instagram.com`), and DNS resolution check rejecting loopback, private, link-local, and cloud metadata (e.g. `169.254.169.254`) IP addresses.
- **Format Verification**: Client format ID is validated against server-stored analysis before job creation.
- **Rate Limiting**: Sliding-window rate limiter per client IP/session (`MAX_REQUESTS_PER_MINUTE`).
- **Concurrency Guards**: Limits per session (`MAX_CONCURRENT_JOBS_PER_SESSION`) and global queue limits.
- **Timeout Protection**: `MAX_JOB_DURATION_SECONDS` terminates hung downloads.
- **Credentials Protection**: Supabase Service Role Key is kept exclusively in backend environment variables and never logged or exposed.

---

## 12. Local Development Instructions

### Backend:
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # On Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Run Tests:
```bash
cd backend
.venv\Scripts\pytest -v tests
```

### Frontend:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` to test the pipeline.

---

## 13. Production Deployment Considerations

- **Containerization**: Use `docker-compose.yml` to launch backend and frontend.
- **Database**: Set `ENVIRONMENT=production` and `DB_ADAPTER=supabase`. The engine will refuse to start if Supabase credentials are not provided in production.
- **Durable Queue**: Replace `AsyncIOJobQueue` with Redis/Celery if running multiple backend API instances.
- **Storage**: Swap `StorageService` to Supabase private storage or AWS S3 with signed download URLs for distributed architectures.

---

## 14. Known Limitations

- **Authentication / DRM**: Does not support private media requiring account credentials or DRM circumvention.
- **Platform Rate Limits**: Frequent downloads from a single IP may be throttled by media hosts; configure rotating proxies or rate limits accordingly.

---

## 15. Clear Instructions for Updating yt-dlp

As platform extractors evolve, update yt-dlp independently:

```bash
# In backend virtual environment:
pip install --upgrade yt-dlp

# Verify updated version:
python -c "import yt_dlp; print('Installed yt-dlp:', yt_dlp.__version__)"

# In Docker:
docker-compose build --no-cache backend
```
Restart backend services to apply the updated extractors.
