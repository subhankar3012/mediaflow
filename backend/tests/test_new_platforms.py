import pytest
from app.security.url_validator import (
    validate_and_normalize_url,
    UnsupportedDomainError,
    SSRFBlockedError,
    InvalidURLError,
)
from app.platforms import get_platform_handler
from app.platforms.x import x_handler
from app.platforms.facebook import facebook_handler
from app.platforms.pinterest import pinterest_handler
from app.platforms.reddit import reddit_handler
from app.services.format_service import format_normalizer

# =====================================================================
# 1. URL Validation & Platform Matching Tests
# =====================================================================

def test_x_twitter_url_validation():
    urls = [
        ("https://x.com/user/status/1234567890", "x"),
        ("https://www.x.com/user/status/1234567890", "x"),
        ("https://twitter.com/user/status/1234567890", "x"),
        ("https://www.twitter.com/user/status/1234567890", "x"),
        ("https://mobile.twitter.com/user/status/1234567890", "x"),
    ]
    for raw_url, expected_platform in urls:
        norm_url, platform = validate_and_normalize_url(raw_url)
        assert platform == expected_platform
        handler = get_platform_handler(norm_url)
        assert handler is not None
        assert handler.name == "x"

def test_facebook_url_validation():
    urls = [
        ("https://www.facebook.com/watch/?v=123456789", "facebook"),
        ("https://facebook.com/reel/123456789", "facebook"),
        ("https://m.facebook.com/story.php?story_fbid=123", "facebook"),
        ("https://web.facebook.com/user/videos/123456789", "facebook"),
        ("https://fb.watch/abcdef1234/", "facebook"),
    ]
    for raw_url, expected_platform in urls:
        norm_url, platform = validate_and_normalize_url(raw_url)
        assert platform == expected_platform
        handler = get_platform_handler(norm_url)
        assert handler is not None
        assert handler.name == "facebook"

def test_pinterest_url_validation():
    urls = [
        ("https://www.pinterest.com/pin/123456789012345678/", "pinterest"),
        ("https://pinterest.com/pin/123456789012345678/", "pinterest"),
        ("https://pin.it/7xyz123", "pinterest"),
    ]
    for raw_url, expected_platform in urls:
        norm_url, platform = validate_and_normalize_url(raw_url)
        assert platform == expected_platform
        handler = get_platform_handler(norm_url)
        assert handler is not None
        assert handler.name == "pinterest"

def test_reddit_url_validation():
    urls = [
        ("https://www.reddit.com/r/videos/comments/123abc4/sample_video/", "reddit"),
        ("https://reddit.com/r/funny/comments/567def8/sample_clip/", "reddit"),
        ("https://old.reddit.com/r/aww/comments/999xyz/cat_video/", "reddit"),
        ("https://v.redd.it/abcdef123456", "reddit"),
        ("https://redd.it/123abc4", "reddit"),
    ]
    for raw_url, expected_platform in urls:
        norm_url, platform = validate_and_normalize_url(raw_url)
        assert platform == expected_platform
        handler = get_platform_handler(norm_url)
        assert handler is not None
        assert handler.name == "reddit"

def test_unsupported_domain_rejected():
    with pytest.raises(UnsupportedDomainError):
        validate_and_normalize_url("https://vimeo.com/123456789")

    with pytest.raises(UnsupportedDomainError):
        validate_and_normalize_url("https://malicious-site.com/fake.mp4")

# =====================================================================
# 2. SSRF Protection Tests for New Domains
# =====================================================================

def test_ssrf_blocked_on_local_ips():
    with pytest.raises(SSRFBlockedError):
        validate_and_normalize_url("http://127.0.0.1/video.mp4")
    with pytest.raises(SSRFBlockedError):
        validate_and_normalize_url("http://192.168.1.1/video.mp4")
    with pytest.raises(SSRFBlockedError):
        validate_and_normalize_url("http://169.254.169.254/latest/meta-data/")

# =====================================================================
# 3. Format Normalization Tests for New Platforms
# =====================================================================

def test_x_format_normalization():
    mock_raw_formats = [
        {"format_id": "http-270", "ext": "mp4", "width": 480, "height": 270, "vcodec": "avc1", "acodec": "mp4a", "tbr": 256.0},
        {"format_id": "http-720", "ext": "mp4", "width": 1280, "height": 720, "vcodec": "avc1", "acodec": "mp4a", "tbr": 2176.0},
        {"format_id": "http-1080", "ext": "mp4", "width": 1920, "height": 1080, "vcodec": "avc1", "acodec": "mp4a", "tbr": 4352.0},
        {"format_id": "audio-only", "ext": "m4a", "vcodec": "none", "acodec": "mp4a", "abr": 128.0},
    ]

    normalized = format_normalizer.normalize_formats(mock_raw_formats, platform="x", duration=30)
    assert len(normalized) > 0

    # Ensure heights are sorted descending
    video_formats = [f for f in normalized if f.has_video]
    heights = [f.height for f in video_formats]
    assert heights == sorted(heights, reverse=True)
    assert 1080 in heights
    assert 720 in heights

    # Ensure audio MP3 format exists
    audio_formats = [f for f in normalized if f.type == "audio"]
    assert len(audio_formats) == 1
    assert audio_formats[0].container == "mp3"
    assert audio_formats[0].has_audio is True

