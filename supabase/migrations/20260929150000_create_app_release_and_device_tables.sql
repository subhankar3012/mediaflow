-- =====================================================================
-- MediaFlow Product Management Schema Migration
-- Migration: 20260929150000_create_app_release_and_device_tables.sql
-- Description: Creates app_releases and app_devices tables with
--              indexes, constraints, and Row Level Security (RLS).
-- =====================================================================

-- Ensure pgcrypto extension is active
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ---------------------------------------------------------------------
-- Table: app_releases
-- Stores metadata for mobile application updates & distribution.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.app_releases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_code INTEGER NOT NULL UNIQUE,
    version_name TEXT NOT NULL,
    apk_url TEXT NOT NULL,
    release_notes TEXT NOT NULL DEFAULT '',
    is_mandatory BOOLEAN NOT NULL DEFAULT false,
    min_supported_version INTEGER NOT NULL DEFAULT 20,
    published_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for querying latest version code
CREATE INDEX IF NOT EXISTS idx_app_releases_version_code ON public.app_releases(version_code DESC);

-- Enable RLS on app_releases
ALTER TABLE public.app_releases ENABLE ROW LEVEL SECURITY;

-- Allow public read access to releases
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'app_releases' AND policyname = 'Allow public read of releases'
    ) THEN
        CREATE POLICY "Allow public read of releases"
        ON public.app_releases
        FOR SELECT
        USING (true);
    END IF;
END $$;

-- ---------------------------------------------------------------------
-- Table: app_devices
-- Stores anonymous device registrations for push notifications (FCM).
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.app_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id TEXT NOT NULL UNIQUE,
    fcm_token TEXT NULL,
    app_version TEXT NOT NULL,
    version_code INTEGER NOT NULL,
    platform TEXT NOT NULL DEFAULT 'android',
    android_version TEXT NULL,
    notification_enabled BOOLEAN NOT NULL DEFAULT true,
    last_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for device lookups and push targeting
CREATE INDEX IF NOT EXISTS idx_app_devices_device_id ON public.app_devices(device_id);
CREATE INDEX IF NOT EXISTS idx_app_devices_fcm_token ON public.app_devices(fcm_token) WHERE fcm_token IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_app_devices_last_seen ON public.app_devices(last_seen DESC);

-- Enable RLS on app_devices
ALTER TABLE public.app_devices ENABLE ROW LEVEL SECURITY;

-- Allow insert/update of device records
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'app_devices' AND policyname = 'Allow anonymous device upsert'
    ) THEN
        CREATE POLICY "Allow anonymous device upsert"
        ON public.app_devices
        FOR ALL
        USING (true)
        WITH CHECK (true);
    END IF;
END $$;

-- ---------------------------------------------------------------------
-- Seed current production version (v1.5.7, versionCode 22)
-- ---------------------------------------------------------------------
INSERT INTO public.app_releases (
    version_code,
    version_name,
    apk_url,
    release_notes,
    is_mandatory,
    min_supported_version
) VALUES (
    22,
    '1.5.7',
    'https://github.com/subhankar3012/mediaflow/releases/latest/download/MediaFlow-release.apk',
    '• Fixed X/Twitter photo and video downloads with Syndication API\n• Added Reddit direct image and v.redd.it audio-video muxing\n• ImageQualityResolver: Original resolution for X, Reddit, and Pinterest\n• Fast video thumbnails in Library via native MediaMetadataRetriever\n• Resilient PhotoViewer and PlayerScreen with error recovery\n• Complete build cache purge and Android 15/16 stability',
    false,
    20
) ON CONFLICT (version_code) DO UPDATE SET
    version_name = EXCLUDED.version_name,
    apk_url = EXCLUDED.apk_url,
    release_notes = EXCLUDED.release_notes,
    published_at = now();
