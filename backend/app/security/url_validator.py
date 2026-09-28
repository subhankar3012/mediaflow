import asyncio
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
    "x.com",
    "www.x.com",
    "twitter.com",
    "www.twitter.com",
    "mobile.twitter.com",
    "facebook.com",
    "www.facebook.com",
    "m.facebook.com",
    "web.facebook.com",
    "fb.watch",
    "pinterest.com",
    "www.pinterest.com",
    "pin.it",
    "reddit.com",
    "www.reddit.com",
    "old.reddit.com",
    "redd.it",
    "v.redd.it",
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


NAT64_PREFIX = ipaddress.ip_network("64:ff9b::/96")

def is_private_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        # NAT64 well-known prefix (RFC 6052) translates public IPv4 on cellular/modern ISPs
        if isinstance(ip, ipaddress.IPv6Address) and ip in NAT64_PREFIX:
            embedded_ipv4 = ipaddress.IPv4Address(ip.packed[-4:])
            return (
                embedded_ipv4.is_private
                or embedded_ipv4.is_loopback
                or embedded_ipv4.is_link_local
                or embedded_ipv4.is_multicast
                or embedded_ipv4.is_reserved
                or embedded_ipv4.is_unspecified
            )
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
    elif (
        hostname_lower in ("x.com", "twitter.com")
        or hostname_lower.endswith(".x.com")
        or hostname_lower.endswith(".twitter.com")
    ):
        matched_domain = True
        platform = "x"
    elif (
        hostname_lower in ("facebook.com", "fb.watch")
        or hostname_lower.endswith(".facebook.com")
        or hostname_lower.endswith(".fb.watch")
    ):
        matched_domain = True
        platform = "facebook"
    elif (
        hostname_lower in ("pinterest.com", "pin.it")
        or hostname_lower.endswith(".pinterest.com")
        or hostname_lower.endswith(".pin.it")
    ):
        matched_domain = True
        platform = "pinterest"
    elif (
        hostname_lower in ("reddit.com", "redd.it")
        or hostname_lower.endswith(".reddit.com")
        or hostname_lower.endswith(".redd.it")
    ):
        matched_domain = True
        platform = "reddit"

    if not matched_domain or not platform:
        raise UnsupportedDomainError(
            f"The domain '{hostname_lower}' is not supported. "
            "Supported platforms are YouTube, Instagram, X (Twitter), Facebook, Pinterest, and Reddit."
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

async def validate_and_normalize_url_async(raw_url: str) -> Tuple[str, str]:
    """
    Asynchronous version of validate_and_normalize_url.
    Offloads blocking socket.getaddrinfo() to the default asyncio threadpool
    executor to avoid freezing the FastAPI event loop during DNS queries.
    Preserves all SSRF protections and validation rules.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, validate_and_normalize_url, raw_url)
