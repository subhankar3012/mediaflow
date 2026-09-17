import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch
from app.services.ytdlp_service import ytdlp_service
from app.services.format_service import format_normalizer
from app.services.ffmpeg_service import ffmpeg_service, MediaValidationError
from app.platforms.youtube import youtube_handler
from app.platforms.instagram import instagram_handler

# --- Existing base normalization tests ---

def test_normalize_combined_video_audio():
    raw = {
        "format_id": "18",
        "ext": "mp4",
        "width": 640,
        "height": 360,
        "fps": 30,
        "vcodec": "avc1.42001E",
        "acodec": "mp4a.40.2",
        "tbr": 600.5,
        "filesize": 10485760,
        "format_note": "360p"
    }
    norm = ytdlp_service.normalize_format(raw)
    assert norm is not None
    assert norm.format_id == "18"
    assert norm.type == "video+audio"
    assert norm.container == "mp4"
    assert norm.width == 640
    assert norm.height == 360
    assert norm.has_video is True
    assert norm.has_audio is True
    assert norm.filesize == 10485760

def test_normalize_video_only():
    raw = {
        "format_id": "137",
        "ext": "mp4",
        "width": 1920,
        "height": 1080,
        "fps": 60,
        "vcodec": "avc1.640028",
        "acodec": "none",
        "tbr": 4500.0,
        "filesize_approx": 52428800
    }
    norm = ytdlp_service.normalize_format(raw)
    assert norm is not None
    assert norm.format_id == "137"
    assert norm.type == "video"
    assert norm.has_video is True
    assert norm.has_audio is False
    assert norm.height == 1080

def test_normalize_audio_only():
    raw = {
        "format_id": "140",
        "ext": "m4a",
        "vcodec": "none",
        "acodec": "mp4a.40.2",
        "abr": 128.0,
        "filesize": 5000000
    }
    norm = ytdlp_service.normalize_format(raw)
    assert norm is not None
    assert norm.format_id == "140"
    assert norm.type == "audio"
    assert norm.has_video is False
    assert norm.has_audio is True
    assert norm.container == "m4a"

def test_normalize_invalid_format():
    raw = {
        "format_id": "none",
        "vcodec": "none",
        "acodec": "none",
    }
    norm = ytdlp_service.normalize_format(raw)
    assert norm is None


# --- Requirement Tests: Format Normalization & Deduplication ---

def test_duplicate_resolution_grouping():
    """Verify multiple technical format streams at 1080p and 720p result in exactly ONE entry per resolution."""
    raw_formats = [
        {"format_id": "137", "ext": "mp4", "height": 1080, "vcodec": "avc1.640028", "acodec": "none", "tbr": 4000},
        {"format_id": "248", "ext": "webm", "height": 1080, "vcodec": "vp9", "acodec": "none", "tbr": 3500},
        {"format_id": "399", "ext": "mp4", "height": 1080, "vcodec": "av01.0.08M.08", "acodec": "none", "tbr": 3000},
        {"format_id": "136", "ext": "mp4", "height": 720, "vcodec": "avc1.4d401f", "acodec": "none", "tbr": 2000},
        {"format_id": "247", "ext": "webm", "height": 720, "vcodec": "vp9", "acodec": "none", "tbr": 1800},
        {"format_id": "140", "ext": "m4a", "vcodec": "none", "acodec": "mp4a.40.2", "abr": 128},
    ]

    normalized = format_normalizer.normalize_formats(raw_formats, platform="youtube")
    video_entries = [f for f in normalized if f.has_video]

    # Exactly 2 video resolution options: 1080p and 720p
    assert len(video_entries) == 2
    heights = [f.height for f in video_entries]
    assert heights == [1080, 720]
    qualities = [f.quality for f in video_entries]
    assert qualities == ["1080p", "720p"]


def test_missing_resolution_filtering():
    """Verify unavailable resolutions are NOT fabricated (e.g. source has only 360 and 1080)."""
    raw_formats = [
        {"format_id": "137", "ext": "mp4", "height": 1080, "vcodec": "avc1.640028", "acodec": "none", "tbr": 4000},
        {"format_id": "18", "ext": "mp4", "height": 360, "vcodec": "avc1.42001E", "acodec": "mp4a.40.2", "tbr": 600},
        {"format_id": "140", "ext": "m4a", "vcodec": "none", "acodec": "mp4a.40.2", "abr": 128},
    ]

    normalized = format_normalizer.normalize_formats(raw_formats, platform="youtube")
    heights = [f.height for f in normalized if f.has_video]

    assert heights == [1080, 360]
    assert 720 not in heights
    assert 480 not in heights
    assert 1440 not in heights
    assert 2160 not in heights