def test_facebook_format_normalization():
    mock_raw_formats = [
        {"format_id": "sd", "ext": "mp4", "width": 854, "height": 480, "vcodec": "avc1", "acodec": "mp4a", "tbr": 600.0},
        {"format_id": "hd", "ext": "mp4", "width": 1920, "height": 1080, "vcodec": "avc1", "acodec": "mp4a", "tbr": 2500.0},
    ]

    normalized = format_normalizer.normalize_formats(mock_raw_formats, platform="facebook", duration=60)
    assert len(normalized) >= 2
    video_formats = [f for f in normalized if f.has_video]
    assert any(f.height == 1080 for f in video_formats)
    # Audio extraction format present
    assert any(f.type == "audio" and f.container == "mp3" for f in normalized)

def test_pinterest_video_pin_normalization():
    mock_raw_formats = [
        {"format_id": "v720", "ext": "mp4", "width": 720, "height": 1280, "vcodec": "h264", "acodec": "aac", "tbr": 1500.0},
    ]
    normalized = format_normalizer.normalize_formats(mock_raw_formats, platform="pinterest", duration=15)
    assert len(normalized) >= 1
    assert normalized[0].has_video is True
    assert normalized[0].container == "mp4"

def test_pinterest_photo_pin_normalization():
    # Photo pin: no video streams, only raw image metadata
    mock_raw_formats = []
    normalized = format_normalizer.normalize_formats(mock_raw_formats, platform="pinterest", duration=None)
    assert len(normalized) == 1
    assert normalized[0].type == "image"
    assert normalized[0].format_id == "original_image"
    assert normalized[0].container == "jpg"
    assert normalized[0].downloadable is True

def test_reddit_dash_format_normalization():
    mock_raw_formats = [
        {"format_id": "fallback", "ext": "mp4", "width": 1920, "height": 1080, "vcodec": "h264", "acodec": "none", "tbr": 3000.0},
        {"format_id": "720p", "ext": "mp4", "width": 1280, "height": 720, "vcodec": "h264", "acodec": "none", "tbr": 1800.0},
        {"format_id": "480p", "ext": "mp4", "width": 854, "height": 480, "vcodec": "h264", "acodec": "none", "tbr": 800.0},
        {"format_id": "audio-0", "ext": "m4a", "vcodec": "none", "acodec": "aac", "abr": 128.0},
    ]

    normalized = format_normalizer.normalize_formats(mock_raw_formats, platform="reddit", duration=45)
    video_formats = [f for f in normalized if f.has_video]
    assert len(video_formats) >= 3

    # Crucial DASH requirement: Has audio must be true because bestaudio will be remuxed by FFmpeg
    for vf in video_formats:
        assert vf.has_audio is True
        assert vf.vcodec == "h264"
        assert vf.acodec == "aac"

    # Audio extraction format present
    audio_formats = [f for f in normalized if f.type == "audio"]
    assert len(audio_formats) == 1
    assert audio_formats[0].container == "mp3"

# =====================================================================
# 4. Format Spec String Building Tests
# =====================================================================

def test_format_spec_builders():
    # X handler
    spec_x_1080 = x_handler.build_format_spec("1080p")
    assert "bestvideo[height<=1080]+bestaudio" in spec_x_1080
    spec_x_audio = x_handler.build_format_spec("any", audio_only=True)
    assert spec_x_audio == "bestaudio/best"

    # Facebook handler
    spec_fb_hd = facebook_handler.build_format_spec("hd")
    assert "hd/bestvideo+bestaudio/best" == spec_fb_hd
    spec_fb_audio = facebook_handler.build_format_spec("any", audio_only=True)
    assert spec_fb_audio == "bestaudio/best"

    # Pinterest handler
    spec_pin_video = pinterest_handler.build_format_spec("720p")
    assert "bestvideo[height<=720]+bestaudio" in spec_pin_video
    spec_pin_audio = pinterest_handler.build_format_spec("any", audio_only=True)
    assert spec_pin_audio == "bestaudio/best"

    # Reddit handler
    spec_reddit_1080 = reddit_handler.build_format_spec("1080p")
    assert "bestvideo[height<=1080]+bestaudio" in spec_reddit_1080
    spec_reddit_audio = reddit_handler.build_format_spec("any", audio_only=True)
    assert spec_reddit_audio == "bestaudio/best"

# =====================================================================
# 5. Baseline YouTube & Instagram Preservation Assertion
# =====================================================================

def test_frozen_baseline_youtube_and_instagram_intact():
    yt_url, yt_plat = validate_and_normalize_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert yt_plat == "youtube"
    yt_handler = get_platform_handler(yt_url)
    assert yt_handler.name == "youtube"

    ig_url, ig_plat = validate_and_normalize_url("https://www.instagram.com/reel/C1234567890/")
    assert ig_plat == "instagram"
    ig_handler = get_platform_handler(ig_url)
    assert ig_handler.name == "instagram"
