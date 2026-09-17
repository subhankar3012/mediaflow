-- =====================================================================
-- Media Downloader Engine Schema Migration
-- Migration: 20260915000000_create_media_downloader_tables.sql
-- Description: Creates media_analyses and download_jobs tables with
--              indexes, constraints, and Row Level Security (RLS).
-- =====================================================================

-- Ensure pgcrypto extension is active
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ---------------------------------------------------------------------
-- Table: media_analyses
-- Stores metadata and normalized available formats extracted via yt-dlp.
-- ---------------------------------------------------------------------
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

-- Indexes for media_analyses
CREATE INDEX IF NOT EXISTS idx_media_analyses_session_id ON public.media_analyses(session_id);
CREATE INDEX IF NOT EXISTS idx_media_analyses_created_at ON public.media_analyses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_media_analyses_expires_at ON public.media_analyses(expires_at);

-- ---------------------------------------------------------------------
-- Table: download_jobs
-- Tracks the lifecycle, status, and progress of media download jobs.
-- ---------------------------------------------------------------------
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

-- Performance Indexes for download_jobs
CREATE INDEX IF NOT EXISTS idx_download_jobs_user_id ON public.download_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_download_jobs_session_id ON public.download_jobs(session_id);
CREATE INDEX IF NOT EXISTS idx_download_jobs_status ON public.download_jobs(status);
CREATE INDEX IF NOT EXISTS idx_download_jobs_created_at ON public.download_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_download_jobs_expires_at ON public.download_jobs(expires_at);

-- ---------------------------------------------------------------------
-- Row Level Security (RLS)
-- Protects media analyses and download jobs from unauthorized access.
-- ---------------------------------------------------------------------
ALTER TABLE public.media_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.download_jobs ENABLE ROW LEVEL SECURITY;

-- 1. Service Role Policies: Full access for backend worker & API
CREATE POLICY "Service role full access on media_analyses"
    ON public.media_analyses
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access on download_jobs"
    ON public.download_jobs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- 2. Authenticated Users: View only their own download jobs
CREATE POLICY "Authenticated users view own download_jobs"
    ON public.download_jobs
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

-- 3. Anonymous Sessions: Can only view jobs matching their X-Session-ID header
CREATE POLICY "Anon view matching session download_jobs"
    ON public.download_jobs
    FOR SELECT
    TO anon
    USING (
        session_id IS NOT NULL 
        AND session_id = COALESCE(
            NULLIF(current_setting('request.headers', true)::json->>'x-session-id', ''),
            ''
        )
    );

CREATE POLICY "Anon view matching session media_analyses"
    ON public.media_analyses
    FOR SELECT
    TO anon
    USING (
        session_id IS NOT NULL 
        AND session_id = COALESCE(
            NULLIF(current_setting('request.headers', true)::json->>'x-session-id', ''),
            ''
        )
    );
