import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from app.main import app
from app.services.format_service import format_normalizer
from app.services.ytdlp_service import ytdlp_service

def test_estimate_stream_size_explicit_filesize():
    fmt = {"filesize": 5000000}
    assert format_normalizer.estimate_stream_size(fmt, duration=60) == 5000000

def test_estimate_stream_size_filesize_approx():
    fmt = {"filesize_approx": 4200000}
    assert format_normalizer.estimate_stream_size(fmt, duration=60) == 4200000

def test_estimate_stream_size_from_bitrate_and_duration():
    # tbr = 1000 kbps, duration = 10s -> 1000 * 1000 / 8 * 10 = 1,250,000 bytes
    fmt = {"tbr": 1000.0}
    size = format_normalizer.estimate_stream_size(fmt, duration=10)
    assert size == 1250000

def test_estimate_stream_size_unknown_returns_none():
    fmt = {"format_id": "18"}
    assert format_normalizer.estimate_stream_size(fmt, duration=None) is None
    assert format_normalizer.estimate_stream_size(fmt, duration=60) is None

def test_distinct_file_sizes_per_resolution():
    duration = 100  # 100 seconds
    audio_format = {
        "format_id": "140",
        "ext": "m4a",
        "vcodec": "none",
        "acodec": "mp4a.40.2",
        "abr": 128.0,
        "filesize": 1600000,  # ~1.6 MB
    }
    video_1080p = {
        "format_id": "137",
        "ext": "mp4",
        "width": 1920,
        "height": 1080,
        "vcodec": "avc1.640028",
        "acodec": "none",
        "tbr": 4000.0,  # 4 Mbps -> ~50 MB
    }
    video_720p = {
        "format_id": "136",
        "ext": "mp4",
        "width": 1280,
        "height": 720,
        "vcodec": "avc1.4d401f",
        "acodec": "none",
        "tbr": 2000.0,  # 2 Mbps -> ~25 MB
    }
    video_360p = {
        "format_id": "134",
        "ext": "mp4",
        "width": 640,
        "height": 360,
        "vcodec": "avc1.4d401e",
        "acodec": "none",
        "tbr": 600.0,  # 600 kbps -> ~7.5 MB
    }

    raw_formats = [audio_format, video_1080p, video_720p, video_360p]
    normalized = format_normalizer.normalize_formats(
        raw_formats=raw_formats,
        platform="youtube",
        duration=duration
    )

    size_map = {f.format_id: f.filesize_approx for f in normalized}

    # Verify all resolutions have distinct sizes
    assert size_map["1080p"] is not None
    assert size_map["720p"] is not None
    assert size_map["360p"] is not None
    assert size_map["audio_best"] == 1600000

    assert size_map["1080p"] > size_map["720p"] > size_map["360p"] > size_map["audio_best"]
    # 1080p = 4000 * 1000 / 8 * 100 + 1600000 = 50000000 + 1600000 = 51600000
    assert size_map["1080p"] == 51600000
    # 720p = 2000 * 1000 / 8 * 100 + 1600000 = 25000000 + 1600000 = 26600000
    assert size_map["720p"] == 26600000

def test_select_best_thumbnail():
    info = {
        "thumbnails": [
            {"url": "https://i.ytimg.com/vi/abc/default.jpg", "width": 120, "height": 90},
            {"url": "https://i.ytimg.com/vi/abc/hqdefault.jpg", "width": 480, "height": 360},
            {"url": "https://i.ytimg.com/vi/abc/maxresdefault.jpg", "width": 1920, "height": 1080},
            {"url": "https://i.ytimg.com/vi/abc/mqdefault.jpg", "width": 320, "height": 180},
        ]
    }
    best = ytdlp_service._select_best_thumbnail(info)
    assert best == "https://i.ytimg.com/vi/abc/maxresdefault.jpg"

def test_select_best_thumbnail_empty():
    assert ytdlp_service._select_best_thumbnail({}) is None
    assert ytdlp_service._select_best_thumbnail({"thumbnails": []}) is None

@pytest.mark.asyncio
async def test_thumbnail_download_endpoint_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        fake_image_bytes = b"\x89PNG\r\n\x1a\nfakeimagedata"
        with patch("app.api.analyze.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_resp = AsyncMock()
            mock_resp.status_code = 200
            mock_resp.content = fake_image_bytes
            mock_resp.headers = {"content-type": "image/png"}
            mock_client.get.return_value = mock_resp
            mock_client_cls.return_value = mock_client

            resp = await ac.get(
                "/api/thumbnail/download",
                params={
                    "url": "https://i.ytimg.com/vi/abc/maxresdefault.png",
                    "title": "Test Video Title"
                }
            )

            assert resp.status_code == 200
            assert resp.content == fake_image_bytes
            assert "attachment;" in resp.headers.get("content-disposition", "")
            assert "Test Video Title-thumbnail.png" in resp.headers.get("content-disposition", "")

@pytest.mark.asyncio
async def test_thumbnail_download_endpoint_ssrf_block():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Disallowed domain
        resp = await ac.get(
            "/api/thumbnail/download",
            params={
                "url": "http://169.254.169.254/latest/meta-data/",
                "title": "AWS Metadata"
            }
        )
        assert resp.status_code == 400
        assert resp.json()["detail"]["error_code"] == "DISALLOWED_DOMAIN"
