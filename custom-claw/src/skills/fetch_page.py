import html as html_lib
import ipaddress
import re
import socket
from urllib.parse import urljoin, urlparse

import certifi
import urllib3

USER_AGENT = "Mozilla/5.0 (compatible; compliance-monitor/1.0)"
MAX_BYTES = 512_000
MAX_REDIRECTS = 3


def _resolve_and_validate(host: str) -> str:
    """Resolve host to an IP, check all address families, return a safe IPv4 address.

    Raises ValueError if any resolved address is private/loopback/reserved.
    """
    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(f"Cannot resolve {host!r}: {exc}") from exc
    if not infos:
        raise ValueError(f"No addresses for {host!r}")
    for _, _, _, _, sockaddr in infos:
        ip = ipaddress.ip_address(sockaddr[0])
        if not ip.is_global:
            raise ValueError(f"Disallowed target address: {ip}")
    # Return first resolved IP to pin the connection
    return infos[0][4][0]


def _make_pool(scheme: str, host: str, ip: str, port: int) -> urllib3.HTTPConnectionPool:
    """Create a urllib3 pool pinned to the validated IP, with SNI for HTTPS."""
    if scheme == "https":
        return urllib3.HTTPSConnectionPool(
            ip, port=port,
            server_hostname=host,   # SNI
            assert_hostname=host,   # cert verification against hostname, not IP
            cert_reqs="CERT_REQUIRED",
            ca_certs=certifi.where(),
        )
    return urllib3.HTTPConnectionPool(ip, port=port)


def _fetch_one(url: str) -> tuple[bytes, str, str | None]:
    """Fetch a single URL (no redirect following). Returns (body, encoding, location)."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Disallowed scheme: {parsed.scheme!r}")
    host = parsed.hostname
    if not host:
        raise ValueError("URL has no hostname")

    ip = _resolve_and_validate(host)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    pool = _make_pool(parsed.scheme, host, ip, port)

    path = parsed.path or "/"
    if parsed.params:
        path += ";" + parsed.params
    if parsed.query:
        path += "?" + parsed.query

    default_port = 443 if parsed.scheme == "https" else 80
    host_header = host if port == default_port else f"{host}:{port}"

    resp = pool.urlopen(
        "GET", path,
        headers={"Host": host_header, "User-Agent": USER_AGENT},
        redirect=False,
        preload_content=False,
        timeout=urllib3.Timeout(connect=10, read=20),
    )

    location = resp.get_redirect_location() or None
    if resp.status in (301, 302, 303, 307, 308):
        if not location:
            resp.close()
            raise RuntimeError(f"Redirect {resp.status} with no Location header from {url}")
        resp.close()
        return b"", "", location

    if not (200 <= resp.status < 300):
        resp.close()
        raise RuntimeError(f"HTTP {resp.status} from {url}")

    buf = b""
    truncated = False
    try:
        for chunk in resp.stream(8192):
            buf += chunk
            if len(buf) >= MAX_BYTES:
                truncated = True
                break
    finally:
        resp.close() if truncated else resp.release_conn()

    content_type = resp.headers.get("content-type", "")
    charset = "utf-8"
    if "charset=" in content_type:
        raw_charset = content_type.split("charset=")[-1].split(";")[0].strip().strip('"\'')
        try:
            b"".decode(raw_charset)  # probe with decode semantics
            charset = raw_charset
        except (LookupError, UnicodeError):
            charset = "utf-8"
    return buf, charset, None


def fetch_compliance_page(url: str) -> str:
    """Fetch a compliance page and return cleaned plain text for the LLM.

    Pins the TCP connection to the DNS-resolved IP to prevent rebinding attacks.
    Raises ValueError for disallowed URLs, RuntimeError on fetch failure.
    """
    current_url = url
    for _ in range(MAX_REDIRECTS + 1):
        try:
            body, charset, location = _fetch_one(current_url)
        except (urllib3.exceptions.HTTPError, OSError) as exc:
            raise RuntimeError(f"Failed to fetch {current_url}: {exc}") from exc

        if location:
            current_url = urljoin(current_url, location)
            continue

        raw = body.decode(charset, errors="replace")
        raw = re.sub(
            r"<(script|style)[^>]*>.*?</(script|style)>",
            " ", raw, flags=re.DOTALL | re.IGNORECASE,
        )
        text = re.sub(r"<[^>]+>", " ", raw)
        text = html_lib.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:6000]

    raise RuntimeError(f"Exceeded {MAX_REDIRECTS} redirects for {url}")
