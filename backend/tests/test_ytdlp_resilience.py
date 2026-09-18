import pytest
import http.cookiejar
from app.services.ytdlp_service import ytdlp_service, YtDlpService

def test_cookie_sanitizer_space_separated_repair():
    """Verifies that space-separated cookie lines are correctly normalized to tab-separated Netscape format."""
    space_cookie_content = """# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
.youtube.com TRUE / FALSE 1823425098 SID g.a000test_cookie_value_here
.youtube.com TRUE / TRUE 1823425098 HSID test_hsid_value
"""
    cookie_path = YtDlpService._sanitize_and_validate_cookies(space_cookie_content)
    assert cookie_path is not None, "Sanitizer should produce a valid cookie file"

    jar = http.cookiejar.MozillaCookieJar(cookie_path)
    jar.load(ignore_discard=True, ignore_expires=True)
    assert len(jar) == 2, f"Expected 2 cookies, got {len(jar)}"
    names = [c.name for c in jar]
    assert "SID" in names
    assert "HSID" in names

def test_cookie_sanitizer_escaped_newlines():
    """Verifies that literal escaped \\n and \\t from environment variables are properly resolved."""
    escaped_content = r"# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tFALSE\t1823425098\tSSID\ttest_ssid_val\n"
    cookie_path = YtDlpService._sanitize_and_validate_cookies(escaped_content)
    assert cookie_path is not None

    jar = http.cookiejar.MozillaCookieJar(cookie_path)
    jar.load(ignore_discard=True, ignore_expires=True)
    assert len(jar) == 1
    assert list(jar)[0].name == "SSID"

def test_cookie_sanitizer_invalid_returns_none():
    """Verifies that garbage or empty input safely returns None without throwing exceptions."""
    assert YtDlpService._sanitize_and_validate_cookies("") is None
    assert YtDlpService._sanitize_and_validate_cookies("   ") is None
    assert YtDlpService._sanitize_and_validate_cookies("random non-cookie text") is None

def test_get_cookies_status():
    """Verifies that get_cookies_status returns a structured dictionary."""
    status = ytdlp_service.get_cookies_status()
    assert isinstance(status, dict)
    assert "loaded" in status
    assert "count" in status
    assert "valid" in status
