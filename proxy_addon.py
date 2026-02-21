"""
APO v2 — mitmproxy addon
Runs as a proxy alongside Tier 2 browser sessions.
Captures full request headers (Sec-GPC), response status codes,
Set-Cookie headers, POST bodies, and tracker domain flags.
Saves to output/raw_traffic_proxy.jsonl (one JSON per line).
"""
import json
import time
import os
from mitmproxy import http

# Tracker domain list 
TRACKERS = {
    "google-analytics.com", "googletagmanager.com", "doubleclick.net",
    "connect.facebook.net", "facebook.com", "linkedin.com", "px.ads.linkedin.com",
    "ads.linkedin.com", "snap.licdn.com", "amazon-adsystem.com",
    "scorecardresearch.com", "quantserve.com", "bing.com", "bat.bing.com",
    "hotjar.com", "clarity.ms", "segment.io", "segment.com",
    "mixpanel.com", "amplitude.com", "heap.io",
}

OUTPUT_FILE = os.path.join(
    os.path.dirname(__file__), "output", "raw_traffic_proxy.jsonl"
)

# Ensure output dir exists
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

def _is_tracker(domain: str) -> bool:
    domain = domain.lstrip(".")
    return any(domain == t or domain.endswith("." + t) for t in TRACKERS)


class APOProxyAddon:
    def __init__(self):
        self._log_fh = open(OUTPUT_FILE, "a")

    def _write(self, record: dict):
        self._log_fh.write(json.dumps(record) + "\n")
        self._log_fh.flush()

    def request(self, flow: http.HTTPFlow):
        """Called for every outgoing request."""
        req = flow.request
        domain = req.pretty_host

        # Check if GPC header is present
        gpc_header = req.headers.get("sec-gpc", req.headers.get("Sec-GPC", None))

        record = {
            "phase": "request",
            "timestamp_ms": int(time.time() * 1000),
            "method": req.method,
            "url": req.pretty_url,
            "domain": domain,
            "is_tracker": _is_tracker(domain),
            "gpc_sent": gpc_header,
            "headers": dict(req.headers),
            "post_body": req.content.decode("utf-8", errors="replace") if req.method in ("POST", "PUT") and req.content else None,
        }
        self._write(record)

    def response(self, flow: http.HTTPFlow):
        """Called for every response."""
        req = flow.request
        resp = flow.response
        domain = req.pretty_host

        set_cookies = resp.headers.get_all("set-cookie")

        record = {
            "phase": "response",
            "timestamp_ms": int(time.time() * 1000),
            "url": req.pretty_url,
            "domain": domain,
            "is_tracker": _is_tracker(domain),
            "status_code": resp.status_code,
            "set_cookie": set_cookies,
            "content_type": resp.headers.get("content-type", ""),
        }
        self._write(record)

    def done(self):
        self._log_fh.close()


addons = [APOProxyAddon()]