def test_h264_preference():
    """Verify H.264/AVC stream is prioritized over VP9 or AV1 for the same resolution."""
    raw_formats = [
        # VP9 has higher bitrate than H.264
        {"format_id": "248_vp9", "ext": "webm", "height": 1080, "vcodec": "vp09.00.51.08", "acodec": "none", "tbr": 5000},
        {"format_id": "137_h264", "ext": "mp4", "height": 1080, "vcodec": "avc1.640028", "acodec": "none", "tbr": 3500},
        {"format_id": "140", "ext": "m4a", "vcodec": "none", "acodec": "mp4a.40.2", "abr": 128},
    ]

    normalized = format_normalizer.normalize_formats(raw_formats, platform="youtube")
    fmt_1080 = next(f for f in normalized if f.height == 1080)

    # H.264 format must be chosen as source_video_format_id
    assert fmt_1080.source_video_format_id == "137_h264"


def test_aac_preference():
    """Verify AAC audio stream is prioritized over Opus audio stream."""
    raw_formats = [
        {"format_id": "137", "ext": "mp4", "height": 1080, "vcodec": "avc1.640028", "acodec": "none"},
        # Opus with higher bitrate
        {"format_id": "251_opus", "ext": "webm", "vcodec": "none", "acodec": "opus", "abr": 160},
        # AAC with lower bitrate
        {"format_id": "140_aac", "ext": "m4a", "vcodec": "none", "acodec": "mp4a.40.2", "abr": 128},
    ]

    normalized = format_normalizer.normalize_formats(raw_formats, platform="youtube")
    fmt_1080 = next(f for f in normalized if f.height == 1080)

    # AAC must be selected as source_audio_format_id
    assert fmt_1080.source_audio_format_id == "140_aac"


def test_internal_source_format_id_tracking():
    """Verify format normalization maintains internal yt-dlp format IDs while exposing clean quality labels."""
    raw_formats = [
        {"format_id": "raw_video_1080", "ext": "mp4", "height": 1080, "vcodec": "avc1.640028", "acodec": "none", "tbr": 4000},
        {"format_id": "raw_audio_128", "ext": "m4a", "vcodec": "none", "acodec": "mp4a.40.2", "abr": 128},
    ]

    normalized = format_normalizer.normalize_formats(raw_formats, platform="youtube")
    fmt = normalized[0]

    assert fmt.format_id == "1080p"
    assert fmt.quality == "1080p"
    assert fmt.source_video_format_id == "raw_video_1080"
    assert fmt.source_audio_format_id == "raw_audio_128"


def test_no_silent_downgrade():
    """Verify that if 1080p is available only in VP9, 1080p is STILL provided (for transcoding), not downgraded to 720p."""
    raw_formats = [
        {"format_id": "248_vp9_1080", "ext": "webm", "height": 1080, "vcodec": "vp9", "acodec": "none"},
        {"format_id": "136_h264_720", "ext": "mp4", "height": 720, "vcodec": "avc1.4d401f", "acodec": "none"},
        {"format_id": "140_aac", "ext": "m4a", "vcodec": "none", "acodec": "mp4a.40.2", "abr": 128},
    ]

    normalized = format_normalizer.normalize_formats(raw_formats, platform="youtube")
    heights = [f.height for f in normalized if f.has_video]

    assert 1080 in heights
    assert 720 in heights
    fmt_1080 = next(f for f in normalized if f.height == 1080)
    assert fmt_1080.source_video_format_id == "248_vp9_1080"


def test_1440p_and_2160p_availability():
    """Verify 1440p (2K) and 2160p (4K) are included ONLY when genuinely present in the source."""
    raw_with_4k = [
        {"format_id": "313_4k", "ext": "webm", "height": 2160, "vcodec": "vp9", "acodec": "none"},
        {"format_id": "271_2k", "ext": "webm", "height": 1440, "vcodec": "vp9", "acodec": "none"},
        {"format_id": "137_1080", "ext": "mp4", "height": 1080, "vcodec": "avc1.640028", "acodec": "none"},
        {"format_id": "140", "ext": "m4a", "vcodec": "none", "acodec": "mp4a.40.2", "abr": 128},
    ]
    norm_4k = format_normalizer.normalize_formats(raw_with_4k, platform="youtube")
    heights = [f.height for f in norm_4k if f.has_video]
    assert heights == [2160, 1440, 1080]

    raw_without_4k = [
        {"format_id": "137_1080", "ext": "mp4", "height": 1080, "vcodec": "avc1.640028", "acodec": "none"},
        {"format_id": "140", "ext": "m4a", "vcodec": "none", "acodec": "mp4a.40.2", "abr": 128},
    ]
    norm_no_4k = format_normalizer.normalize_formats(raw_without_4k, platform="youtube")
    heights_no_4k = [f.height for f in norm_no_4k if f.has_video]
    assert 2160 not in heights_no_4k
    assert 1440 not in heights_no_4k


