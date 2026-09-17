import pytest
from app.security.url_validator import (
    validate_and_normalize_url,
    InvalidURLError,
    UnsupportedDomainError,
    SSRFBlockedError
)

def test_valid_youtube_urls():
    urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
    ]
    for u in urls:
        norm, platform = validate_and_normalize_url(u)
        assert platform == "youtube"
        assert norm == u

def test_valid_instagram_urls():
    urls = [
        "https://www.instagram.com/reel/C3abc123/",
        "https://instagram.com/p/C3abc123/",
    ]
    for u in urls:
        norm, platform = validate_and_normalize_url(u)
        assert platform == "instagram"
        assert norm == u

def test_unsupported_domains():
    with pytest.raises(UnsupportedDomainError):
        validate_and_normalize_url("https://malicious-site.com/video")

    with pytest.raises(UnsupportedDomainError):
        validate_and_normalize_url("https://example.com")

def test_invalid_schemes():
    with pytest.raises(InvalidURLError):
        validate_and_normalize_url("ftp://youtube.com/watch?v=123")

    with pytest.raises(InvalidURLError):
        validate_and_normalize_url("file:///etc/passwd")

    with pytest.raises(InvalidURLError):
        validate_and_normalize_url("javascript:alert(1)")

def test_private_ip_detection():
    from app.security.url_validator import is_private_ip
    assert is_private_ip("127.0.0.1") is True
    assert is_private_ip("10.0.0.1") is True
    assert is_private_ip("192.168.1.1") is True
    assert is_private_ip("169.254.169.254") is True
    assert is_private_ip("::1") is True
    assert is_private_ip("8.8.8.8") is False
