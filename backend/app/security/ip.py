import ipaddress
from typing import List, Optional
from fastapi import Request
from app.config import settings

def _parse_trusted_proxies(trusted_str: str) -> List[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    networks = []
    for item in trusted_str.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            if "/" in item:
                networks.append(ipaddress.ip_network(item, strict=False))
            else:
                ip = ipaddress.ip_address(item)
                networks.append(ipaddress.ip_network(f"{ip}/{32 if ip.version == 4 else 128}"))
        except ValueError:
            continue
    return networks

def is_trusted_proxy(ip_str: str, trusted_networks: Optional[List] = None) -> bool:
    """Returns True if the given IP address falls within trusted proxy CIDRs."""
    if not ip_str:
        return False
    try:
        ip = ipaddress.ip_address(ip_str.strip())
        networks = trusted_networks if trusted_networks is not None else _parse_trusted_proxies(settings.TRUSTED_PROXIES)
        return any(ip in net for net in networks)
    except ValueError:
        return False

def get_client_ip(request: Request) -> str:
    """
    Extracts the real client IP address safely:
    1. If request.client is None, returns 'unknown'.
    2. If direct peer (request.client.host) is NOT in TRUSTED_PROXIES, return direct peer IP.
       Never trust spoofed forward headers from untrusted direct connections.
    3. If direct peer IS a trusted proxy:
       - Check 'CF-Connecting-IP' first if present.
       - Parse 'X-Forwarded-For' by walking backwards from right to left,
         skipping trusted proxy IPs, and returning the first untrusted client IP.
    """
    if not request.client or not request.client.host:
        return "unknown"

    peer_ip = request.client.host.strip()
    trusted_networks = _parse_trusted_proxies(settings.TRUSTED_PROXIES)

    if not is_trusted_proxy(peer_ip, trusted_networks):
        return peer_ip

    # Peer is a trusted proxy -> inspect headers
    cf_connecting = request.headers.get("CF-Connecting-IP")
    if cf_connecting:
        cf_ip = cf_connecting.strip()
        try:
            ipaddress.ip_address(cf_ip)
            return cf_ip
        except ValueError:
            pass

    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        parts = [p.strip() for p in x_forwarded_for.split(",") if p.strip()]
        # Walk from right to left
        for ip in reversed(parts):
            if not is_trusted_proxy(ip, trusted_networks):
                try:
                    ipaddress.ip_address(ip)
                    return ip
                except ValueError:
                    continue

    return peer_ip
