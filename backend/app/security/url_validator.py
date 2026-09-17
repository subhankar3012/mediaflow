import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple, Optional, Set

# Allowed platforms / domain names
ALLOWED_DOMAINS: Set[str] = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
    "instagram.com",
    "www.instagram.com",
}

class SecurityError(Exception):
    def __init__(self, message: str, code: str = "INVALID_URL"):
        super().__init__(message)
        self.code = code
        self.message = message

class InvalidURLError(SecurityError):
    def __init__(self, message: str = "URL must be a non-empty, valid HTTP/HTTPS URL."):
        super().__init__(message, code="INVALID_URL")

class UnsupportedDomainError(SecurityError):
    def __init__(self, message: str = "The requested domain is not supported."):
        super().__init__(message, code="UNSUPPORTED_PLATFORM")

class SSRFBlockedError(SecurityError):
    def __init__(self, message: str = "Access to private or reserved IP address is forbidden."):
        super().__init__(message, code="INVALID_URL")


def is_private_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        return False

def validate_and_normalize_url(raw_url: str) -> Tuple[str, str]:
    """
    Validates user-submitted URL:
    1. Enforces HTTP/HTTPS.
    2. Verifies hostname is in allowed domain list.
    3. Resolves hostname to prevent SSRF against private/link-local IP addresses.
    4. Returns (normalized_url, platform_name).
    """
    if not raw_url or not isinstance(raw_url, str):
        raise InvalidURLError("URL must be a non-empty string.")

    cleaned_url = raw_url.strip()
    parsed = urlparse(cleaned_url)

    if parsed.scheme not in ("http", "https"):
        raise InvalidURLError("Invalid URL scheme. Only HTTP and HTTPS are permitted.")

    hostname = parsed.hostname
    if not hostname:
        raise InvalidURLError("URL must have a valid hostname.")

    hostname_lower = hostname.lower()

    # Pre-check: If hostname is an explicit private/loopback IP or localhost, block SSRF immediately
    if hostname_lower in ("localhost", "0.0.0.0") or is_private_ip(hostname_lower):
        raise SSRFBlockedError(
            f"Access to private or reserved IP address {hostname_lower} is forbidden."
        )

    # Domain allowlist check
    matched_domain = False
    platform = None

    if (
        hostname_lower == "youtu.be"
        or hostname_lower == "youtube.com"
        or hostname_lower.endswith(".youtube.com")
    ):
        matched_domain = True
        platform = "youtube"
    elif (
        hostname_lower == "instagram.com"
        or hostname_lower.endswith(".instagram.com")
    ):
        matched_domain = True
        platform = "instagram"

    if not matched_domain or not platform:
        raise UnsupportedDomainError(
            f"The domain '{hostname_lower}' is not supported. "
            "Supported platforms are currently YouTube and Instagram."
        )

    # SSRF Protection: Resolve hostname to IP and ensure it is not private/loopback/cloud-metadata
    try:
        addr_info = socket.getaddrinfo(hostname_lower, None)
        for entry in addr_info:
            ip_str = entry[4][0]
            if is_private_ip(ip_str):
                raise SSRFBlockedError(
                    f"Access to private or reserved IP address {ip_str} is forbidden."
                )
    except socket.gaierror as e:
        raise InvalidURLError(f"Hostname resolution failed: {str(e)}")

    return cleaned_url, platform