def test_instagram_normalization_simplified():
    """Verify Instagram formats are reduced to a single Best Quality option tracking both video and audio."""
    raw_formats = [
        {"format_id": "insta_dash_video", "ext": "mp4", "height": 1080, "vcodec": "avc1.4d401f", "acodec": "none"},
        {"format_id": "insta_dash_audio", "ext": "m4a", "vcodec": "none", "acodec": "mp4a.40.2"},
    ]

    normalized = format_normalizer.normalize_formats(raw_formats, platform="instagram")
    assert len(normalized) == 1
    insta_fmt = normalized[0]
    assert insta_fmt.format_id == "best"
    assert insta_fmt.quality == "Best Quality"
    assert insta_fmt.has_video is True
    assert insta_fmt.has_audio is True
    assert insta_fmt.source_video_format_id == "insta_dash_video"
    assert insta_fmt.source_audio_format_id == "insta_dash_audio"


# --- Platform Handler Spec Tests ---

def test_youtube_build_format_spec_respects_resolution():
    """Verify YouTube handler builds format spec with requested resolution and H.264 preference."""
    spec_1080 = youtube_handler.build_format_spec("1080p")
    assert "height<=1080" in spec_1080
    assert "vcodec^=avc1" in spec_1080
    assert "bestaudio" in spec_1080

    spec_720 = youtube_handler.build_format_spec("720p")
    assert "height<=720" in spec_720

    spec_audio = youtube_handler.build_format_spec("audio_best", audio_only=True)
    assert "bestaudio" in spec_audio


def test_instagram_build_format_spec_includes_audio():
    """Verify Instagram handler always requests both video and audio to fix missing audio bug."""
    spec = instagram_handler.build_format_spec("best")
    assert spec == "bestvideo+bestaudio/best"


# --- FFprobe Validation Tests ---

@pytest.mark.asyncio
async def test_ffprobe_validation_h264_aac_success(tmp_path: Path):
    """Verify valid H.264 + AAC MP4 passes FFprobe validation."""
    dummy_file = tmp_path / "valid.mp4"
    dummy_file.write_bytes(b"dummy mp4 media content")

    mock_probe = {
        "format": {
            "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
            "duration": "42.5",
            "size": "1048576"
        },
        "streams": [
            {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080},
            {"codec_type": "audio", "codec_name": "aac", "sample_rate": "44100"}
        ]
    }

    with patch.object(ffmpeg_service, "probe", new_callable=AsyncMock) as mock:
        mock.return_value = mock_probe
        result = await ffmpeg_service.validate_media_file(dummy_file, is_audio_only=False)
        assert result["valid"] is True
        assert result["video_codec"] == "h264"
        assert result["audio_codec"] == "aac"
        assert result["duration"] == 42.5


@pytest.mark.asyncio
async def test_ffprobe_validation_video_only_fails(tmp_path: Path):
    """Verify video-only MP4 (missing audio) is REJECTED by validation."""
    dummy_file = tmp_path / "video_only.mp4"
    dummy_file.write_bytes(b"dummy video only")

    mock_probe = {
        "format": {
            "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
            "duration": "10.0",
            "size": "500000"
        },
        "streams": [
            {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080}
            # No audio stream
        ]
    }

    with patch.object(ffmpeg_service, "probe", new_callable=AsyncMock) as mock:
        mock.return_value = mock_probe
        with pytest.raises(MediaValidationError, match="Output contains no audio stream"):
            await ffmpeg_service.validate_media_file(dummy_file, is_audio_only=False)


@pytest.mark.asyncio
async def test_ffprobe_validation_incompatible_codec_fails(tmp_path: Path):
    """Verify non-H.264 video codec (e.g. VP9) inside MP4 is REJECTED."""
    dummy_file = tmp_path / "vp9_in_mp4.mp4"
    dummy_file.write_bytes(b"dummy vp9 in mp4")

    mock_probe = {
        "format": {
            "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
            "duration": "15.0",
            "size": "600000"
        },
        "streams": [
            {"codec_type": "video", "codec_name": "vp9", "width": 1920, "height": 1080},
            {"codec_type": "audio", "codec_name": "aac"}
        ]
    }

    with patch.object(ffmpeg_service, "probe", new_callable=AsyncMock) as mock:
        mock.return_value = mock_probe
        with pytest.raises(MediaValidationError, match="not standard H.264"):
            await ffmpeg_service.validate_media_file(dummy_file, is_audio_only=False)


@pytest.mark.asyncio
async def test_ffprobe_validation_missing_file_fails(tmp_path: Path):
    """Verify non-existent file is REJECTED."""
    missing_file = tmp_path / "does_not_exist.mp4"
    with pytest.raises(MediaValidationError, match="does not exist"):
        await ffmpeg_service.validate_media_file(missing_file)


@pytest.mark.asyncio
async def test_ffprobe_validation_zero_byte_fails(tmp_path: Path):
    """Verify empty 0-byte output file is REJECTED."""
    empty_file = tmp_path / "empty.mp4"
    empty_file.write_bytes(b"")
    with pytest.raises(MediaValidationError, match="empty"):
        await ffmpeg_service.validate_media_file(empty_file)
